"""Agent boundaries tested without making model calls or inventing a live result."""
import asyncio
from types import SimpleNamespace

import pytest

from backend import agent as agent_module
from backend.agent import AgentUnavailable, PlanningSession, _guard_changes, run_agent
from backend.demo import demo_plan
from backend.models import PlanRequest, Weather, WeatherHour
from backend.weather import WeatherUnavailable


@pytest.fixture
def plan():
    return demo_plan()


def weather_for(plan):
    """Deliberately synthetic weather, only for offline constraint tests."""
    return Weather(
        source="Open-Meteo", fetchedAt="2026-10-11T13:00:00Z", mode="saved",
        date=plan.date, timezone="Asia/Kolkata",
        latitude=plan.location.latitude, longitude=plan.location.longitude,
        gridLatitude=plan.location.latitude, gridLongitude=plan.location.longitude,
        hours=[WeatherHour(time=f"{hour:02d}:00", temperatureC=25 + hour / 4,
                           apparentTemperatureC=25 + hour / 3, precipitationProbability=0)
               for hour in range(24)],
        attribution="Synthetic offline test fixture; not measured weather.",
        sourceUrl="https://example.invalid/test-weather", warnings=["TEST FIXTURE"],
    )


def revised(plan, change):
    value = plan.model_dump(mode="json")
    change(value)
    return PlanRequest.model_validate(value)


def test_cannot_drop_work_to_make_plan_cooler(plan):
    candidate = revised(plan, lambda value: value["tasks"].pop(0))
    with pytest.raises(ValueError, match="removal was not explicitly requested"):
        _guard_changes(plan, candidate, "Optimize this plan and make it cooler.")


def test_negated_removal_is_not_permission(plan):
    candidate = revised(plan, lambda value: value["tasks"].pop(0))
    with pytest.raises(ValueError):
        _guard_changes(plan, candidate, "Do not remove grounds cleanup. Find a cooler plan.")


def test_negated_unlock_is_not_permission(plan):
    candidate = revised(plan, lambda value: value["tasks"][2].update(locked=False))
    with pytest.raises(ValueError, match="lock"):
        _guard_changes(plan, candidate, "Do not unlock the inspection.")


def test_baseline_preservation_cannot_be_overridden_by_move_verb(plan):
    candidate = revised(plan, lambda value: value["tasks"][0].update(baselineStart="15:00"))
    with pytest.raises(ValueError, match="baseline"):
        _guard_changes(plan, candidate, "Move grounds cleanup earlier but keep its original baseline unchanged.")


def test_requested_time_cannot_be_replaced_by_another_clock(plan):
    candidate = revised(plan, lambda value: value["tasks"][1].update(earliestStart="09:00"))
    with pytest.raises(ValueError, match="exact clock"):
        _guard_changes(plan, candidate, "Change garden maintenance to start after 13:00.")


def test_shift_start_request_cannot_extend_both_shift_ends(plan):
    candidate = revised(plan, lambda value: value.update(shiftStart="07:00", shiftEnd="18:00"))
    with pytest.raises(ValueError, match="exact clock"):
        _guard_changes(plan, candidate, "Set the paid shift start to09:00.")


def test_correct_shift_clock_without_intervening_space_is_valid(plan):
    candidate = revised(plan, lambda value: value.update(shiftStart="09:00"))
    _guard_changes(plan, candidate, "Do not unlock the inspection. Set the paid shift start to09:00.")


def test_shared_maintenance_word_cannot_authorize_another_task(plan):
    value = plan.model_dump(mode="json")
    value["tasks"][0]["title"] = "Courtyard maintenance"
    plan = PlanRequest.model_validate(value)
    candidate = revised(plan, lambda value: value["tasks"][0].update(earliestStart="13:00"))
    with pytest.raises(ValueError, match="window"):
        _guard_changes(plan, candidate, "Garden maintenance can only start after 13:00.")


def test_named_explicit_removal_remains_only_a_proposal(plan):
    candidate = revised(plan, lambda value: value["tasks"].pop(0))
    session = PlanningSession(plan, "Remove grounds cleanup from this plan.")
    session.propose_plan(candidate.model_dump(mode="json"))
    assert len(session.proposed.tasks) == 3
    assert len(plan.tasks) == 4
    assert session.response("ollama", "test")["requiresApproval"] is True


