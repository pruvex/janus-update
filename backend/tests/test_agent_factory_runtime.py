import json

import pytest

from backend.data.models import SkillTelemetry
from backend.data.schemas import PlannerContext, PlannerProviderProfile
from backend.services.agent_planner import AgentPlanner
from backend.services.agent_runtime import AgentRuntime
from backend.services.orchestrator.intent_engine import IntentDetectionResult


def _planner_profile(provider="openai", model="gpt-5.4-nano"):
    return PlannerProviderProfile(
        provider=provider,
        requested_model=model,
        planner_model=model,
        model_class="nano" if "nano" in model else "standard",
        max_iterations_cap=8,
    )


def _planner_context(allowed=None, forbidden=None, negative=None, required=None):
    return PlannerContext(
        allowed_skill_ids=list(allowed or []),
        required_skill_ids=list(required or []),
        forbidden_skill_ids=list(forbidden or []),
        negative_constraints=list(negative or []),
    )


@pytest.mark.asyncio
async def test_agent_planner_builds_specialist_spec(monkeypatch):
    planner = AgentPlanner()

    async def _fake_generate(**_kwargs):
        return {
            "text": json.dumps(
                {
                    "name": "PDF-Forensiker",
                    "goal": "Dokumente nach Kairo durchsuchen und Zusammenfassung schreiben",
                    "required_skills": ["knowledge.query", "filesystem.create_file"],
                    "instructions": "Suche zuerst, schreibe dann Datei.",
                    "max_iterations": 4,
                },
                ensure_ascii=False,
            )
        }

    monkeypatch.setattr("backend.services.agent_planner.llm_gateway.simple_llm_generate_content", _fake_generate)

    spec = await planner.plan(
        user_prompt="Durchsuche meine Dokumente nach Kairo und erstelle eine Zusammenfassung als neue Textdatei.",
        intent_result=IntentDetectionResult(primary_intent="complex_document"),
        planner_context=_planner_context(["knowledge.query", "filesystem.create_file"]),
        provider_profile=_planner_profile(),
        capability_groups={
            "document_analysis": ["knowledge.query"],
            "file_write": ["filesystem.create_file"],
        },
        provider="openai",
        model="gpt-5.4-nano",
        api_key="dummy",
    )

    assert spec.name == "PDF-Forensiker"
    assert spec.required_skills == ["knowledge.query", "filesystem.create_file"]
    assert spec.max_iterations == 4


@pytest.mark.asyncio
async def test_agent_planner_normalizes_llm_plan_and_injects_required_routing_country_skills(monkeypatch):
    planner = AgentPlanner()

    async def _fake_generate(**_kwargs):
        return {
            "text": json.dumps(
                {
                    "name": "Travel Agent",
                    "goal": "Reiseplanung",
                    "required_skills": [
                        "system.country_info",
                        "system.country_info",
                        "system.routing",
                        "system.websearch",
                    ],
                    "instructions": "Nutze alle Skills",
                    "max_iterations": 12,
                },
                ensure_ascii=False,
            )
        }

    monkeypatch.setattr("backend.services.agent_planner.llm_gateway.simple_llm_generate_content", _fake_generate)

    spec = await planner.plan(
        user_prompt="Wie viele Einwohner hat Japan und wie weit ist es von Tokio nach Kyoto?",
        intent_result=IntentDetectionResult(),
        planner_context=_planner_context(["system.country_info", "system.routing"]),
        provider_profile=_planner_profile(provider="gemini", model="gemini-3-flash-preview"),
        capability_groups={
            "geo": ["system.country_info", "system.routing"],
        },
        provider="gemini",
        model="gemini-3-flash-preview",
        api_key="dummy",
    )

    assert spec.required_skills == ["system.country_info", "system.routing"]
    assert spec.max_iterations == 8


@pytest.mark.asyncio
async def test_agent_planner_sanitizes_list_strings_and_required_skills_string(monkeypatch):
    planner = AgentPlanner()

    async def _fake_generate(**_kwargs):
        return {
            "text": json.dumps(
                {
                    "name": "Local Planner",
                    "goal": ["Schweden PDF erstellen"],
                    "required_skills": "system.routing",
                    "instructions": ["Ermittle Distanz", "Erstelle dann PDF"],
                    "max_iterations": 3,
                },
                ensure_ascii=False,
            )
        }

    monkeypatch.setattr("backend.services.agent_planner.llm_gateway.simple_llm_generate_content", _fake_generate)

    spec = await planner.plan(
        user_prompt="Wie weit ist es von Berlin nach Stockholm?",
        intent_result=IntentDetectionResult(),
        planner_context=_planner_context(["system.routing", "system.country_info"]),
        provider_profile=_planner_profile(provider="ollama", model="gemma2:27b"),
        capability_groups={
            "geo": ["system.routing", "system.country_info"],
        },
        provider="ollama",
        model="gemma2:27b",
        api_key="dummy",
    )

    assert spec.required_skills == ["system.routing"]
    assert spec.instructions == "Ermittle Distanz Erstelle dann PDF"
    assert spec.goal == "Schweden PDF erstellen"


