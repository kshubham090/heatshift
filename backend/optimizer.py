"""Exact one-crew optimizer on 15-minute slots, with auditable constraints.

Dynamic programming over (time, completed-task bitmask). The lexicographic
objective is weighted apparent-temperature exposure, number of moved jobs,
then total minutes moved. No jobs are dropped and no generated text does math.
"""
from __future__ import annotations

from decimal import Decimal
from itertools import combinations

from .models import (ConstraintCheck, PlanMetrics, PlanRequest, PlanResult,
                     ScheduleItem, Weather, clock_minutes, clock_string)
from .weather import WeatherUnavailable


def _overlap(start: int, end: int, other_start: int, other_end: int) -> bool:
    return start < other_end and other_start < end


def _schedule_violations(plan: PlanRequest, starts: list[int]) -> list[str]:
    violations: list[str] = []
    first, last = clock_minutes(plan.shiftStart), clock_minutes(plan.shiftEnd, allow_end=True)
    breaks = [(clock_minutes(item.start), clock_minutes(item.end, allow_end=True)) for item in plan.breaks]
    for index, task in enumerate(plan.tasks):
        start, end = starts[index], starts[index] + task.durationMinutes
        if start < first or end > last:
            violations.append(f"{task.title} is outside the paid shift {plan.shiftStart}–{plan.shiftEnd}.")
        if start < clock_minutes(task.earliestStart) or end > clock_minutes(task.latestEnd, allow_end=True):
            violations.append(f"{task.title} is outside its allowed window {task.earliestStart}–{task.latestEnd}.")
        if task.locked and start != clock_minutes(task.baselineStart):
            violations.append(f"{task.title} must stay locked at {task.baselineStart}.")
        for break_start, break_end in breaks:
            if _overlap(start, end, break_start, break_end):
                violations.append(f"{task.title} overlaps the protected break {clock_string(break_start)}–{clock_string(break_end)}.")
    for first_index, second_index in combinations(range(len(plan.tasks)), 2):
        first_task, second_task = plan.tasks[first_index], plan.tasks[second_index]
        if _overlap(starts[first_index], starts[first_index] + first_task.durationMinutes,
                    starts[second_index], starts[second_index] + second_task.durationMinutes):
            violations.append(f"{first_task.title} overlaps {second_task.title}; one crew cannot do both at once.")
    return violations