@pytest.mark.parametrize("change,expected", [
    (lambda value: value["tasks"][0].update(durationMinutes=30), "duration"),
    (lambda value: value["tasks"][2].update(locked=False), "lock"),
    (lambda value: value.update(shiftEnd="18:00"), "paid shift"),
    (lambda value: value.update(breaks=[]), "breaks"),
    (lambda value: value["tasks"][2].update(earliestStart="08:00"), "window"),
    (lambda value: value["tasks"][0].update(baselineStart="09:00"), "baseline"),
    (lambda value: value.update(thresholdC=40), "threshold"),
])
def test_cannot_silently_relax_constraints(plan, change, expected):
    with pytest.raises(ValueError, match=expected):
        _guard_changes(plan, revised(plan, change), "Find the best cooler schedule.")


def test_explicit_task_window_change_is_allowed(plan):
    candidate = revised(plan, lambda value: value["tasks"][1].update(earliestStart="13:00"))
    _guard_changes(plan, candidate, "Garden maintenance can only start after 13:00.")


@pytest.mark.parametrize("change", [
    lambda value: value.update(shiftEnd="18:00"),
    lambda value: value.update(breaks=[]),
    lambda value: value["tasks"][0].update(durationMinutes=30),
    lambda value: value["tasks"][2].update(locked=False),
    lambda value: value["tasks"][2].update(earliestStart="08:00"),
])
def test_mentioning_preserved_controls_is_not_permission(plan, change):
    with pytest.raises(ValueError):
        _guard_changes(plan, revised(plan, change),
                       "Replan grounds cleanup, garden and inspection while preserving all work durations, shift, lunch break, task windows and inspection lock.")


def test_invalid_proposal_records_real_error_and_keeps_current(plan):
    session = PlanningSession(plan, "Make grounds cleanup 17 minutes.")
    bad = plan.model_dump(mode="json")
    bad["tasks"][0]["durationMinutes"] = 17
    with pytest.raises(ValueError, match="multiple of 15"):
        session.propose_plan(bad)
    assert session.proposed is None
    assert session.trace == [{
        "tool": "propose_plan", "status": "error",
        "summary": "tasks.0.durationMinutes: Value error, Task duration must be a multiple of 15 minutes.",
    }]


def test_small_task_patch_validates_complete_plan_and_preserves_other_fields(plan):
    session = PlanningSession(plan, "Garden maintenance can only start after 13:00.")
    session.propose_changes({"tasks": {"garden": {"earliestStart": "13:00"}}})
    expected = plan.model_dump(mode="json")
    expected["tasks"][1]["earliestStart"] = "13:00"
    assert session.proposed.model_dump(mode="json") == expected
    assert plan.tasks[1].earliestStart == "08:00"


@pytest.mark.parametrize("patch", [
    {"madeUpField": True},
    {"tasks": {"nonexistent": {"earliestStart": "13:00"}}},
    {"tasks": {"garden": {"id": "renamed"}}},
    {"tasks": {"garden": {"earliestStart": "13:07"}}},
])
def test_bad_patch_fails_without_applying_or_discarding_tasks(plan, patch):
    session = PlanningSession(plan, "Change garden maintenance to 13:00.")
    with pytest.raises(ValueError):
        session.propose_changes(patch)
    assert session.proposed is None
    assert len(plan.tasks) == 4
    assert session.trace[-1]["status"] == "error"


def test_rejected_edit_cannot_be_hidden_by_optimizing_original(plan, monkeypatch):
    session = PlanningSession(plan, "Find a cooler plan.")
    with pytest.raises(ValueError):
        session.propose_changes({"tasks": {"inspection": {"locked": False}}})
    with pytest.raises(ValueError, match="proposed edit was rejected"):
        asyncio.run(session.optimize_plan())
    assert session.result is None


def test_coordinates_cannot_come_from_model_memory(plan):
    candidate = revised(plan, lambda value: value["location"].update(name="Mumbai", latitude=19.07, longitude=72.87))
    with pytest.raises(ValueError, match="cannot invent"):
        _guard_changes(plan, candidate, "Change the location to Mumbai.")