@pytest.mark.asyncio
async def test_agent_planner_heuristic_plan_selects_country_and_routing_for_travel_prompt(monkeypatch):
    planner = AgentPlanner()

    async def _raise_generate(**_kwargs):
        raise RuntimeError("planner unavailable")

    monkeypatch.setattr("backend.services.agent_planner.llm_gateway.simple_llm_generate_content", _raise_generate)

    spec = await planner.plan(
        user_prompt="Berechne Distanz und Fahrzeit von Tokio nach Kyoto und nenne die Einwohner von Japan.",
        intent_result=IntentDetectionResult(),
        planner_context=_planner_context(["system.country_info", "system.routing", "knowledge.query"]),
        provider_profile=_planner_profile(),
        capability_groups={
            "geo": ["system.country_info", "system.routing"],
            "knowledge": ["knowledge.query"],
        },
        provider="openai",
        model="gpt-5.4-nano",
        api_key="dummy",
    )

    assert "system.routing" in spec.required_skills
    assert "system.country_info" in spec.required_skills


@pytest.mark.asyncio
async def test_agent_planner_pdf_single_goal_keeps_only_create_pdf(monkeypatch):
    planner = AgentPlanner()

    async def _fake_generate(**_kwargs):
        return {
            "text": json.dumps(
                {
                    "name": "Dokumenten-Agent",
                    "goal": "PDF erzeugen",
                    "required_skills": [
                        "create_pdf",
                        "knowledge.open_document",
                        "knowledge.edit_pdf",
                        "read_full_text",
                    ],
                    "instructions": "Erstellen, dann lesen und bearbeiten.",
                    "max_iterations": 5,
                },
                ensure_ascii=False,
            )
        }

    monkeypatch.setattr("backend.services.agent_planner.llm_gateway.simple_llm_generate_content", _fake_generate)

    spec = await planner.plan(
        user_prompt="Erstelle eine PDF 'Reise.pdf' mit Inhalt 'Hallo'.",
        intent_result=IntentDetectionResult(),
        planner_context=_planner_context(
            ["create_pdf", "knowledge.open_document", "knowledge.edit_pdf", "read_full_text"],
            required=["create_pdf"],
        ),
        provider_profile=_planner_profile(),
        capability_groups={
            "pdf": ["create_pdf", "knowledge.open_document", "knowledge.edit_pdf", "read_full_text"],
        },
        provider="openai",
        model="gpt-5.4-nano",
        api_key="dummy",
    )

    assert spec.required_skills == ["create_pdf"]
    assert spec.max_iterations == 1


@pytest.mark.asyncio
async def test_agent_planner_lockdown_prompt_returns_empty_required_skills(monkeypatch):
    planner = AgentPlanner()

    async def _fake_generate(**_kwargs):
        raise AssertionError("LLM darf im Lockdown-Mode nicht aufgerufen werden")

    monkeypatch.setattr("backend.services.agent_planner.llm_gateway.simple_llm_generate_content", _fake_generate)

    spec = await planner.plan(
        user_prompt="LOCKDOWN_MODE: CREATE_PDF_DONE\nRegel: Keine weiteren Tools planen.",
        intent_result=IntentDetectionResult(),
        planner_context=_planner_context(["create_pdf", "knowledge.open_document"]),
        provider_profile=_planner_profile(),
        capability_groups={"pdf": ["create_pdf", "knowledge.open_document"]},
        provider="openai",
        model="gpt-5.4-nano",
        api_key="dummy",
    )

    assert spec.required_skills == []
    assert spec.max_iterations == 1


