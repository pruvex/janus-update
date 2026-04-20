"""Legacy serialization keys on ToolResultV1 (success, output)."""

from backend.data.schemas_tools import ToolResultV1


def test_tool_result_v1_model_dump_includes_legacy_keys():
    res = ToolResultV1(status="ok", message="Test")
    dumped = res.model_dump()
    assert dumped["success"] is True
    assert dumped["output"] == "Test"
    assert dumped["status"] == "ok"


def test_tool_result_v1_error_legacy_success_false():
    from backend.data.schemas_tools import ToolErrorDetails

    res = ToolResultV1(
        status="error",
        error=ToolErrorDetails(code="X", message="failed"),
    )
    dumped = res.model_dump()
    assert dumped["success"] is False
    assert dumped["output"] == ""


def test_tool_result_v1_strips_legacy_keys_on_validate():
    """Incoming dicts may carry old keys; they must not break parsing."""
    res = ToolResultV1.model_validate(
        {
            "status": "ok",
            "message": "Hi",
            "success": False,
            "output": "ignored",
        }
    )
    assert res.success is True
    assert res.output == "Hi"