def optimize(plan: PlanRequest, weather: Weather) -> PlanResult:
    """Return an exact feasible optimum, or an honest infeasibility explanation.

    WeatherUnavailable is raised for date/location mismatch or missing required
    weather. HTTP callers should map that exception to 503.
    """
    if weather.date != plan.date or weather.timezone != "Asia/Kolkata":
        raise WeatherUnavailable("The available weather does not match the plan's local date.")
    if abs(weather.latitude - plan.location.latitude) > 1e-6 or abs(weather.longitude - plan.location.longitude) > 1e-6:
        raise WeatherUnavailable("The available weather does not match the selected location.")
    first, last = clock_minutes(plan.shiftStart), clock_minutes(plan.shiftEnd, allow_end=True)
    count = (last - first) // 15
    hourly = {clock_minutes(item.time): item.apparentTemperatureC for item in weather.hours}
    temperatures: list[Decimal] = []
    for minute in range(first, last, 15):
        hour = minute // 60 * 60
        if hour not in hourly:
            raise WeatherUnavailable(f"Forecast data are missing for {clock_string(hour)}. No schedule was calculated.")
        temperatures.append(Decimal(str(hourly[hour])))
    prefix = [Decimal(0)]
    hot_prefix = [0]
    threshold = Decimal(str(plan.thresholdC))
    for temperature in temperatures:
        prefix.append(prefix[-1] + temperature * 15)
        hot_prefix.append(hot_prefix[-1] + (15 if temperature >= threshold else 0))

    breaks = [(clock_minutes(item.start), clock_minutes(item.end, allow_end=True)) for item in plan.breaks]
    blocked = [any(_overlap(first + slot * 15, first + (slot + 1) * 15, a, b) for a, b in breaks)
               for slot in range(count)]
    blocked_prefix = [0]
    for value in blocked:
        blocked_prefix.append(blocked_prefix[-1] + int(value))
    open_minutes = (count - sum(blocked)) * 15
    work_minutes = sum(task.durationMinutes for task in plan.tasks)
    original_starts = [clock_minutes(task.baselineStart) for task in plan.tasks]
    baseline_violations = _schedule_violations(plan, original_starts)
    baseline_valid = not baseline_violations
    durations = [task.durationMinutes // 15 for task in plan.tasks]

    def exposure(index: int, slot: int) -> Decimal:
        return prefix[slot + durations[index]] - prefix[slot]

    def hot_minutes(index: int, slot: int) -> int:
        return hot_prefix[slot + durations[index]] - hot_prefix[slot]

    def schedule_items(starts: list[int]) -> list[ScheduleItem]:
        result = []
        for index, task in enumerate(plan.tasks):
            slot = (starts[index] - first) // 15
            result.append(ScheduleItem(
                taskId=task.id, title=task.title, start=clock_string(starts[index]),
                end=clock_string(starts[index] + task.durationMinutes), locked=task.locked,
                meanApparentTemperatureC=round(float(exposure(index, slot) / task.durationMinutes), 3),
            ))
        return sorted(result, key=lambda item: (item.start, item.taskId))

    baseline_cost = (sum((exposure(index, (start - first) // 15) for index, start in enumerate(original_starts)), Decimal(0))
                     if baseline_valid else None)
    baseline_hot = (sum(hot_minutes(index, (start - first) // 15) for index, start in enumerate(original_starts))
                    if baseline_valid else None)
    baseline_schedule = schedule_items(original_starts) if baseline_valid else []
    candidates: list[dict[int, Decimal]] = []
    impossible: list[str] = []
    if work_minutes > open_minutes:
        impossible.append(f"The jobs require {work_minutes} minutes, but this shift has only {open_minutes} working minutes after protected breaks.")

    for index, task in enumerate(plan.tasks):
        earliest = max(first, clock_minutes(task.earliestStart))
        latest = min(last, clock_minutes(task.latestEnd, allow_end=True)) - task.durationMinutes
        candidate_minutes = ([original_starts[index]] if task.locked else range(earliest, latest + 1, 15))
        options: dict[int, Decimal] = {}
        for start in candidate_minutes:
            end = start + task.durationMinutes
            if start < earliest or start > latest:
                continue
            slot = (start - first) // 15
            stop = slot + durations[index]
            if blocked_prefix[stop] != blocked_prefix[slot]:
                continue
            # Other immovable jobs are already known obstacles. This pruning
            # also produces useful explanations for otherwise opaque conflicts.
            if any(other.locked and other_index != index and
                   _overlap(start, end, original_starts[other_index],
                            original_starts[other_index] + other.durationMinutes)
                   for other_index, other in enumerate(plan.tasks)):
                continue
            options[slot] = exposure(index, slot)
        candidates.append(options)
        if not options:
            if task.locked:
                impossible.append(f"{task.title} is locked at {task.baselineStart}; its full {task.durationMinutes} minutes conflict with its window, the shift, a protected break, or another locked job.")
            else:
                impossible.append(f"{task.title} needs {task.durationMinutes} uninterrupted minutes within {task.earliestStart}–{task.latestEnd}; none fit the shift, protected breaks and locked jobs.")

    # A state stores (exposure, moved-job count, displacement minutes, task starts).
    # Starts sorted by task index supply a stable final tie-break for equal plans.
    State = tuple[Decimal, int, int, tuple[tuple[int, int], ...]]
    levels: list[dict[int, State]] = [dict() for _ in range(count + 1)]
    levels[0][0] = (Decimal(0), 0, 0, ())

    def retain(time: int, mask: int, candidate: State) -> None:
        current = levels[time].get(mask)
        if current is None or candidate < current:
            levels[time][mask] = candidate

    if not impossible:
        for time in range(count + 1):
            for mask, state in tuple(levels[time].items()):
                if time < count:
                    retain(time + 1, mask, state)
                for index, task in enumerate(plan.tasks):
                    if mask & (1 << index) or time not in candidates[index]:
                        continue
                    start = first + time * 15
                    updated: State = (
                        state[0] + candidates[index][time],
                        state[1] + int(start != original_starts[index]),
                        state[2] + abs(start - original_starts[index]),
                        tuple(sorted((*state[3], (index, start)))),
                    )
                    retain(time + durations[index], mask | (1 << index), updated)
    best = levels[count].get((1 << len(plan.tasks)) - 1)

    if best is None:
        if not impossible:
            # Find a concrete over-subscribed interval whenever one exists.
            bounds = sorted({0, count, *(start for options in candidates for start in options),
                             *(start + durations[index] for index, options in enumerate(candidates) for start in options)})
            for left, right in combinations(bounds, 2):
                confined = [index for index, options in enumerate(candidates)
                            if min(options) >= left and max(options) + durations[index] <= right]
                required = sum(plan.tasks[index].durationMinutes for index in confined)
                available = (right - left - (blocked_prefix[right] - blocked_prefix[left])) * 15
                if required > available:
                    titles = ", ".join(plan.tasks[index].title for index in confined)
                    impossible.append(f"Between {clock_string(first + left * 15)} and {clock_string(first + right * 15)}, {titles} require {required} minutes, but only {available} are available to one crew.")
                    break
        if not impossible:
            titles = ", ".join(task.title for task in plan.tasks)
            impossible.append(f"No non-overlapping placement exists for {titles} under their current windows, locked starts and breaks. The exact search found no schedule; widen a window, extend the paid shift or revise a task with approval.")
        violations = list(dict.fromkeys(impossible + [f"Original plan: {item}" for item in baseline_violations]))
        return PlanResult(
            status="infeasible", schedule=[], baselineSchedule=baseline_schedule, baselineValid=baseline_valid,
            metrics=PlanMetrics(workMinutes=work_minutes,
                baselineMeanApparentTemperatureC=round(float(baseline_cost / work_minutes), 3) if baseline_cost is not None else None,
                proposedMeanApparentTemperatureC=None, deltaC=None, baselineHotMinutes=baseline_hot,
                proposedHotMinutes=None, thresholdC=plan.thresholdC),
            explanation="No valid schedule exists with all the current constraints. No jobs were removed or shortened. " + impossible[0],
            violations=violations,
            constraintChecks=[ConstraintCheck(label="Forecast matches the selected date and location", passed=True),
                              ConstraintCheck(label="All jobs fit with locks, windows and breaks preserved", passed=False)],
            weather=weather, request=plan,
        )

    starts = [0] * len(plan.tasks)
    for index, start in best[3]:
        starts[index] = start
    final_violations = _schedule_violations(plan, starts)
    if final_violations:
        raise AssertionError("Optimizer produced an invalid schedule: " + "; ".join(final_violations))
    proposed_cost = best[0]
    proposed_mean = round(float(proposed_cost / work_minutes), 3)
    baseline_mean = round(float(baseline_cost / work_minutes), 3) if baseline_cost is not None else None
    delta = round(float((baseline_cost - proposed_cost) / work_minutes), 3) if baseline_cost is not None else None
    if baseline_cost is None:
        status = "planned"
        explanation = "A valid plan preserves every job, duration, allowed window, lock and break. The original plan violates constraints, so no temperature improvement or savings is claimed against it."
    elif proposed_cost < baseline_cost:
        status = "improved"
        explanation = (f"The same {work_minutes} minutes of work fit a plan averaging {delta:g}°C lower forecast apparent temperature. "
                       "All task windows, locks and breaks are preserved. This is a forecast comparison, not a measured health improvement.")
    else:
        status = "unchanged"
        explanation = "The original plan is already optimal under the current constraints and forecast. No jobs were moved just to make the plan look different."
    return PlanResult(
        status=status, schedule=schedule_items(starts), baselineSchedule=baseline_schedule,
        baselineValid=baseline_valid,
        metrics=PlanMetrics(workMinutes=work_minutes, baselineMeanApparentTemperatureC=baseline_mean,
            proposedMeanApparentTemperatureC=proposed_mean, deltaC=delta,
            baselineHotMinutes=baseline_hot,
            proposedHotMinutes=sum(hot_minutes(index, (start - first) // 15) for index, start in enumerate(starts)),
            thresholdC=plan.thresholdC),
        explanation=explanation,
        violations=[f"Original plan: {item}" for item in baseline_violations],
        constraintChecks=[
            ConstraintCheck(label=f"All {len(plan.tasks)} jobs and {work_minutes} work minutes preserved", passed=True),
            ConstraintCheck(label="One crew; no overlapping jobs", passed=True),
            ConstraintCheck(label="Every job stays inside the paid shift and its allowed window", passed=True),
            ConstraintCheck(label="Every locked start and protected break preserved", passed=True),
            ConstraintCheck(label="Forecast matches the selected date and location", passed=True),
        ],
        weather=weather, request=plan,
    )