@pytest.mark.asyncio
async def test_agent_planner_calendar_intent_forbids_pdf_and_skips_llm(monkeypatch):
    planner = AgentPlanner()

    async def _fake_generate(**_kwargs):
        raise AssertionError("LLM darf bei eindeutigem Kalender-Intent nicht aufgerufen werden")

    monkeypatch.setattr("backend.services.agent_planner.llm_gateway.simple_llm_generate_content", _fake_generate)

    spec = await planner.plan(
        user_prompt="Welche Termine habe ich nächsten Mittwoch?",
        intent_result=IntentDetectionResult(is_calendar_intent=True, primary_intent="calendar"),
        planner_context=_planner_context(
            ["calendar.list_events", "system.create_pdf"],
            forbidden=["system.create_pdf"],
            negative=["Kalender-Turn: PDF-Tools verboten."],
        ),
        provider_profile=_planner_profile(),
        capability_groups={
            "calendar": ["calendar.list_events"],
            "document_generation": ["system.create_pdf"],
        },
        provider="openai",
        model="gpt-5.4-nano",
        api_key="dummy",
    )

    assert spec.required_skills == ["calendar.list_events"]
    assert "system.create_pdf" not in spec.required_skills
    assert spec.max_iterations == 1


@pytest.mark.asyncio
async def test_agent_planner_shopping_intent_forces_price_comparison_without_llm(monkeypatch):
    planner = AgentPlanner()

    async def _fake_generate(**_kwargs):
        raise AssertionError("LLM darf bei eindeutigem Shopping-Intent nicht aufgerufen werden")

    monkeypatch.setattr("backend.services.agent_planner.llm_gateway.simple_llm_generate_content", _fake_generate)

    spec = await planner.plan(
        user_prompt="Was kostet die Apple Watch Ultra am günstigsten?",
        intent_result=IntentDetectionResult(is_shopping_intent=True, primary_intent="shopping"),
        planner_context=_planner_context(["system.price_comparison", "system.websearch"]),
        provider_profile=_planner_profile(),
        capability_groups={
            "shopping": ["system.price_comparison"],
            "web_research": ["system.websearch"],
        },
        provider="openai",
        model="gpt-5.4-nano",
        api_key="dummy",
    )

    assert spec.required_skills == ["system.price_comparison"]
    assert spec.max_iterations == 1


@pytest.mark.asyncio
async def test_agent_runtime_runs_required_skills_sequentially_one_skill_per_phase(db_session, monkeypatch):
    runtime = AgentRuntime(db_session, context_manager=None)

    async def _dummy_handler(**_kwargs):
        return {"result": "ok"}

    monkeypatch.setattr(
        "backend.services.tool_executor.skill_router.resolve_tool_name",
        lambda name: str(name),
    )
    monkeypatch.setattr(
        "backend.services.tool_executor.skill_router.get_tool_definition",
        lambda name: type("Def", (), {"name": str(name), "func": _dummy_handler, "args_schema": None})(),
    )
    monkeypatch.setattr(
        "backend.services.tool_executor.PolicyEngine.evaluate",
        lambda _tool_name, _db: "ALLOW",
    )

    calls = []
    phase_payloads = []

    async def _fake_reason_and_respond(**kwargs):
        phase_payloads.append(
            {
                "messages": list(kwargs.get("chat_history") or []),
                "user_prompt": str(kwargs.get("user_prompt") or ""),
            }
        )
        calls.append(
            {
                "allowed_skill_ids": list(kwargs.get("allowed_skill_ids") or []),
                "disable_tools": bool(kwargs.get("disable_tools")),
                "max_tool_rounds": kwargs.get("max_tool_rounds"),
            }
        )
        executor = kwargs["tool_executor"]
        allowed = list(kwargs.get("allowed_skill_ids") or [])
        if kwargs.get("disable_tools"):
            return {"text": "Agent abgeschlossen"}
        if "knowledge.query" in allowed:
            await executor.execute_tool_calls(
                [
                    {
                        "id": "tc-knowledge",
                        "function": {"name": "knowledge.query", "arguments": '{"query_text":"Kairo"}'},
                    }
                ]
            )
        if "filesystem.create_file" in allowed:
            await executor.execute_tool_calls(
                [
                    {
                        "id": "tc-create",
                        "function": {
                            "name": "filesystem.create_file",
                            "arguments": '{"path":"agent_summary.txt","content":"Kairo summary"}',
                        },
                    }
                ]
            )
        return {"text": "Agent abgeschlossen"}

    monkeypatch.setattr("backend.services.agent_runtime.llm_gateway.reason_and_respond", _fake_reason_and_respond)

    spec = type("Spec", (), {
        "name": "PDF-Forensiker",
        "goal": "Kairo zusammenfassen",
        "required_skills": ["knowledge.query", "filesystem.create_file"],
        "instructions": "Search then write.",
        "max_iterations": 5,
        "model_dump": lambda self: {
            "name": self.name,
            "goal": self.goal,
            "required_skills": self.required_skills,
            "instructions": self.instructions,
            "max_iterations": self.max_iterations,
        },
    })()

    result = await runtime.run(
        spec=spec,
        user_prompt="Durchsuche meine Dokumente nach Kairo und erstelle eine Zusammenfassung als neue Textdatei.",
        provider="openai",
        model="gpt-5.4-nano",
        api_key="dummy",
        chat_id=123,
    )

    assert result["text"] == "Agent abgeschlossen"
    assert len(calls) == 3
    assert calls[0]["allowed_skill_ids"] == ["knowledge.query"]
    assert calls[1]["allowed_skill_ids"] == ["filesystem.create_file"]
    assert calls[2]["allowed_skill_ids"] == ["knowledge.query", "filesystem.create_file"]
    assert calls[0]["disable_tools"] is False
    assert calls[1]["disable_tools"] is False
    assert calls[2]["disable_tools"] is True
    first_phase_messages = phase_payloads[0]["messages"]
    first_phase_system_messages = [
        msg for msg in first_phase_messages if isinstance(msg, dict) and msg.get("role") == "system"
    ]
    assert any(
        "Du hast eine Task-Queue mit folgenden Aufgaben" in str(msg.get("content") or "")
        for msg in first_phase_system_messages
    )
    assert "TASK_COMPLETE" in phase_payloads[0]["user_prompt"]
    telemetry_rows = (
        db_session.query(SkillTelemetry)
        .order_by(SkillTelemetry.id.desc())
        .limit(2)
        .all()
    )
    assert len(telemetry_rows) == 2
    assert len({row.trace_id for row in telemetry_rows}) == 2


