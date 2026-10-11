"""Validated public API types; field names deliberately match the camelCase contract."""
from __future__ import annotations

from datetime import date as CalendarDate
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def clock_minutes(value: str, *, allow_end: bool = False) -> int:
    if allow_end and value == "24:00":
        return 1440
    if not isinstance(value, str) or not re.fullmatch(r"(?:[01]\d|2[0-3]):(?:00|15|30|45)", value):
        raise ValueError("Use local HH:MM time in 15-minute increments.")
    hour, minute = map(int, value.split(":"))
    return hour * 60 + minute


def clock_string(minutes: int) -> str:
    if not 0 <= minutes <= 1440:
        raise ValueError("Time is outside the selected local day.")
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def valid_date(value: str) -> str:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("Use a calendar date in YYYY-MM-DD format.")
    CalendarDate.fromisoformat(value)
    return value


class APIModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, str_strip_whitespace=True)


class Location(APIModel):
    name: str = Field(min_length=1, max_length=120)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class TimeBlock(APIModel):
    start: str
    end: str

    @model_validator(mode="after")
    def valid_interval(self):
        if clock_minutes(self.start) >= clock_minutes(self.end, allow_end=True):
            raise ValueError("A break must end after it starts on the same day.")
        return self


class Task(APIModel):
    id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    title: str = Field(min_length=1, max_length=160)
    durationMinutes: int = Field(strict=True, ge=15, le=720)
    earliestStart: str
    latestEnd: str
    baselineStart: str
    locked: bool = False

    @field_validator("durationMinutes")
    @classmethod
    def quarter_hour_duration(cls, value: int) -> int:
        if value % 15:
            raise ValueError("Task duration must be a multiple of 15 minutes.")
        return value

    @model_validator(mode="after")
    def valid_times(self):
        first = clock_minutes(self.earliestStart)
        last = clock_minutes(self.latestEnd, allow_end=True)
        clock_minutes(self.baselineStart)
        if first >= last:
            raise ValueError("Task latestEnd must be after earliestStart on the same day.")
        return self


class PlanRequest(APIModel):
    date: str
    location: Location
    shiftStart: str
    shiftEnd: str
    breaks: list[TimeBlock] = Field(default_factory=list, max_length=16)
    thresholdC: float = Field(default=32, ge=-50, le=80)
    tasks: list[Task] = Field(min_length=1, max_length=8)

    _calendar_date = field_validator("date")(valid_date)

    @model_validator(mode="after")
    def valid_plan(self):
        first = clock_minutes(self.shiftStart)
        last = clock_minutes(self.shiftEnd, allow_end=True)
        if not 0 < last - first <= 720:
            raise ValueError("The shift must be on one day and last at most 12 hours.")
        if len({task.id for task in self.tasks}) != len(self.tasks):
            raise ValueError("Every task must have a unique id.")
        ordered = sorted(self.breaks, key=lambda item: item.start)
        previous_end = first
        for block in ordered:
            start = clock_minutes(block.start)
            end = clock_minutes(block.end, allow_end=True)
            if start < first or end > last:
                raise ValueError("Every break must be inside the paid shift.")
            if start < previous_end:
                raise ValueError("Breaks must not overlap.")
            previous_end = end
        return self


class WeatherHour(APIModel):
    time: str
    temperatureC: float = Field(ge=-100, le=80)
    apparentTemperatureC: float = Field(ge=-150, le=100)
    precipitationProbability: float | None = Field(default=None, ge=0, le=100)

    @field_validator("time")
    @classmethod
    def whole_hour(cls, value: str) -> str:
        if clock_minutes(value) % 60:
            raise ValueError("Weather observations must be at whole-hour times.")
        return value


class Weather(APIModel):
    source: Literal["Open-Meteo"] = "Open-Meteo"
    fetchedAt: str
    mode: Literal["live", "saved"]
    date: str
    timezone: Literal["Asia/Kolkata"] = "Asia/Kolkata"
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    gridLatitude: float = Field(ge=-90, le=90)
    gridLongitude: float = Field(ge=-180, le=180)
    hours: list[WeatherHour] = Field(min_length=1, max_length=24)
    attribution: str
    sourceUrl: str
    warnings: list[str] = Field(default_factory=list)

    _calendar_date = field_validator("date")(valid_date)

    @field_validator("hours")
    @classmethod
    def distinct_hours(cls, values: list[WeatherHour]) -> list[WeatherHour]:
        if len({entry.time for entry in values}) != len(values):
            raise ValueError("Weather contains duplicate hours.")
        return sorted(values, key=lambda entry: entry.time)


class ScheduleItem(APIModel):
    taskId: str
    title: str
    start: str
    end: str
    locked: bool
    meanApparentTemperatureC: float


class PlanMetrics(APIModel):
    workMinutes: int
    baselineMeanApparentTemperatureC: float | None
    proposedMeanApparentTemperatureC: float | None
    deltaC: float | None
    baselineHotMinutes: int | None
    proposedHotMinutes: int | None
    thresholdC: float


class ConstraintCheck(APIModel):
    label: str
    passed: bool


class PlanResult(APIModel):
    status: Literal["improved", "unchanged", "planned", "infeasible"]
    schedule: list[ScheduleItem]
    baselineSchedule: list[ScheduleItem]
    baselineValid: bool
    metrics: PlanMetrics
    explanation: str
    violations: list[str]
    constraintChecks: list[ConstraintCheck]
    weather: Weather
    request: PlanRequest
