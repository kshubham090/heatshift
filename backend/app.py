"""HTTP boundary: validate requests, use real data, and serve the built client."""
from __future__ import annotations

import asyncio
import inspect
import logging
import os
import time
from collections import OrderedDict, deque
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from mangum import Mangum

from .models import PlanRequest
from .optimizer import optimize
from .weather import WeatherUnavailable, get_weather
from .demo import demo_plan
from .cloud_budget import reserve_agent_slot, CloudBudgetExceeded, CloudBudgetUnavailable

logger = logging.getLogger("heatshift")
app = FastAPI(title="HeatShift", version="1.0.0", description="One crew. The same work. A cooler feasible plan.")
ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
AGENT_TIMEOUT = float(os.getenv("HEATSHIFT_AGENT_TIMEOUT", "120"))
_agent_semaphore = asyncio.Semaphore(1)
_rate_windows: OrderedDict[tuple[str, str], deque[float]] = OrderedDict()

class AgentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str = Field(min_length=1, max_length=2000)
    plan: PlanRequest

    @field_validator("message")
    @classmethod
    def meaningful_message(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Enter a planning request.")
        return value.strip()

@app.middleware("http")
async def bounded_requests(request: Request, call_next):
    if request.method == "POST":
        # Small, structured plans only. Images and documents are not uploaded.
        content_length = request.headers.get("content-length")
        if content_length and (not content_length.isdigit() or int(content_length) > 65536):
            return JSONResponse({"detail": "This plan is too large. Keep it to eight jobs."}, status_code=413)
        chunks = []
        size = 0
        async for chunk in request.stream():
            size += len(chunk)
            if size > 65536:
                return JSONResponse({"detail": "This plan is too large. Keep it to eight jobs."}, status_code=413)
            chunks.append(chunk)
        # Starlette's cached request replays _body to the route's JSON parser.
        # Read incrementally first, so chunked requests cannot bypass the limit.
        request._body = b"".join(chunks)
        if request.url.path not in {"/api/agent", "/api/optimize"}:
            return JSONResponse({"detail": "Unknown API route"}, status_code=404)
        if os.getenv("HEATSHIFT_RATE_LIMIT", "1") == "1":
            now = time.monotonic()
            peer = request.client.host if request.client else "unknown"
            key = (peer, request.url.path)
            window = _rate_windows.setdefault(key, deque())
            _rate_windows.move_to_end(key)
            while len(_rate_windows) > 2000:
                _rate_windows.popitem(last=False)
            while window and window[0] <= now - 60:
                window.popleft()
            limit = 6 if request.url.path == "/api/agent" else 60
            if len(window) >= limit:
                return JSONResponse({"detail": "Please wait a minute before trying again."}, status_code=429, headers={"Retry-After": "60"})
            window.append(now)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response

@app.get("/api/health")
async def health():
    try:
        from .agent import get_agent_status
        status = await asyncio.wait_for(asyncio.to_thread(get_agent_status), timeout=4)
        if inspect.isawaitable(status):
            status = await asyncio.wait_for(status, timeout=4)
    except Exception:
        status = {"available": False, "provider": os.getenv("HEATSHIFT_AGENT_PROVIDER", "ollama"), "model": os.getenv("HEATSHIFT_AGENT_MODEL", "qwen3:1.7b")}
    return {"status": "ok", "agent": status, "version": "1.0.0"}

@app.get("/api/demo")
async def demo():
    return {"plan": demo_plan()}

@app.get("/api/weather")
async def weather_endpoint(latitude: float = Query(ge=-90, le=90), longitude: float = Query(ge=-180, le=180), date: str = Query(pattern=r"^\d{4}-\d{2}-\d{2}$")):
    try:
        return await get_weather(latitude, longitude, date)
    except WeatherUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.post("/api/optimize")
async def optimize_endpoint(plan: PlanRequest):
    try:
        weather = await get_weather(plan.location.latitude, plan.location.longitude, plan.date)
        return await asyncio.to_thread(optimize, plan, weather)
    except WeatherUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.post("/api/agent")
async def agent_endpoint(body: AgentRequest):
    from .agent import run_agent
    if _agent_semaphore.locked():
        raise HTTPException(status_code=429, detail="The assistant is finishing another request. Please try again shortly.")
    try:
        async with _agent_semaphore:
            await asyncio.to_thread(reserve_agent_slot)
            return await asyncio.wait_for(run_agent(body.message.strip(), body.plan), timeout=AGENT_TIMEOUT)
    except CloudBudgetExceeded as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except CloudBudgetUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except asyncio.TimeoutError as exc:
        raise HTTPException(status_code=504, detail="The assistant took too long. Your current plan is unchanged. You can still use the planner.") from exc
    except (ValidationError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="The proposed change was not valid. Please specify the job and its time window.") from exc
    except Exception as exc:
        # Never echo model prompts, credentials, raw SDK traces or provider responses.
        logger.warning("Agent request failed: %s", type(exc).__name__)
        raise HTTPException(status_code=503, detail="The AI assistant is unavailable. Your current plan is unchanged. The deterministic planner still works.") from exc

if (DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

@app.get("/{path:path}", include_in_schema=False)
async def frontend(path: str):
    if path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Unknown API route")
    requested = (DIST / path).resolve()
    if requested.is_relative_to(DIST.resolve()) and requested.is_file():
        return FileResponse(requested)
    index = DIST / "index.html"
    if index.exists():
        return FileResponse(index)
    return JSONResponse({"service": "HeatShift", "message": "Backend ready. Run the frontend development server or build the client.", "docs": "/docs"})

handler = Mangum(app, lifespan="off")
