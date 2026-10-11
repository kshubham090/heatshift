"""Offline API proofs that budget admission precedes all model execution."""
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from backend import agent, app as api, cloud_budget
from backend.demo import demo_plan


@pytest.fixture
def boundary(monkeypatch):
    # Isolate the global admission cap from the independent per-IP limiter.
    monkeypatch.setenv("HEATSHIFT_RATE_LIMIT", "0")
    monkeypatch.setenv("HEATSHIFT_AGENT_PROVIDER", "ollama")
    monkeypatch.delenv("HEATSHIFT_DAILY_BUDGET_TABLE", raising=False)
    monkeypatch.delenv("HEATSHIFT_PUBLIC_HOSTED", raising=False)
    monkeypatch.delenv("HEATSHIFT_DAILY_AGENT_LIMIT", raising=False)
    model_calls = []

    async def offline_model(message, plan):
        model_calls.append((message, plan.model_dump()))
        return {"message": "Explicit offline API-test response", "proposedPlan": None,
                "result": None, "trace": [], "provider": "ollama", "model": "test-double",
                "requiresApproval": False}

    monkeypatch.setattr(agent, "run_agent", offline_model)
    with TestClient(api.app) as client:
        yield SimpleNamespace(client=client, model_calls=model_calls,
                              body={"message": " Inspect the current plan. ", "plan": demo_plan().model_dump()})


@pytest.mark.parametrize("error_code,expected_status,expected_message", [
    ("ConditionalCheckFailedException", 429, "Today's hosted assistant limit has been reached"),
    ("AccessDeniedException", 503, "hosted assistant limit could not be checked"),
])
def test_real_budget_failure_prevents_model_invocation(boundary, monkeypatch, error_code, expected_status, expected_message):
    monkeypatch.setenv("HEATSHIFT_PUBLIC_HOSTED", "1")
    monkeypatch.setenv("HEATSHIFT_DAILY_BUDGET_TABLE", "test-daily-admission")
    counter_calls = []

    class CounterFailure(Exception):
        response = {"Error": {"Code": error_code, "Message": "DO_NOT_EXPOSE_PROVIDER_DETAIL"}}

    class OfflineCounter:
        def update_item(self, **kwargs):
            counter_calls.append(kwargs)
            raise CounterFailure("DO_NOT_EXPOSE_PROVIDER_DETAIL")

    # Keep the real reserve_agent_slot and HTTP endpoint; substitute only the
    # network-facing DynamoDB client so no AWS operation can occur.
    monkeypatch.setattr(cloud_budget, "_client", lambda: OfflineCounter())
    response = boundary.client.post("/api/agent", json=boundary.body)
    assert response.status_code == expected_status, response.text
    assert expected_message in response.json()["detail"]
    assert "DO_NOT_EXPOSE_PROVIDER_DETAIL" not in response.text
    assert len(counter_calls) == 1
    assert counter_calls[0]["TableName"] == "test-daily-admission"
    assert not boundary.model_calls


def test_missing_required_hosted_table_fails_before_client_or_model(boundary, monkeypatch):
    monkeypatch.setenv("HEATSHIFT_PUBLIC_HOSTED", "1")
    client_calls = []

    def forbidden_client():
        client_calls.append(True)
        raise AssertionError("A missing table must fail before contacting a cloud SDK")

    monkeypatch.setattr(cloud_budget, "_client", forbidden_client)
    response = boundary.client.post("/api/agent", json=boundary.body)
    assert response.status_code == 503
    assert "hosted assistant limit could not be checked" in response.json()["detail"]
    assert not client_calls
    assert not boundary.model_calls


def test_local_default_reaches_agent_without_any_cloud_client(boundary, monkeypatch):
    client_calls = []

    def forbidden_client():
        client_calls.append(True)
        raise AssertionError("Local defaults must not contact DynamoDB")

    monkeypatch.setattr(cloud_budget, "_client", forbidden_client)
    response = boundary.client.post("/api/agent", json=boundary.body)
    assert response.status_code == 200, response.text
    assert boundary.model_calls == [("Inspect the current plan.", boundary.body["plan"])]
    assert not client_calls
    assert response.json()["provider"] == "ollama"


@pytest.mark.parametrize("message", ["", " \t\n   "])
def test_empty_message_never_reserves_a_slot_or_invokes_model(boundary, monkeypatch, message):
    reservations = []

    def forbidden_reservation():
        reservations.append(True)
        raise AssertionError("Whitespace must be rejected before admission is reserved")

    monkeypatch.setattr(api, "reserve_agent_slot", forbidden_reservation)
    response = boundary.client.post("/api/agent", json={**boundary.body, "message": message})
    assert response.status_code == 422
    assert not reservations
    assert not boundary.model_calls
