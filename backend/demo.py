"""Illustrative scenario, deliberately not represented as actual DTU operations."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from .models import PlanRequest


def demo_plan() -> PlanRequest:
    tomorrow = datetime.now(ZoneInfo("Asia/Kolkata")).date() + timedelta(days=1)
    return PlanRequest.model_validate({
        "date": tomorrow.isoformat(),
        "location": {"name": "Delhi · DTU (illustrative)", "latitude": 28.75, "longitude": 77.12},
        "shiftStart": "08:00", "shiftEnd": "17:00",
        "breaks": [{"start": "12:30", "end": "13:00"}], "thresholdC": 32,
        "tasks": [
            {"id": "grounds", "title": "Grounds cleanup", "durationMinutes": 60,
             "earliestStart": "08:00", "latestEnd": "17:00", "baselineStart": "11:30", "locked": False},
            {"id": "garden", "title": "Garden maintenance", "durationMinutes": 60,
             "earliestStart": "08:00", "latestEnd": "17:00", "baselineStart": "13:00", "locked": False},
            {"id": "inspection", "title": "Fixed contractor inspection", "durationMinutes": 30,
             "earliestStart": "10:00", "latestEnd": "10:30", "baselineStart": "10:00", "locked": True},
            {"id": "pathways", "title": "Pathway sweeping", "durationMinutes": 45,
             "earliestStart": "08:00", "latestEnd": "17:00", "baselineStart": "14:00", "locked": False},
        ],
    })
