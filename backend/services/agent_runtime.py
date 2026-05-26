import logging
import uuid
from typing import Any, Dict, List, Optional

from backend.data.schemas import AgentSpec
from backend.services import llm_gateway
from backend.services.tool_executor import ToolExecutor

logger = logging.getLogger("janus_backend")


class AgentRuntime:
    """Executes a planned AgentSpec in a restricted runtime."""

    def __init__(self, db: Any, context_manager: Any):
        self.db = db
        self.context_manager = context_manager

    async def run(
        self,
        *,
        spec: AgentSpec,
        user_prompt: str,
        original_user_text: Optional[str] = None,
        provider: str,
        model: str,
        api_key: str,
        chat_id: Optional[int],
        skip_final_synthesis: bool = False,
    ) -> Dict[str, Any]:
        system_prompt = self._build_runtime_prompt(spec)
        history: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        requested_skills = [str(skill).strip() for skill in (spec.required_skills or []) if str(skill).strip()]
        task_queue = list(requested_skills)
        phase_trace_ids: List[str] = []
        phase_outputs: List[str] = []
        response: Dict[str, Any] = {}

        if requested_skills:
            for idx, skill_id in enumerate(requested_skills, start=1):
                skill_label = self._skill_label(skill_id)
                phase_max_tool_rounds = 2 if str(provider or "").lower() == "ollama" else 1
                phase_user_prompt = (
                    f"{user_prompt}\n\n"
                    "TASK_COMPLETE-VERTRAG: Markiere abgeschlossene Schritte intern als TASK_COMPLETE, "
                    "bevor du zur naechsten Phase gehst."
                )
                logger.info(
                    "TASK-QUEUE Phase %s/%s geplant: %s",
                    idx,
                    len(task_queue),
                    skill_label,
                )
                phase_trace_id = str(uuid.uuid4())
                phase_trace_ids.append(phase_trace_id)
                executor = ToolExecutor(
                    db=self.db,
                    api_key=api_key,
                    provider=provider,
                    model=model,
                    additional_context={
                        "chat_id": chat_id,
                        "trace_id": phase_trace_id,
                        "allowed_skill_ids": [skill_id],
                        "original_user_text": original_user_text or user_prompt,
                        "provider": provider,
                        "model": model,
                    },
                )
                response = await llm_gateway.reason_and_respond(
                    provider=provider,
                    model=model,
                    api_key=api_key,
                    chat_history=history,
                    context_manager=self.context_manager,
                    db=self.db,
                    user_prompt=phase_user_prompt,
                    chat_id=chat_id or 0,
                    tool_executor=executor,
                    disable_tools=False,
                    allowed_skill_ids=[skill_id],
                    max_tool_rounds=phase_max_tool_rounds,
                )
                phase_text = self._extract_text(response)
                logger.info("TASK-QUEUE Phase %s ausgefuehrt: %s", idx, skill_label)
                logger.info("TASK-QUEUE Phase %s TASK_COMPLETE: %s", idx, skill_label)
                if phase_text and not self._is_generic_completion_text(phase_text):
                    phase_line = f"[{skill_id}] {phase_text}"
                    phase_outputs.append(phase_line)
                    history.append({"role": "assistant", "content": phase_line})

            if not skip_final_synthesis:
                final_trace_id = str(uuid.uuid4())
                phase_trace_ids.append(final_trace_id)
                synthesis_executor = ToolExecutor(
                    db=self.db,
                    api_key=api_key,
                    provider=provider,
                    model=model,
                    additional_context={
                        "chat_id": chat_id,
                        "trace_id": final_trace_id,
                        "allowed_skill_ids": requested_skills,
                        "original_user_text": original_user_text or user_prompt,
                        "provider": provider,
                        "model": model,
                    },
                )
                logger.info("TASK-QUEUE: Finale Synthese startet nach %s abgeschlossenen Aufgaben.", len(task_queue))
                response = await self._synthesize_final_response(
                    history=history,
                    user_prompt=user_prompt,
                    provider=provider,
                    model=model,
                    api_key=api_key,
                    chat_id=chat_id,
                    synthesis_executor=synthesis_executor,
                    allowed_skill_ids=requested_skills,
                )
        else:
            trace_id = str(uuid.uuid4())
            phase_trace_ids.append(trace_id)
            executor = ToolExecutor(
                db=self.db,
                api_key=api_key,
                provider=provider,
                model=model,
                additional_context={
                    "chat_id": chat_id,
                    "trace_id": trace_id,
                    "allowed_skill_ids": [],
                    "original_user_text": original_user_text or user_prompt,
                    "provider": provider,
                    "model": model,
                },
            )
            response = await llm_gateway.reason_and_respond(
                provider=provider,
                model=model,
                api_key=api_key,
                chat_history=history,
                context_manager=self.context_manager,
                db=self.db,
                user_prompt=user_prompt,
                chat_id=chat_id or 0,
                tool_executor=executor,
                disable_tools=False,
                allowed_skill_ids=[],
                max_tool_rounds=max(1, int(spec.max_iterations)),
            )

        final_text = self._extract_text(response)
        if phase_outputs and self._is_generic_completion_text(final_text):
            final_text = self._build_phase_summary(phase_outputs)
        return {
            "text": final_text,
            "trace_id": phase_trace_ids[0],
            "trace_ids": phase_trace_ids,
            "task_queue": task_queue,
            "phase_outputs": phase_outputs,
            "agent_spec": spec.model_dump(),
            "raw_response": response,
        }

    @staticmethod
    def _skill_label(skill_id: str) -> str:
        mapping = {
            "system.country_info": "Country Info",
            "system.routing": "Routing",
        }
        return mapping.get(str(skill_id or "").strip(), str(skill_id or "").strip())

    def _build_runtime_prompt(self, spec: AgentSpec) -> str:
        allowed = ", ".join(spec.required_skills) if spec.required_skills else "(keine)"
        return (
            f"Du bist der Spezial-Agent '{spec.name}'.\n"
            f"Du hast eine Task-Queue mit folgenden Aufgaben: {allowed}\n"
            f"Ziel: {spec.goal}\n"
            f"Regeln: {spec.instructions}\n"
            f"Erlaubte Skills: {allowed}\n"
            "Nutze ausschließlich die erlaubten Skills."
        )

    async def _synthesize_final_response(
        self,
        *,
        history: List[Dict[str, Any]],
        user_prompt: str,
        provider: str,
        model: str,
        api_key: str,
        chat_id: Optional[int],
        synthesis_executor: ToolExecutor,
        allowed_skill_ids: List[str],
    ) -> Dict[str, Any]:
        synthesis_history = [dict(item) for item in (history or []) if isinstance(item, dict)]
        system_prompt = ""
        if synthesis_history and str(synthesis_history[0].get("role") or "") == "system":
            system_prompt = str(synthesis_history[0].get("content") or "")
            provider_name = str(provider or "").strip().lower()
            if provider_name == "ollama":
                format_rules = (
                    "\n\n🚨 FORMATIERUNGS-REGELN FÜR LOKALE ORTE:\n"
                    "Nutze für jeden präsentierten Ort ZWINGEND dieses Markdown-Format:\n\n"
                    "### 🍽️ [Name des Ortes]\n"
                    "- 📍 **Adresse:** [Adresse]\n"
                    "WICHTIG: Die folgenden Zeilen NUR anzeigen, wenn Daten vorhanden sind! Fehlen Daten, lass die Zeile komplett weg!\n"
                    "- � **Öffnungszeiten:** [Zeiten]\n"
                    "- 📞 **Telefon:** [Nummer]\n"
                    "- 🌐 **Info:** [Klickbarer Link, falls vorhanden. Z.B. Google Maps oder Website]\n\n"
                    "REGELN:\n"
                    "1. Erfinde NIEMALS Daten. Fehlt eine Website oder Telefonnummer in den dir übergebenen Daten, lass den Punkt stillschweigend weg.\n"
                    "2. Übersetze rohe englische Tags (wie 'italian' oder 'opening_hours') in fließendes Deutsch.\n"
                    "3. Sei freundlich und übersichtlich."
                )
                if isinstance(system_prompt, str):
                    system_prompt += format_rules
                    synthesis_history[0] = {"role": "system", "content": system_prompt}
        return await llm_gateway.reason_and_respond(
            provider=provider,
            model=model,
            api_key=api_key,
            chat_history=synthesis_history,
            context_manager=self.context_manager,
            db=self.db,
            user_prompt=user_prompt,
            chat_id=chat_id or 0,
            tool_executor=synthesis_executor,
            disable_tools=True,
            allowed_skill_ids=allowed_skill_ids,
            max_tool_rounds=1,
        )

    def _extract_text(self, response: Any) -> str:
        if isinstance(response, dict):
            text = response.get("text")
            if isinstance(text, str) and text.strip():
                return text
            raw = response.get("raw_assistant_response") or response.get("message")
            if isinstance(raw, dict):
                content = raw.get("content")
                if isinstance(content, str) and content.strip():
                    return content
            if isinstance(raw, str) and raw.strip():
                return raw
        if isinstance(response, str):
            return response
        return "Ich habe die Agenten-Ausführung abgeschlossen."

    @staticmethod
    def _is_generic_completion_text(text: str) -> bool:
        normalized = str(text or "").strip().lower()
        if not normalized:
            return True
        generic_markers = {
            "ich habe die agenten-ausführung abgeschlossen.",
            "ich habe die agenten-ausfuehrung abgeschlossen.",
            "agent-ausführung abgeschlossen.",
            "agent-ausfuehrung abgeschlossen.",
        }
        return normalized in generic_markers

    @staticmethod
    def _build_phase_summary(phase_outputs: List[str]) -> str:
        cleaned = [str(item or "").strip() for item in (phase_outputs or []) if str(item or "").strip()]
        if not cleaned:
            return "Ich habe die Agenten-Ausführung abgeschlossen."
        return "\n".join(cleaned)
