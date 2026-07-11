from backend.services.workflow.placeholder_resolver import (
    PlaceholderResolutionError,
    resolve_placeholder_value,
    resolve_routine_step_args,
)


def test_resolve_routine_step_args_resolves_nested_placeholder():
    resolved = resolve_routine_step_args(
        {
            "city": "{{user.city}}",
            "range": "today",
            "meta": {"label": "{{user.city}}"},
        },
        memory_context={"user": {"city": "Koeln"}},
    )

    assert resolved == {
        "city": "Koeln",
        "range": "today",
        "meta": {"label": "Koeln"},
    }


def test_resolve_routine_step_args_uses_arg_binding_fallback():
    resolved = resolve_routine_step_args(
        {"city": "{{user.city}}"},
        memory_context={"wohnort": "Berlin"},
        arg_bindings={"city": "memory:wohnort"},
    )

    assert resolved["city"] == "Berlin"


def test_resolve_placeholder_value_raises_for_missing_placeholder():
    try:
        resolve_placeholder_value("user.city", memory_context={})
    except PlaceholderResolutionError as exc:
        assert "user.city" in str(exc)
    else:
        raise AssertionError("expected PlaceholderResolutionError")