@pytest.mark.asyncio
async def test_agent_runtime_e2e_style_japan_prompt_single_tool_per_turn_no_forcing_logs(db_session, monkeypatch, caplog):
    runtime = AgentRuntime(db_session, context_manager=None)

    async def _country_handler(**_kwargs):
        return {"status": "ok", "data": {"country": "Japan", "population": "124.5 Mio", "currency": "Yen"}}

    async def _routing_handler(**_kwargs):
        return {
            "status": "ok",
            "data": {
                "origin": "Tokio, Japan",
                "destination": "Kyoto, Japan",
                "distance_km": 454.8,
                "duration": "5 Std. 35 Min.",
            },
        }

    monkeypatch.setattr(
        "backend.services.tool_executor.skill_router.resolve_tool_name",
        lambda name: str(name),
    )
    monkeypatch.setattr(
        "backend.services.tool_executor.skill_router.get_tool_definition",
        lambda name: type(
            "Def",
            (),
            {
                "name": str(name),
                "func": _country_handler if str(name) == "system.country_info" else _routing_handler,
                "args_schema": None,
            },
        )(),
    )
    monkeypatch.setattr(
        "backend.services.tool_executor.PolicyEngine.evaluate",
        lambda _tool_name, _db: "ALLOW",
    )

    async def _fake_reason_and_respond(**kwargs):
        executor = kwargs["tool_executor"]
        allowed = list(kwargs.get("allowed_skill_ids") or [])
        if kwargs.get("disable_tools"):
            return {"text": "Synthese abgeschlossen"}
        tool_name = allowed[0]
        if tool_name == "system.country_info":
            await executor.execute_tool_calls(
                [
                    {
                        "id": "tc-country",
                        "function": {
                            "name": "system.country_info",
                            "arguments": '{"country":"Japan","language":"de"}',
                        },
                    }
                ]
            )
        elif tool_name == "system.routing":
            await executor.execute_tool_calls(
                [
                    {
                        "id": "tc-routing",
                        "function": {
                            "name": "system.routing",
                            "arguments": '{"origin":"Tokio, Japan","destination":"Kyoto, Japan","mode":"driving"}',
                        },
                    }
                ]
            )
        return {"text": "phase done"}

    monkeypatch.setattr("backend.services.agent_runtime.llm_gateway.reason_and_respond", _fake_reason_and_respond)

    spec = type("Spec", (), {
        "name": "Reise-Analyst",
        "goal": "Japan-Infos und Route",
        "required_skills": ["system.country_info", "system.routing"],
        "instructions": "Sequentiell arbeiten.",
        "max_iterations": 2,
        "model_dump": lambda self: {
            "name": self.name,
            "goal": self.goal,
            "required_skills": self.required_skills,
            "instructions": self.instructions,
            "max_iterations": self.max_iterations,
        },
    })()

    caplog.set_level("INFO", logger="janus_backend")
    result = await runtime.run(
        spec=spec,
        user_prompt="Ich plane eine Reise nach Japan. Einwohner/Währung? Distanz Tokio-Kyoto?",
        provider="gemini",
        model="gemini-3-flash-preview",
        api_key="dummy",
        chat_id=77,
    )

    assert result["text"] == "Synthese abgeschlossen"
    assert result.get("task_queue") == ["system.country_info", "system.routing"]
    log_text = "\n".join(record.getMessage() for record in caplog.records)
    assert "Forcing" not in log_text
    assert "Anzahl Tools=2" not in log_text
    assert "TASK-QUEUE Phase 1/2 geplant: Country Info" in log_text
    assert "TASK-QUEUE Phase 1 ausgefuehrt: Country Info" in log_text
    assert "TASK-QUEUE Phase 1 TASK_COMPLETE: Country Info" in log_text
    assert "TASK-QUEUE Phase 2/2 geplant: Routing" in log_text
    assert "TASK-QUEUE Phase 2 ausgefuehrt: Routing" in log_text
    assert "TASK-QUEUE Phase 2 TASK_COMPLETE: Routing" in log_text
    assert "TASK-QUEUE: Finale Synthese startet nach 2 abgeschlossenen Aufgaben." in log_text
    assert "Executing tool 'system.country_info'" in log_text
    assert "Executing tool 'system.routing'" in log_text
    assert log_text.index("Executing tool 'system.country_info'") < log_text.index("Executing tool 'system.routing'")