def test_tools_reuse_real_fetch_and_never_mutate_original(plan, monkeypatch):
    calls = []

    async def fetch(latitude, longitude, date):
        calls.append((latitude, longitude, date))
        return weather_for(plan)

    monkeypatch.setattr(agent_module, "get_weather", fetch)
    before = plan.model_dump(mode="json")
    session = PlanningSession(plan, "Find a cooler schedule.")

    async def run():
        session.inspect_plan()
        await session.inspect_weather()
        await session.optimize_plan()

    asyncio.run(run())
    response = session.response("ollama", "test-model")
    assert len(calls) == 1
    assert [entry["tool"] for entry in response["trace"]] == ["inspect_plan", "inspect_weather", "optimize_plan"]
    assert all(entry["status"] == "complete" for entry in response["trace"])
    assert response["result"]["metrics"]["workMinutes"] == sum(task.durationMinutes for task in plan.tasks)
    assert response["proposedPlan"] == before
    assert response["result"]["request"] == before
    assert response["requiresApproval"] is True
    assert plan.model_dump(mode="json") == before


def test_new_proposal_invalidates_old_result(plan, monkeypatch):
    async def fetch(*args):
        return weather_for(plan)

    monkeypatch.setattr(agent_module, "get_weather", fetch)
    session = PlanningSession(plan, "Find a cooler schedule.")
    asyncio.run(session.optimize_plan())
    assert session.result is not None
    session.message = "Garden maintenance can only start after 13:00."
    candidate = revised(plan, lambda value: value["tasks"][1].update(earliestStart="13:00"))
    session.propose_plan(candidate.model_dump(mode="json"))
    assert session.result is None


def test_weather_failure_does_not_invent_result(plan, monkeypatch):
    async def fail(*args):
        raise WeatherUnavailable("No matching weather is available.")

    monkeypatch.setattr(agent_module, "get_weather", fail)
    session = PlanningSession(plan, "Find a cooler plan.")
    with pytest.raises(WeatherUnavailable):
        asyncio.run(session.optimize_plan())
    assert session.result is None
    assert session.dependency_error
    assert session.trace[-1]["status"] == "error"


def test_model_text_and_reasoning_never_enter_response(plan, monkeypatch):
    async def fetch(*args):
        return weather_for(plan)

    class TestAgent:
        def __init__(self, session):
            self.session = session

        async def invoke_async(self, prompt, **kwargs):
            assert kwargs["limits"]["turns"] == 6
            self.session.inspect_plan()
            await self.session.optimize_plan()
            return SimpleNamespace(stop_reason="end_turn", message="<think>private reasoning</think>99% safer")

    monkeypatch.setattr(agent_module, "get_weather", fetch)
    monkeypatch.setattr(agent_module, "_make_model", lambda *args: object())
    monkeypatch.setattr(agent_module, "_build_agent", lambda session, model: TestAgent(session))
    response = asyncio.run(run_agent("Find a cooler plan.", plan))
    assert "99%" not in str(response)
    assert "private reasoning" not in str(response)
    assert response["result"] is not None


def test_same_agent_gets_one_bounded_verification_turn_after_edit(plan, monkeypatch):
    calls = []

    async def fetch(*args):
        return weather_for(plan)

    class EditThenVerifyAgent:
        def __init__(self, session):
            self.session = session

        async def invoke_async(self, prompt, **kwargs):
            calls.append(kwargs["limits"]["turns"])
            if len(calls) == 1:
                self.session.inspect_plan()
                self.session.propose_changes({"shiftStart": "09:00"})
            else:
                await self.session.optimize_plan()
            return SimpleNamespace(stop_reason="end_turn")

    monkeypatch.setattr(agent_module, "get_weather", fetch)
    monkeypatch.setattr(agent_module, "_make_model", lambda *args: object())
    monkeypatch.setattr(agent_module, "_build_agent", lambda session, model: EditThenVerifyAgent(session))
    result = asyncio.run(run_agent("Set the paid shift start to09:00.", plan))
    assert calls == [6, 1]
    assert result["result"]["request"]["shiftStart"] == "09:00"
    assert result["requiresApproval"] is True


def test_model_failure_is_unavailable_without_leaking_exception(plan, monkeypatch):
    def fail(*args):
        raise RuntimeError("secret-token and account-specific provider body")

    monkeypatch.setattr(agent_module, "_make_model", fail)
    with pytest.raises(AgentUnavailable) as error:
        asyncio.run(run_agent("Find a cooler plan.", plan))
    assert "secret-token" not in str(error.value)
    assert "No changes were applied" in str(error.value)


