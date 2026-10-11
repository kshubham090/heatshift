"""An atomic daily admission cap for the optional public Bedrock assistant.

Call reserve_agent_slot() in a worker thread immediately before starting an
agent request. It does not cap non-agent hosting traffic or currency spend.
Local defaults do not import boto3 or contact DynamoDB. A reserved attempt is
not refunded when inference fails, so retries cannot bypass the cap.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import lru_cache
import os
from zoneinfo import ZoneInfo


class CloudBudgetUnavailable(RuntimeError):
    """Admission could not be verified. The caller must not run the agent."""


class CloudBudgetExceeded(CloudBudgetUnavailable):
    """The current day's admitted hosted attempts have reached the limit."""


@dataclass(frozen=True)
class BudgetReservation:
    enforced: bool
    day: str | None = None
    limit: int | None = None
    used: int | None = None


def _now() -> datetime:
    return datetime.now(timezone.utc)


@lru_cache(maxsize=1)
def _client():
    # Lazy: a normal local Ollama run never imports the cloud SDK here.
    import boto3
    from botocore.config import Config
    return boto3.client(
        "dynamodb",
        config=Config(connect_timeout=2, read_timeout=3,
                      retries={"total_max_attempts": 1}),
    )


def reserve_agent_slot() -> BudgetReservation:
    """Atomically admit one attempt across all Lambda instances, or fail closed.

    Day boundaries are Asia/Kolkata. TTL only cleans old rows; the exact date
    partition key, not asynchronous DynamoDB expiration, resets the allowance.
    HEATSHIFT_PUBLIC_HOSTED=1 prevents a missing table from disabling the cap.
    """
    table = os.getenv("HEATSHIFT_DAILY_BUDGET_TABLE", "").strip()
    public_hosted = os.getenv("HEATSHIFT_PUBLIC_HOSTED", "0") == "1"
    if not table:
        if public_hosted:
            raise CloudBudgetUnavailable(
                "The hosted assistant limit could not be checked. "
                "Please try again later; the planner still works."
            )
        return BudgetReservation(enforced=False)

    try:
        raw_limit = os.getenv("HEATSHIFT_DAILY_AGENT_LIMIT", "25")
        if not raw_limit.isdigit():
            raise ValueError("Invalid daily limit")
        limit = int(raw_limit)
        if not 1 <= limit <= 100:
            raise ValueError("Invalid daily limit")
        local_now = _now().astimezone(ZoneInfo("Asia/Kolkata"))
        day = local_now.date().isoformat()
        expiry = int((local_now.replace(hour=0, minute=0, second=0, microsecond=0)
                      + timedelta(days=3)).timestamp())
        response = _client().update_item(
            TableName=table,
            Key={"day": {"S": day}},
            UpdateExpression="SET #ttl = :ttl ADD #used :one",
            ConditionExpression="attribute_not_exists(#used) OR #used < :limit",
            ExpressionAttributeNames={"#used": "used", "#ttl": "expiresAt"},
            ExpressionAttributeValues={
                ":ttl": {"N": str(expiry)}, ":one": {"N": "1"},
                ":limit": {"N": str(limit)},
            },
            ReturnValues="UPDATED_NEW",
        )
        used = int(response["Attributes"]["used"]["N"])
        if not 1 <= used <= limit:
            raise ValueError("Unexpected counter response")
        return BudgetReservation(enforced=True, day=day, limit=limit, used=used)
    except Exception as exc:
        if getattr(exc, "response", {}).get("Error", {}).get("Code") == "ConditionalCheckFailedException":
            raise CloudBudgetExceeded(
                "Today's hosted assistant limit has been reached. "
                "It resets at midnight IST; the planner still works."
            ) from None
        raise CloudBudgetUnavailable(
            "The hosted assistant limit could not be checked. "
            "Please try again later; the planner still works."
        ) from None