@pytest.mark.asyncio
async def test_agent_runtime_ollama_uses_two_tool_rounds_per_skill(db_session, monkeypatch):
    runtime = AgentRuntime(db_session, context_manager=None)
    captured_max_rounds = []

    async def _fake_reason_and_respond(**kwargs):
        captured_max_rounds.append(int(kwargs.get("max_tool_rounds") or 0))
        if kwargs.get("disable_tools"):
            return {"text": "Synthese abgeschlossen"}
        return {
            "text": "phase done",
            "raw_response": {"tool_calls": [{"id": "dummy"}]},
        }

    monkeypatch.setattr("backend.services.agent_runtime.llm_gateway.reason_and_respond", _fake_reason_and_respond)

    spec = type("Spec", (), {
        "name": "Reise-Analyst",
        "goal": "Japan-Infos und Route",
        "required_skills": ["system.country_info", "system.routing"],
        "instructions": "Sequentiell arbeiten.",
        "max_iterations": 2,
        "model_dump": lambda self: {
            "name": self.name,
            "goal": self.goal,
            "required_skills": self.required_skills,
            "instructions": self.instructions,
            "max_iterations": self.max_iterations,
        },
    })()

    result = await runtime.run(
        spec=spec,
        user_prompt="Japan facts + route",
        provider="ollama",
        model="gemma2:27b@test",
        api_key="dummy",
        chat_id=77,
    )

    assert result["text"] == "Synthese abgeschlossen"
    assert captured_max_rounds == [2, 2, 1]


@pytest.mark.asyncio
async def test_agent_runtime_uses_phase_summary_when_final_synthesis_is_generic(db_session, monkeypatch):
    runtime = AgentRuntime(db_session, context_manager=None)
    phase_counter = {"idx": 0}

    async def _fake_reason_and_respond(**kwargs):
        if kwargs.get("disable_tools"):
            return {"text": "Ich habe die Agenten-Ausführung abgeschlossen."}
        phase_counter["idx"] += 1
        if phase_counter["idx"] == 1:
            return {"text": "Japan: Hauptstadt Tokio, Einwohner 124.5 Mio."}
        return {"text": "Ich habe die Agenten-Ausführung abgeschlossen."}

    monkeypatch.setattr("backend.services.agent_runtime.llm_gateway.reason_and_respond", _fake_reason_and_respond)

    spec = type("Spec", (), {
        "name": "Reise-Analyst",
        "goal": "Japan-Infos und Route",
        "required_skills": ["system.country_info", "system.routing"],
        "instructions": "Sequentiell arbeiten.",
        "max_iterations": 2,
        "model_dump": lambda self: {
            "name": self.name,
            "goal": self.goal,
            "required_skills": self.required_skills,
            "instructions": self.instructions,
            "max_iterations": self.max_iterations,
        },
    })()

    result = await runtime.run(
        spec=spec,
        user_prompt="Reisefakten sammeln",
        provider="ollama",
        model="gemma2:27b@test",
        api_key="dummy",
        chat_id=42,
    )

    assert result["phase_outputs"] == ["[system.country_info] Japan: Hauptstadt Tokio, Einwohner 124.5 Mio."]
    assert result["text"] == "[system.country_info] Japan: Hauptstadt Tokio, Einwohner 124.5 Mio."