def test_no_tool_execution_is_not_faked_as_success(plan, monkeypatch):
    class NoToolAgent:
        async def invoke_async(self, *args, **kwargs):
            return SimpleNamespace(stop_reason="end_turn")

    monkeypatch.setattr(agent_module, "_make_model", lambda *args: object())
    monkeypatch.setattr(agent_module, "_build_agent", lambda *args: NoToolAgent())
    with pytest.raises(AgentUnavailable, match="without executing"):
        asyncio.run(run_agent("Find a cooler plan.", plan))


def test_skipped_requested_edit_cannot_return_old_plan_success(plan, monkeypatch):
    class WrongOrderAgent:
        def __init__(self, session):
            self.session = session

        async def invoke_async(self, *args, **kwargs):
            self.session.inspect_plan()
            try:
                await self.session.optimize_plan()
            except ValueError:
                pass  # Strands converts tool validation errors to a tool response.
            return SimpleNamespace(stop_reason="end_turn")

    monkeypatch.setattr(agent_module, "_make_model", lambda *args: object())
    monkeypatch.setattr(agent_module, "_build_agent", lambda session, model: WrongOrderAgent(session))
    result = asyncio.run(run_agent("Set the paid shift start to09:00.", plan))
    assert result["requiresApproval"] is False
    assert result["proposedPlan"] is None
    assert result["result"] is None
    assert "shiftStart must be 09:00" in result["message"]


def test_ambiguous_shift_edit_asks_for_exact_time_without_optimization(plan):
    session = PlanningSession(plan, "Set the paid shift start earlier.")
    with pytest.raises(ValueError, match="exact paid shift start"):
        asyncio.run(session.optimize_plan())
    assert session.result is None


def test_tool_budget_is_bounded(plan):
    session = PlanningSession(plan, "Inspect the plan.")
    for _ in range(10):
        session.inspect_plan()
    with pytest.raises(ValueError, match="10-tool-call limit"):
        session.inspect_plan()


def test_failure_diagnostics_only_log_classes_and_allowlisted_codes(caplog):
    from botocore.exceptions import ClientError

    secret = "SENSITIVE_TEST_PROMPT_AND_TOKEN"
    inner = ClientError({
        "Error": {"Code": "ValidationException", "Message": secret},
        "ResponseMetadata": {"RequestId": secret, "HTTPHeaders": {"authorization": secret}},
    }, "ConverseStream")
    outer = RuntimeError(secret)
    outer.__cause__ = inner
    details = agent_module._safe_failure_details(outer, "bedrock", "model_invocation")
    assert details["exceptionClasses"] == ["RuntimeError", "ClientError"]
    assert details["awsErrorCodes"] == ["ValidationException"]
    assert secret not in str(details)
    with caplog.at_level("WARNING", logger="backend.agent"):
        agent_module._log_agent_failure(outer, "bedrock", "model_invocation")
    assert "ValidationException" in caplog.text
    assert secret not in caplog.text
    assert not any(record.exc_info for record in caplog.records)


def test_unknown_diagnostic_code_and_exception_cycle_are_bounded():
    from botocore.exceptions import ClientError

    error = ClientError({"Error": {"Code": "UNTRUSTED_BODY_VALUE", "Message": "private"}}, "ConverseStream")
    error.__cause__ = error
    details = agent_module._safe_failure_details(error, "untrusted-provider", "untrusted-stage")
    assert details["exceptionClasses"] == ["ClientError"]
    assert details["awsErrorCodes"] == []
    assert details["provider"] == "unknown"
    assert details["stage"] == "unknown"
    assert "UNTRUSTED_BODY_VALUE" not in str(details)


