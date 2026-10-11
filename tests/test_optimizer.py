"""Adversarial integrity and independent exhaustive-oracle tests."""
from datetime import datetime, timezone
from itertools import product
from random import Random

import pytest
from pydantic import ValidationError

from backend.demo import demo_plan
from backend.models import PlanRequest, Weather, WeatherHour, clock_minutes
from backend.optimizer import optimize
from backend.weather import WeatherUnavailable


def plan_with(tasks, *, start="08:00", end="16:00", breaks=None, threshold=32):
    return PlanRequest.model_validate({
        "date": "2026-10-12", "location": {"name": "Test site", "latitude": 28.75, "longitude": 77.12},
        "shiftStart": start, "shiftEnd": end, "breaks": breaks or [], "thresholdC": threshold, "tasks": tasks,
    })


def task(id="a", duration=60, start="12:00", earliest="08:00", latest="16:00", locked=False):
    return {"id": id, "title": f"Task {id}", "durationMinutes": duration, "baselineStart": start,
            "earliestStart": earliest, "latestEnd": latest, "locked": locked}


def forecast(plan, values=None):
    temperatures = values or {hour: 24 if hour < 10 else 35 for hour in range(24)}
    return Weather(fetchedAt=datetime.now(timezone.utc).isoformat(), mode="live", date=plan.date,
        latitude=plan.location.latitude, longitude=plan.location.longitude,
        gridLatitude=28.787, gridLongitude=77.143,
        hours=[WeatherHour(time=f"{hour:02d}:00", temperatureC=value - 2,
                          apparentTemperatureC=value, precipitationProbability=0)
               for hour, value in temperatures.items()],
        attribution="Explicit synthetic test fixture", sourceUrl="https://example.test/fixture")


def test_cooler_plan_keeps_every_duration_lock_break_and_window():
    plan = plan_with([task("a", start="11:30"), task("b", 45, "13:00"),
                      task("locked", 30, "10:00", "10:00", "10:30", True)],
                     breaks=[{"start": "12:30", "end": "13:00"}])
    result = optimize(plan, forecast(plan))
    assert result.status == "improved"
    assert result.metrics.deltaC > 0
    assert result.metrics.workMinutes == 135
    assert {item.taskId for item in result.schedule} == {"a", "b", "locked"}
    assert all(check.passed for check in result.constraintChecks)
    for item in result.schedule:
        original = next(task for task in plan.tasks if task.id == item.taskId)
        assert clock_minutes(item.end, allow_end=True) - clock_minutes(item.start) == original.durationMinutes
        if item.locked:
            assert item.start == original.baselineStart
        assert not (item.start < "13:00" and item.end > "12:30")


def test_all_locked_hostile_request_cannot_invent_improvement():
    plan = plan_with([task(str(hour), 60, f"{hour}:00", "12:00", "16:00", True)
                      for hour in range(12, 16)], start="12:00", end="16:00")
    result = optimize(plan, forecast(plan))
    assert result.status == "unchanged"
    assert result.metrics.deltaC == 0
    assert result.schedule == result.baselineSchedule


def test_constant_forecast_prefers_zero_movements():
    plan = plan_with([task("a", 45, "11:00"), task("b", 30, "13:15")])
    result = optimize(plan, forecast(plan, {hour: 30 for hour in range(24)}))
    assert result.status == "unchanged"
    assert result.schedule == result.baselineSchedule


def test_invalid_overlapping_baseline_never_earns_savings():
    plan = plan_with([task("a"), task("b")])
    result = optimize(plan, forecast(plan))
    assert result.status == "planned"
    assert not result.baselineValid
    assert result.baselineSchedule == []
    assert result.metrics.deltaC is None
    assert result.metrics.baselineMeanApparentTemperatureC is None
    assert result.metrics.baselineHotMinutes is None
    assert any("overlaps" in value for value in result.violations)
    assert len(result.schedule) == 2


def test_overlapping_locks_are_infeasible_not_silently_unlocked():
    plan = plan_with([task("a", locked=True), task("b", locked=True)])
    result = optimize(plan, forecast(plan))
    assert result.status == "infeasible"
    assert not result.schedule
    assert result.metrics.proposedMeanApparentTemperatureC is None
    assert any("locked" in message for message in result.violations)


def test_locked_break_conflict_is_explained():
    plan = plan_with([task("a", start="12:00", locked=True)],
                     breaks=[{"start": "12:30", "end": "13:00"}])
    result = optimize(plan, forecast(plan))
    assert result.status == "infeasible"
    assert any("break" in value for value in result.violations)


