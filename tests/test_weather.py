"""Provider failures, dates, units and honest saved-forecast behavior."""
import asyncio
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import httpx
import pytest

from backend import weather
from backend.weather import WeatherUnavailable, get_weather


def tomorrow():
    return (datetime.now(ZoneInfo("Asia/Kolkata")).date() + timedelta(days=1)).isoformat()


def payload(date=None):
    selected = date or tomorrow()
    return {"latitude": 28.787, "longitude": 77.143, "timezone": "Asia/Kolkata",
            "hourly_units": {"temperature_2m": "°C", "apparent_temperature": "°C", "precipitation_probability": "%"},
            "hourly": {"time": [f"{selected}T{hour:02d}:00" for hour in range(24)],
                       "temperature_2m": [29.0] * 24, "apparent_temperature": [33.0] * 24,
                       "precipitation_probability": [10] * 24}}


@pytest.fixture(autouse=True)
def isolated_cache():
    weather._CACHE.clear()
    yield
    weather._CACHE.clear()


def mock_service(monkeypatch, handler):
    original = httpx.AsyncClient
    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(weather.httpx, "AsyncClient", lambda **kwargs: original(transport=transport, **kwargs))


def test_real_response_then_saved_cache_keeps_source_time(monkeypatch):
    calls = []
    def respond(request):
        calls.append(request)
        assert request.url.params["temperature_unit"] == "celsius"
        return httpx.Response(200, json=payload())
    mock_service(monkeypatch, respond)
    first = asyncio.run(get_weather(28.75, 77.12, tomorrow()))
    second = asyncio.run(get_weather(28.75, 77.12, tomorrow()))
    assert first.mode == "live"
    assert second.mode == "saved"
    assert first.fetchedAt == second.fetchedAt
    assert first.latitude == 28.75 and first.gridLatitude == 28.787
    assert len(first.hours) == 24
    assert len(calls) == 1
    assert any("saved" in warning for warning in second.warnings)


@pytest.mark.parametrize("corruption", ["missing", "wrong_date", "fahrenheit", "nan", "duplicate", "range", "timezone"])
def test_bad_provider_data_is_never_used_as_a_forecast(monkeypatch, corruption):
    data = payload()
    if corruption == "missing":
        data["hourly"]["apparent_temperature"][9] = None
    elif corruption == "wrong_date":
        data["hourly"]["time"][0] = "2020-01-01T00:00"
    elif corruption == "fahrenheit":
        data["hourly_units"]["apparent_temperature"] = "°F"
    elif corruption == "nan":
        data["hourly"]["temperature_2m"][0] = "NaN"
    elif corruption == "duplicate":
        data["hourly"]["time"][1] = data["hourly"]["time"][0]
    elif corruption == "range":
        data["hourly"]["apparent_temperature"][0] = 400
    else:
        data["timezone"] = "UTC"
    mock_service(monkeypatch, lambda request: httpx.Response(200, json=data))
    with pytest.raises(WeatherUnavailable):
        asyncio.run(get_weather(28.75, 77.12, tomorrow()))
    assert not weather._CACHE


def test_provider_failure_without_cache_is_honest(monkeypatch):
    mock_service(monkeypatch, lambda request: httpx.Response(503))
    with pytest.raises(WeatherUnavailable, match="No usable saved forecast"):
        asyncio.run(get_weather(28.75, 77.12, tomorrow()))


def test_timeout_falls_back_only_to_same_date_location_and_retains_age(monkeypatch):
    initial = weather._parse_response(payload(), 28.75, 77.12, tomorrow(), "https://example.test")
    fetched_at = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
    initial = initial.model_copy(update={"fetchedAt": fetched_at})
    weather._CACHE[(28.75, 77.12, tomorrow())] = initial
    def fail(request):
        raise httpx.ReadTimeout("test timeout", request=request)
    mock_service(monkeypatch, fail)
    saved = asyncio.run(get_weather(28.75, 77.12, tomorrow()))
    assert saved.mode == "saved"
    assert saved.fetchedAt == fetched_at
    assert any("same date and location" in value for value in saved.warnings)
    with pytest.raises(WeatherUnavailable):
        asyncio.run(get_weather(19.07, 72.88, tomorrow()))
    different_date = (datetime.now(ZoneInfo("Asia/Kolkata")).date() + timedelta(days=2)).isoformat()
    with pytest.raises(WeatherUnavailable):
        asyncio.run(get_weather(28.75, 77.12, different_date))


def test_more_than_day_old_saved_forecast_is_rejected_on_failure(monkeypatch):
    initial = weather._parse_response(payload(), 28.75, 77.12, tomorrow(), "https://example.test")
    initial = initial.model_copy(update={"fetchedAt": (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()})
    weather._CACHE[(28.75, 77.12, tomorrow())] = initial
    mock_service(monkeypatch, lambda request: httpx.Response(503))
    with pytest.raises(WeatherUnavailable):
        asyncio.run(get_weather(28.75, 77.12, tomorrow()))


def test_invalid_coordinates_and_outside_forecast_dates(monkeypatch):
    def unexpected(request):
        pytest.fail("Invalid inputs should not make network requests")
    mock_service(monkeypatch, unexpected)
    for latitude, selected in [(999, tomorrow()), (float("nan"), tomorrow()), (28.75, "2020-01-01"), (28.75, "bad-date")]:
        with pytest.raises(WeatherUnavailable):
            asyncio.run(get_weather(latitude, 77.12, selected))
