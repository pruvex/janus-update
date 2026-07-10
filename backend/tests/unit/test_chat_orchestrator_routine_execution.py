from types import SimpleNamespace

import pytest

from backend.data import schemas
from backend.services.chat_orchestrator import ChatOrchestrator, RequestContext


class _RoutineResult:
    def __init__(self, *, found: bool, response_text: str, matched_trigger: str = "semantic:test") -> None:
        self.found = found
        self.response_text = response_text
        self.matched_trigger = matched_trigger
        self.routine_name = "Routine List Events"
        self.status = "ok"


@pytest.mark.asyncio
async def test_try_routine_execution_sets_final_text_for_finalize_path(monkeypatch):
    orchestrator = ChatOrchestrator.__new__(ChatOrchestrator)
    orchestrator.db = object()

    class _ExecutorStub:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

    class _RunnerStub:
        def __init__(self, _db, _executor) -> None:
            pass

        async def execute_by_trigger(self, _user_text, **_kwargs):
            return _RoutineResult(
                found=True,
                response_text="Ich habe deine passende gespeicherte Routine genutzt.\nRoutine erfolgreich ausgefuehrt.",
            )

    monkeypatch.setattr("backend.services.chat_orchestrator.ToolExecutor", _ExecutorStub)
    monkeypatch.setattr("backend.services.chat_orchestrator.RoutineRunner", _RunnerStub)

    ctx = RequestContext(
        request=schemas.ChatRequest(
            prompt="Was steht heute in meinem Kalender und wie wird das Wetter in Koeln?",
            provider="openai",
            model="gpt-5.4-nano",
            chat_id=1,
        ),
    )
    ctx.workflow = SimpleNamespace(
        user_text="Was steht heute in meinem Kalender und wie wird das Wetter in Koeln?",
        skip_llm_generation=False,
        help_intent_type=None,
        has_image=False,
        is_policy_response=False,
        is_policy_question=False,
        is_waiting_for_consent=False,
        api_key=None,
        selected=[],
        final_text="",
        final_text_to_generate="",
        use_agent_factory=True,
    )

    result = await ChatOrchestrator._try_routine_execution(orchestrator, ctx)

    assert result.workflow.skip_llm_generation is True
    assert result.workflow.use_agent_factory is False
    assert result.workflow.final_text == result.workflow.final_text_to_generate
    assert "passende gespeicherte Routine" in result.workflow.final_text


@pytest.mark.asyncio
async def test_try_routine_execution_leaves_context_unchanged_when_no_routine(monkeypatch):
    orchestrator = ChatOrchestrator.__new__(ChatOrchestrator)
    orchestrator.db = object()

    class _ExecutorStub:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

    class _RunnerStub:
        def __init__(self, _db, _executor) -> None:
            pass

        async def execute_by_trigger(self, _user_text, **_kwargs):
            return _RoutineResult(found=False, response_text="")

    monkeypatch.setattr("backend.services.chat_orchestrator.ToolExecutor", _ExecutorStub)
    monkeypatch.setattr("backend.services.chat_orchestrator.RoutineRunner", _RunnerStub)

    ctx = RequestContext(
        request=schemas.ChatRequest(
            prompt="Wie wird das Wetter in Berlin?",
            provider="gemini",
            model="gemini-3-flash-preview",
            chat_id=2,
        ),
    )
    ctx.workflow = SimpleNamespace(
        user_text="Wie wird das Wetter in Berlin?",
        skip_llm_generation=False,
        help_intent_type=None,
        has_image=False,
        is_policy_response=False,
        is_policy_question=False,
        is_waiting_for_consent=False,
        api_key=None,
        selected=[],
        final_text="",
        final_text_to_generate="",
        use_agent_factory=True,
    )

    result = await ChatOrchestrator._try_routine_execution(orchestrator, ctx)

    assert result.workflow.skip_llm_generation is False
    assert result.workflow.use_agent_factory is True
    assert result.workflow.final_text == ""
    assert result.workflow.final_text_to_generate == ""


@pytest.mark.asyncio
async def test_try_routine_execution_sets_final_text_for_calendar_routing_semantic_match(monkeypatch):
    orchestrator = ChatOrchestrator.__new__(ChatOrchestrator)
    orchestrator.db = object()

    class _ExecutorStub:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

    class _RunnerStub:
        def __init__(self, _db, _executor) -> None:
            pass

        async def execute_by_trigger(self, _user_text, **_kwargs):
            return _RoutineResult(
                found=True,
                response_text=(
                    "Ich habe deine passende gespeicherte Routine genutzt.\n\n"
                    "Keine Termine im angegebenen Zeitraum gefunden.\n\n"
                    "Die Entfernung von Berlin nach Hamburg betraegt etwa 290 Kilometer."
                ),
                matched_trigger="semantic:calendar.list_events,system.routing",
            )

    monkeypatch.setattr("backend.services.chat_orchestrator.ToolExecutor", _ExecutorStub)
    monkeypatch.setattr("backend.services.chat_orchestrator.RoutineRunner", _RunnerStub)

    ctx = RequestContext(
        request=schemas.ChatRequest(
            prompt="Welche Termine habe ich heute und wie weit ist es von Berlin nach Hamburg?",
            provider="openai",
            model="gpt-5.4-nano",
            chat_id=3,
        ),
    )
    ctx.workflow = SimpleNamespace(
        user_text="Welche Termine habe ich heute und wie weit ist es von Berlin nach Hamburg?",
        skip_llm_generation=False,
        help_intent_type=None,
        has_image=False,
        is_policy_response=False,
        is_policy_question=False,
        is_waiting_for_consent=False,
        api_key=None,
        selected=[],
        final_text="",
        final_text_to_generate="",
        use_agent_factory=True,
    )

    result = await ChatOrchestrator._try_routine_execution(orchestrator, ctx)

    assert result.workflow.skip_llm_generation is True
    assert result.workflow.use_agent_factory is False
    assert "passende gespeicherte Routine" in result.workflow.final_text
    assert "Berlin nach Hamburg" in result.workflow.final_text