def test_actual_sdk_parser_warning_is_suppressed_but_safe_diagnostics_remain(caplog, monkeypatch):
    import io
    import logging
    from botocore.exceptions import ClientError
    from strands.event_loop.streaming import handle_content_block_stop

    secret = "PRIVATE_TOOL_INPUT_SENTINEL"
    sdk_output = io.StringIO()
    sdk_logger = logging.getLogger("strands.event_loop.streaming")
    # An explicit child handler bypasses a parent-only NullHandler policy.
    monkeypatch.setattr(sdk_logger, "handlers", [logging.StreamHandler(sdk_output)])
    monkeypatch.setattr(sdk_logger, "disabled", False)
    monkeypatch.setattr(sdk_logger, "propagate", True)
    monkeypatch.setattr(sdk_logger, "level", logging.WARNING)
    agent_module._suppress_strands_diagnostics()

    state = {
        "content": [],
        "current_tool_use": {
            "name": "propose_plan", "toolUseId": "offline-regression",
            "input": '{"changes": ' + secret,  # Deliberately malformed JSON.
        },
        "text": "", "reasoningText": "", "citationsContent": [],
    }
    result = handle_content_block_stop(state)  # Real installed SDK; no model call.
    assert result["content"][0]["toolUse"]["input"] == {}
    assert sdk_output.getvalue() == ""
    assert secret not in caplog.text

    error = ClientError({"Error": {"Code": "ValidationException", "Message": secret}}, "ConverseStream")
    with caplog.at_level("WARNING", logger="backend.agent"):
        agent_module._log_agent_failure(error, "bedrock", "model_invocation")
        logging.getLogger("heatshift.review").warning("Unrelated application logging still works")
    assert "ValidationException" in caplog.text
    assert "Unrelated application logging still works" in caplog.text
    assert secret not in caplog.text
    assert not any(record.exc_info for record in caplog.records)


def test_later_sdk_child_with_default_level_cannot_reach_its_handler(monkeypatch):
    import io
    import logging

    agent_module._suppress_strands_diagnostics()
    sdk_logger = logging.getLogger("strands.offline_later_import_regression")
    output = io.StringIO()
    monkeypatch.setattr(sdk_logger, "handlers", [logging.StreamHandler(output)])
    monkeypatch.setattr(sdk_logger, "disabled", False)
    monkeypatch.setattr(sdk_logger, "propagate", True)
    monkeypatch.setattr(sdk_logger, "level", logging.NOTSET)
    sdk_logger.error("PRIVATE_LATER_SDK_SENTINEL", exc_info=True)
    assert output.getvalue() == ""


def test_disabled_bedrock_health_overrides_cached_ready_without_credentials(monkeypatch):
    reason = "AWS is currently rejecting model requests for this account. Hosted AI planning is temporarily unavailable; the schedule planner remains available."
    monkeypatch.setenv("HEATSHIFT_AGENT_PROVIDER", "bedrock")
    monkeypatch.setenv("HEATSHIFT_AGENT_DISABLED_REASON", reason)
    configuration = agent_module._configuration()
    monkeypatch.setattr(agent_module, "_STATUS_CACHE", (
        agent_module.time.monotonic(), configuration,
        {"available": True, "provider": "bedrock", "model": configuration[1]},
    ))

    def forbidden(*args, **kwargs):
        raise AssertionError("Disabled health must not resolve credentials")

    monkeypatch.setattr("boto3.Session", forbidden)
    status = agent_module.get_agent_status()
    assert status["available"] is False
    assert status["reason"] == reason


def test_disabled_bedrock_rejects_before_model_construction(plan, monkeypatch):
    reason = "Hosted AI is temporarily unavailable; use the schedule planner."
    monkeypatch.setenv("HEATSHIFT_AGENT_PROVIDER", "bedrock")
    monkeypatch.setenv("HEATSHIFT_AGENT_DISABLED_REASON", reason)

    def forbidden(*args, **kwargs):
        raise AssertionError("Disabled agent must not construct a model")

    monkeypatch.setattr(agent_module, "_make_model", forbidden)
    with pytest.raises(AgentUnavailable) as error:
        asyncio.run(run_agent("Find a cooler plan.", plan))
    assert str(error.value) == reason


@pytest.mark.parametrize("provider,reason", [("ollama", "Cloud is blocked."), ("bedrock", ""), ("bedrock", "   ")])
def test_availability_override_is_cloud_only_and_empty_by_default(provider, reason, monkeypatch):
    monkeypatch.setenv("HEATSHIFT_AGENT_PROVIDER", provider)
    monkeypatch.setenv("HEATSHIFT_AGENT_DISABLED_REASON", reason)
    assert agent_module.get_agent_disabled_reason() is None
