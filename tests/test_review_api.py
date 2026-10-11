"""Regression tests for bounded streaming and real middleware rate state.

These tests drive the ASGI app with chunked requests and distinct client peers;
they do not bypass the middleware or replace the rate limiter.
"""
import asyncio
from datetime import datetime, timezone
import json

import httpx
import pytest

from backend import app as api
from backend.demo import demo_plan
from backend.models import Weather, WeatherHour


@pytest.fixture(autouse=True)
def clean_rate_state(monkeypatch):
    monkeypatch.setenv("HEATSHIFT_RATE_LIMIT", "1")
    api._rate_windows.clear()
    yield
    api._rate_windows.clear()


def test_chunked_oversized_body_stops_reading_at_limit():
    async def run():
        consumed = 0

        async def body():
            nonlocal consumed
            for _ in range(100):
                consumed += 1
                yield b"x" * 1024

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api.app), base_url="http://test") as client:
            response = await client.post("/api/agent", content=body(), headers={"Content-Type": "application/json"})
        assert response.status_code == 413
        # The first 64 chunks fit. Reading the 65th is enough to reject it;
        # draining all 100 would allow an unbounded stream to exhaust memory.
        assert consumed == 65
        assert not api._rate_windows

    asyncio.run(run())


def test_valid_chunked_json_is_replayed_to_route_without_corruption(monkeypatch):
    plan = demo_plan()
    calls = []

    async def fixture_weather(latitude, longitude, date):
        calls.append((latitude, longitude, date))
        return Weather(
            fetchedAt=datetime.now(timezone.utc).isoformat(), mode="saved", date=date,
            latitude=latitude, longitude=longitude, gridLatitude=latitude, gridLongitude=longitude,
            hours=[WeatherHour(time=f"{hour:02d}:00", temperatureC=28, apparentTemperatureC=30)
                   for hour in range(24)],
            attribution="Explicit synthetic review test fixture", sourceUrl="https://example.invalid/review",
        )

    monkeypatch.setattr(api, "get_weather", fixture_weather)
    encoded = json.dumps(plan.model_dump(), ensure_ascii=False).encode("utf-8")

    async def run():
        async def body():
            # Small uneven byte chunks also split multibyte UTF-8 characters.
            for offset in range(0, len(encoded), 7):
                yield encoded[offset:offset + 7]

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api.app), base_url="http://test") as client:
            response = await client.post("/api/optimize", content=body(), headers={"Content-Type": "application/json"})
        assert response.status_code == 200, response.text
        assert response.json()["request"] == plan.model_dump()
        assert response.json()["metrics"]["workMinutes"] == 195
        assert calls == [(plan.location.latitude, plan.location.longitude, plan.date)]

    asyncio.run(run())


def test_known_route_rate_cache_is_bounded_and_keeps_recent_peers():
    async def post_from(peer):
        transport = httpx.ASGITransport(app=api.app, client=(peer, 40000))
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/optimize", json={})
        # Empty plans fail schema validation after the actual middleware runs;
        # they require no weather or model calls.
        assert response.status_code == 422

    async def run():
        peers = [f"192.0.{index // 256}.{index % 256}" for index in range(2001)]
        for peer in peers[:2000]:
            await post_from(peer)
        assert len(api._rate_windows) == 2000
        await post_from(peers[0])  # Refresh the oldest peer's recency.
        await post_from(peers[2000])
        assert len(api._rate_windows) == 2000
        assert (peers[0], "/api/optimize") in api._rate_windows
        assert (peers[1], "/api/optimize") not in api._rate_windows
        assert (peers[2000], "/api/optimize") in api._rate_windows

    asyncio.run(run())


def test_unknown_post_paths_do_not_allocate_rate_cache_entries():
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api.app), base_url="http://test") as client:
            for index in range(30):
                response = await client.post(f"/unknown-{index}", json={})
                assert response.status_code == 404
        assert not api._rate_windows

    asyncio.run(run())