def test_insufficient_capacity_preserves_requested_work():
    plan = plan_with([task("a", 60, "08:00"), task("b", 60, "09:00")],
                     start="08:00", end="10:00", breaks=[{"start": "09:00", "end": "09:15"}])
    result = optimize(plan, forecast(plan))
    assert result.status == "infeasible"
    assert result.metrics.workMinutes == 120
    assert any("105" in value for value in result.violations)


def test_nonpreemptive_task_cannot_be_split_around_break():
    plan = plan_with([task("a", 90, "08:00", "08:00", "10:30")], start="08:00", end="10:30",
                     breaks=[{"start": "09:00", "end": "09:30"}])
    result = optimize(plan, forecast(plan))
    assert result.status == "infeasible"
    assert any("uninterrupted" in value for value in result.violations)


def test_oversubscribed_window_has_specific_explanation():
    plan = plan_with([task("a", 45, "08:00", "08:00", "09:00"),
                      task("b", 45, "08:00", "08:00", "09:00")])
    result = optimize(plan, forecast(plan))
    assert result.status == "infeasible"
    assert any("require 90 minutes" in value and "60" in value for value in result.violations)


def test_metrics_weight_work_duration_and_use_threshold_inclusively():
    plan = plan_with([task("a", 15, "08:00", locked=True), task("b", 45, "09:00", locked=True)], threshold=40)
    result = optimize(plan, forecast(plan, {hour: 40 if hour == 8 else 20 for hour in range(24)}))
    assert result.metrics.proposedMeanApparentTemperatureC == 25
    assert result.metrics.proposedHotMinutes == 15
    assert result.metrics.workMinutes == 60


def test_quarter_hour_task_spanning_two_forecast_hours():
    plan = plan_with([task("a", 30, "08:45", locked=True)], threshold=30)
    result = optimize(plan, forecast(plan, {hour: 30 if hour == 8 else 20 for hour in range(24)}))
    assert result.metrics.proposedMeanApparentTemperatureC == 25
    assert result.metrics.proposedHotMinutes == 15


def test_missing_required_weather_rejects_instead_of_using_zero():
    plan = plan_with([task()])
    weather = forecast(plan)
    weather.hours = [hour for hour in weather.hours if hour.time != "09:00"]
    with pytest.raises(WeatherUnavailable, match="09:00"):
        optimize(plan, weather)


@pytest.mark.parametrize("update", [{"date": "2026-10-13"}, {"latitude": 19.07}])
def test_weather_from_another_date_or_location_is_rejected(update):
    plan = plan_with([task()])
    with pytest.raises(WeatherUnavailable):
        optimize(plan, forecast(plan).model_copy(update=update))


@pytest.mark.parametrize("patch", [
    {"durationMinutes": 20}, {"baselineStart": "08:10"}, {"durationMinutes": True},
    {"earliestStart": "25:00"}, {"durationMinutes": 0},
])
def test_bad_task_inputs_are_rejected_before_solving(patch):
    values = task()
    values.update(patch)
    with pytest.raises(ValidationError):
        plan_with([values])


def test_bounds_and_unique_ids():
    with pytest.raises(ValidationError):
        plan_with([task()], start="01:00", end="23:00")
    with pytest.raises(ValidationError):
        plan_with([task("a"), task("a")])
    with pytest.raises(ValidationError):
        plan_with([task(str(index)) for index in range(9)])
    with pytest.raises(ValidationError):
        plan_with([task()], threshold=float("nan"))


def test_demo_has_a_valid_baseline():
    plan = demo_plan()
    result = optimize(plan, forecast(plan))
    assert result.baselineValid
    assert len(result.schedule) == len(plan.tasks)


def test_exact_optimizer_matches_independent_exhaustive_oracle():
    random = Random(12)
    for _ in range(15):
        durations = [random.choice([15, 30, 45]) for _ in range(3)]
        values = {hour: random.randint(20, 40) for hour in range(24)}
        tasks = [task(str(index), duration, "08:00", "08:00", "10:00") for index, duration in enumerate(durations)]
        plan = plan_with(tasks, start="08:00", end="10:00")
        result = optimize(plan, forecast(plan, values))
        possibilities = [range(480, 600 - duration + 1, 15) for duration in durations]
        best = None
        for starts in product(*possibilities):
            intervals = sorted(zip(starts, durations))
            if any(left + duration > right for (left, duration), (right, _) in zip(intervals, intervals[1:])):
                continue
            cost = sum(values[minute // 60] * 15 for start, duration in zip(starts, durations)
                       for minute in range(start, start + duration, 15))
            best = cost if best is None else min(best, cost)
        if best is None:
            assert result.status == "infeasible"
        else:
            actual = sum(values[minute // 60] * 15 for item in result.schedule
                         for minute in range(clock_minutes(item.start), clock_minutes(item.end), 15))
            assert actual == best
