"""The hosted admission cap must be atomic, fail closed, and stay off locally."""
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

import pytest

from backend import cloud_budget as budget


class ConditionalFailure(Exception):
    response = {"Error": {"Code": "ConditionalCheckFailedException"}}


class AtomicCounter:
    """A tiny DynamoDB conditional-update contract fake, not a network client."""
    def __init__(self):
        self.values = {}
        self.calls = []
        self.lock = Lock()

    def update_item(self, **kwargs):
        assert kwargs["ConditionExpression"] == "attribute_not_exists(#used) OR #used < :limit"
        assert kwargs["UpdateExpression"] == "SET #ttl = :ttl ADD #used :one"
        assert kwargs["ReturnValues"] == "UPDATED_NEW"
        day = kwargs["Key"]["day"]["S"]
        limit = int(kwargs["ExpressionAttributeValues"][":limit"]["N"])
        with self.lock:
            self.calls.append(kwargs)
            if self.values.get(day, 0) >= limit:
                raise ConditionalFailure()
            self.values[day] = self.values.get(day, 0) + 1
            return {"Attributes": {"used": {"N": str(self.values[day])}}}


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
    for key in ("HEATSHIFT_DAILY_BUDGET_TABLE", "HEATSHIFT_DAILY_AGENT_LIMIT", "HEATSHIFT_PUBLIC_HOSTED"):
        monkeypatch.delenv(key, raising=False)


def test_local_defaults_never_request_a_cloud_client(monkeypatch):
    monkeypatch.setattr(budget, "_client", lambda: pytest.fail("Local run contacted cloud"))
    assert budget.reserve_agent_slot() == budget.BudgetReservation(enforced=False)


def test_public_flag_requires_a_table(monkeypatch):
    monkeypatch.setenv("HEATSHIFT_PUBLIC_HOSTED", "1")
    with pytest.raises(budget.CloudBudgetUnavailable):
        budget.reserve_agent_slot()


def test_default_cap_admits_only_25_even_when_requests_race(monkeypatch):
    counter = AtomicCounter()
    monkeypatch.setenv("HEATSHIFT_DAILY_BUDGET_TABLE", "heatshift-budget")
    monkeypatch.setattr(budget, "_client", lambda: counter)
    monkeypatch.setattr(budget, "_now", lambda: datetime(2026, 10, 11, 12, tzinfo=timezone.utc))
    def attempt(_):
        try:
            return budget.reserve_agent_slot().used
        except budget.CloudBudgetExceeded:
            return None
    with ThreadPoolExecutor(max_workers=12) as pool:
        admitted = [v for v in pool.map(attempt, range(70)) if v is not None]
    assert sorted(admitted) == list(range(1, 26))
    assert counter.values == {"2026-10-11": 25}
    assert all(c["TableName"] == "heatshift-budget" for c in counter.calls)


def test_new_ist_day_uses_a_new_key_without_waiting_for_ttl(monkeypatch):
    counter = AtomicCounter()
    monkeypatch.setenv("HEATSHIFT_DAILY_BUDGET_TABLE", "heatshift-budget")
    monkeypatch.setenv("HEATSHIFT_DAILY_AGENT_LIMIT", "1")
    monkeypatch.setattr(budget, "_client", lambda: counter)
    monkeypatch.setattr(budget, "_now", lambda: datetime(2026, 10, 11, 18, 29, tzinfo=timezone.utc))
    first = budget.reserve_agent_slot()
    with pytest.raises(budget.CloudBudgetExceeded):
        budget.reserve_agent_slot()
    monkeypatch.setattr(budget, "_now", lambda: datetime(2026, 10, 11, 18, 30, tzinfo=timezone.utc))
    second = budget.reserve_agent_slot()
    assert first.day == "2026-10-11" and second.day == "2026-10-12"
    assert second.used == 1


@pytest.mark.parametrize("invalid", ["0", "-1", "101", "1.5", "abc", "", " 25"])
def test_invalid_configuration_fails_before_cloud_access(monkeypatch, invalid):
    monkeypatch.setenv("HEATSHIFT_DAILY_BUDGET_TABLE", "heatshift-budget")
    monkeypatch.setenv("HEATSHIFT_DAILY_AGENT_LIMIT", invalid)
    monkeypatch.setattr(budget, "_client", lambda: pytest.fail("Invalid config contacted cloud"))
    with pytest.raises(budget.CloudBudgetUnavailable):
        budget.reserve_agent_slot()


def test_cloud_failure_is_closed_and_does_not_leak_provider_details(monkeypatch):
    class BrokenClient:
        def update_item(self, **_):
            raise RuntimeError("sensitive account detail from provider")
    monkeypatch.setenv("HEATSHIFT_DAILY_BUDGET_TABLE", "heatshift-budget")
    monkeypatch.setattr(budget, "_client", lambda: BrokenClient())
    with pytest.raises(budget.CloudBudgetUnavailable) as caught:
        budget.reserve_agent_slot()
    assert "sensitive" not in str(caught.value)
    assert "planner still works" in str(caught.value)


def test_unreadable_counter_result_fails_closed(monkeypatch):
    class BrokenResponse:
        def update_item(self, **_):
            return {}
    monkeypatch.setenv("HEATSHIFT_DAILY_BUDGET_TABLE", "heatshift-budget")
    monkeypatch.setattr(budget, "_client", lambda: BrokenResponse())
    with pytest.raises(budget.CloudBudgetUnavailable):
        budget.reserve_agent_slot()
