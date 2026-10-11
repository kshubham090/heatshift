"""Open-Meteo adapter. Await get_weather(latitude, longitude, date).

Cache entries retain the original retrieval time and are keyed by exact requested
location and date. Only a complete real API response enters the cache.
"""
from __future__ import annotations

from datetime import date as CalendarDate, datetime, timedelta, timezone
import math
from typing import Any
from zoneinfo import ZoneInfo

import httpx
from pydantic import ValidationError

from .models import Weather, WeatherHour, valid_date


class WeatherUnavailable(RuntimeError):
    """A usable real forecast could not be obtained; expose as HTTP 503."""


_CACHE: dict[tuple[float, float, str], Weather] = {}
_CACHE_TTL_SECONDS = 900
_MAX_SAVED_AGE_SECONDS = 24 * 3600
_ENDPOINT = "https://api.open-meteo.com/v1/forecast"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _age_seconds(weather: Weather) -> float:
    return (_utc_now() - datetime.fromisoformat(weather.fetchedAt)).total_seconds()


def _saved(weather: Weather, message: str) -> Weather:
    warnings = list(weather.warnings)
    if message not in warnings:
        warnings.append(message)
    return weather.model_copy(update={"mode": "saved", "warnings": warnings}, deep=True)


def _parse_response(data: dict[str, Any], latitude: float, longitude: float,
                    selected_date: str, source_url: str) -> Weather:
    if data.get("timezone") != "Asia/Kolkata":
        raise WeatherUnavailable("Weather provider returned an unexpected timezone.")
    units = data.get("hourly_units", {})
    if units.get("temperature_2m") != "°C" or units.get("apparent_temperature") != "°C":
        raise WeatherUnavailable("Weather provider returned missing or non-Celsius temperature units.")
    if units.get("precipitation_probability") not in (None, "%"):
        raise WeatherUnavailable("Weather provider returned unexpected precipitation units.")
    hourly = data.get("hourly")
    if not isinstance(hourly, dict):
        raise WeatherUnavailable("Weather provider returned no hourly forecast.")
    times = hourly.get("time", [])
    temperatures = hourly.get("temperature_2m", [])
    apparent = hourly.get("apparent_temperature", [])
    rain = hourly.get("precipitation_probability")
    if not isinstance(times, list) or len(times) != 24:
        raise WeatherUnavailable("Weather provider did not return all 24 hours for this date.")
    if not isinstance(temperatures, list) or not isinstance(apparent, list) or len(temperatures) != 24 or len(apparent) != 24:
        raise WeatherUnavailable("Weather provider returned incomplete temperature data.")
    if rain is None:
        rain = [None] * 24
    if not isinstance(rain, list) or len(rain) != 24:
        raise WeatherUnavailable("Weather provider returned incomplete precipitation data.")
    hours = []
    expected = [f"{selected_date}T{hour:02d}:00" for hour in range(24)]
    if times != expected:
        raise WeatherUnavailable("Weather provider returned hours from a different or incomplete local date.")
    try:
        for index, stamp in enumerate(times):
            for value in (temperatures[index], apparent[index]):
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                    raise WeatherUnavailable("Weather provider has a missing or invalid temperature hour.")
            hours.append(WeatherHour(time=stamp[-5:], temperatureC=temperatures[index],
                                     apparentTemperatureC=apparent[index],
                                     precipitationProbability=rain[index]))
        return Weather(
            fetchedAt=_utc_now().isoformat(), mode="live", date=selected_date,
            latitude=latitude, longitude=longitude,
            gridLatitude=data["latitude"], gridLongitude=data["longitude"], hours=hours,
            sourceUrl=source_url,
            attribution="Weather data: Open-Meteo.com and its contributing national weather services, CC BY 4.0.",
            warnings=[
                "Forecast values describe a weather-model grid, not a sensor at this work site.",
                "Each hourly forecast value is held constant within its four 15-minute planning slots.",
                "Apparent temperature is a planning input, not an occupational heat-safety certification.",
            ],
        )
    except (ValidationError, KeyError, TypeError) as error:
        raise WeatherUnavailable("Weather provider returned invalid or out-of-range values.") from error


async def get_weather(latitude: float, longitude: float, date: str) -> Weather:
    """Fetch a forecast, or return clearly labeled same-date/location saved data.

    Raises WeatherUnavailable on every unavailable-data path. No synthetic
    fallback, backdated record, implicit Celsius conversion, or location rounding.
    """
    try:
        selected_date = CalendarDate.fromisoformat(valid_date(date))
        if not math.isfinite(latitude) or not math.isfinite(longitude) or not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            raise ValueError("Invalid coordinates")
    except (ValueError, TypeError) as error:
        raise WeatherUnavailable("Choose a valid date and geographic coordinates.") from error
    today = datetime.now(ZoneInfo("Asia/Kolkata")).date()
    if not today <= selected_date <= today + timedelta(days=15):
        raise WeatherUnavailable("Choose today or a forecast date within the next 15 days.")
    key = (float(latitude), float(longitude), date)
    cached = _CACHE.get(key)
    if cached is not None and 0 <= _age_seconds(cached) < _CACHE_TTL_SECONDS:
        return _saved(cached, "Using a date-matched saved forecast retrieved within the last 15 minutes.")
    params = {
        "latitude": latitude, "longitude": longitude,
        "hourly": "temperature_2m,apparent_temperature,precipitation_probability",
        "timezone": "Asia/Kolkata", "start_date": date, "end_date": date,
        "temperature_unit": "celsius",
    }
    source_url = str(httpx.URL(_ENDPOINT, params=params))
    reason = "Weather service is temporarily unavailable."
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0), follow_redirects=False) as client:
            response = await client.get(_ENDPOINT, params=params)
            response.raise_for_status()
            data = response.json()
        if not isinstance(data, dict):
            raise WeatherUnavailable("Weather provider returned an invalid response.")
        parsed = _parse_response(data, latitude, longitude, date, source_url)
        if len(_CACHE) >= 128:
            oldest_key = min(_CACHE, key=lambda cache_key: _CACHE[cache_key].fetchedAt)
            _CACHE.pop(oldest_key, None)
        _CACHE[key] = parsed.model_copy(deep=True)
        return parsed
    except WeatherUnavailable as error:
        reason = str(error)
    except (httpx.HTTPError, ValueError, TypeError):
        reason = "Weather service could not supply a valid forecast."
    if cached is not None and 0 <= _age_seconds(cached) <= _MAX_SAVED_AGE_SECONDS:
        return _saved(cached, f"{reason} Showing a saved forecast for this same date and location; check its retrieval time.")
    raise WeatherUnavailable(f"{reason} No usable saved forecast exists for this date and location. Try again shortly.")
