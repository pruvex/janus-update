import pytest

from backend.services.skill_router import SkillNotFoundError
from backend.services.tool_executor import ToolExecutor
from backend.services.tool_manager import ToolManager


async def _dummy_tool():
    return {"status": "ok"}


def test_tool_manager_resolves_dot_underscore_and_domain_legacy_aliases():
    manager = ToolManager()
    manager.register_tool(_dummy_tool, name="create_calendar_event")

    assert manager.get_skill_id("create_calendar_event") == "calendar.create_event"
    assert manager.get_skill_id("calendar_create_event") == "calendar.create_event"
    assert manager.get_skill_id("calendar.create_calendar_event") == "calendar.create_event"

    assert manager.get_tool("calendar.create_event") is manager.get_tool("create_calendar_event")
    assert manager.get_tool("calendar_create_event") is manager.get_tool("create_calendar_event")
    assert manager.get_tool("calendar.create_calendar_event") is manager.get_tool("create_calendar_event")


def test_executor_resolve_tool_name_retries_dot_underscore_and_suffix(monkeypatch):
    executor = ToolExecutor.__new__(ToolExecutor)
    calls = []

    def _resolve(candidate):
        calls.append(candidate)
        if candidate == "create_calendar_event":
            return "calendar.create_event"
        raise SkillNotFoundError(candidate)

    monkeypatch.setattr("backend.services.tool_executor.skill_router.resolve_tool_name", _resolve)

    assert executor._resolve_tool_name_with_alternates("calendar.create_calendar_event") == "calendar.create_event"
    assert "calendar.create_calendar_event" in calls
    assert "create_calendar_event" in calls


def test_executor_resolve_tool_name_raises_after_all_aliases(monkeypatch):
    executor = ToolExecutor.__new__(ToolExecutor)

    def _resolve(candidate):
        raise SkillNotFoundError(candidate)

    monkeypatch.setattr("backend.services.tool_executor.skill_router.resolve_tool_name", _resolve)

    with pytest.raises(SkillNotFoundError):
        executor._resolve_tool_name_with_alternates("missing.tool")
