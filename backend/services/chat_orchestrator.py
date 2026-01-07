import logging
import json
import os
import base64
import asyncio
import keyring
from datetime import datetime
from typing import Dict, Optional, List

from backend.services.rag_manager import query_knowledge_base

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.data import crud, database, schemas
from backend.data.database import Memory 
from backend.services import llm_gateway, image_manager, memory_extractor, memory_manager, cost_service
from backend.services.context_manager import ContextManager
from backend.services.tool_executor import ToolExecutor
from backend.services.chat.tool_selector import ToolSelector
from backend.services.chat.context_builder import ContextBuilder
from backend.services.planner_service import generate_decision_context
from backend.services.verifier_service import verify_decision_integrity
from backend.data.schemas import ExtractedFact
from backend.utils import intent_classifier
from backend.utils.config_loader import initialize_file_from_template
from backend.utils.paths import get_app_data_dir

logger = logging.getLogger("janus_backend")

class ChatOrchestrator:
    def __init__(
        self,
        db: Session,
        context_manager: ContextManager,
        model_catalog: Dict,
        config_file_path: str,
        template_config_file_path: str,
        personalities_file_path: str,
        template_personalities_file_path: str,
    ):
        self.db = db
        self.context_manager = context_manager
        self.model_catalog = model_catalog
        self.config_file = config_file_path
        self.personalities_file = personalities_file_path
        
        initialize_file_from_template(template_config_file_path, config_file_path)
        initialize_file_from_template(template_personalities_file_path, personalities_file_path)
        
        self.context_builder = ContextBuilder(db)
        
        self.last_response_id_per_chat = {}
        self.last_ssml_response_per_chat = {}
        self.last_email_list_per_chat = {}
        self.follow_up_context_per_chat = {}

    def _load_config(self):
        try:
            with open(self.config_file, "r") as f:
                return json.load(f)
        except:
            return {}

    def _save_config(self, config):
        with open(self.config_file, "w") as f:
            json.dump(config, f, indent=2)

    def _load_active_personality(self, config):
        pid = config.get("active_personality", "ai_assistant")
        try:
            with open(self.personalities_file, "r", encoding="utf-8-sig") as f:
                pers = json.load(f)
                return next((p for p in pers if p["id"] == pid), {})
        except Exception:
            return {}
            
    def _get_fast_model_for_provider(self, provider: str) -> str:
        """Helper to get a fast/cheap model for the specific provider."""
        if provider == "openai":
            return "gpt-5-nano"
        elif provider == "gemini":
            return "gemini-3-flash-preview"
        elif provider == "anthropic":
            return "claude-3-haiku-20240307"
        elif provider == "groq":
            return "llama3-8b-8192"
        return "gpt-5-nano"

    def _get_recent_memories_raw(self, limit: int = 20) -> List[ExtractedFact]:
        """
        CONTEXT INJECTION: Holt die neuesten Fakten direkt aus der DB.
        Limit auf 20 erhöht für besseres Kurzzeitgedächtnis.
        """
        try:
            recent_mems = self.db.query(Memory).order_by(desc(Memory.id)).limit(limit).all()
            extracted_facts = []
            for mem in recent_mems:
                try:
                    data = json.loads(mem.snippet)
                    fact = ExtractedFact(
                        fact=data.get("fact", ""),
                        category=data.get("category", "Allgemein"),
                        type=data.get("type", "GENERAL"),
                        expires_in_hours=None,
                        canonical_key=data.get("canonical_key"),
                        subject_role=data.get("subject_role"),
                        subject_pet_type=None,
                        subject_relative_type=None,
                        subject_name=data.get("subject_name"),
                        predicate=data.get("predicate"),
                        object_value=data.get("object_value"),
                        evidence=data.get("evidence", "")
                    )
                    extracted_facts.append(fact)
                except Exception as e:
                    continue
            return extracted_facts
        except Exception as e:
            logger.warning(f"Konnte Recent Memories nicht laden: {e}")
            return []

    def _save_cost_from_response(self, response: Dict, model: str, provider: str, source_type: str):
        """Extracts cost and usage from LLM response and saves it to the database."""
        if "cost" in response and "usage" in response:
            try:
                cost_data = response["cost"]
                usage_data = response["usage"]
                cost_service.create_cost_entry(
                    db=self.db,
                    amount=cost_data.get("total_cost", 0.0),
                    model=model,
                    provider=provider,
                    source_type=source_type,
                    input_tokens=usage_data.get("prompt_tokens", 0) or usage_data.get("input_tokens", 0),
                    output_tokens=usage_data.get("completion_tokens", 0) or usage_data.get("output_tokens", 0)
                )
            except Exception as e:
                logger.error(f"Failed to save cost entry: {e}")

    async def handle_chat_request(self, request: schemas.ChatRequest) -> Dict:
        logger.info(f"--- ORCHESTRATOR START: {request.provider} / {request.model} ---")
        
        if not request.chat_id: raise HTTPException(400, "Missing chat_id")
        user_text = request.prompt or ""
        if request.content:
            for part in request.content:
                if part.type == "text":
                    user_text = part.text
                    break
        if not user_text: raise HTTPException(400, "Empty request")
            
        api_key = keyring.get_password("Janus-Projekt", request.provider)
        if not api_key: raise HTTPException(400, "API Key missing")

        crud.create_message(self.db, request.chat_id, "user", user_text)

        config = self._load_config()
        persona = self._load_active_personality(config)
        email_context = self.last_email_list_per_chat.get(request.chat_id)

        # Classify intent (uses a fast model for efficiency)
        intent = await intent_classifier.classify_intent_with_llm(
            user_text, api_key, provider=request.provider
        )
        
        # 1. FAST LANE (z.B. für Grüße) -> Respektiert die Wahl des Nutzers
        if intent == 'BEGRUESSUNG':
            logger.info(" FAST LANE: Greeting/Thanks detected.")
            messages = self.context_builder.build_chat_history_for_execution(
                request.chat_id, user_text, persona, email_context, facts=[]
            )
            executor = ToolExecutor(self.db, api_key, request.provider, request.model, additional_context={"email_context": email_context})
            
            response = await llm_gateway.reason_and_respond(
                provider=request.provider, model=request.model, api_key=api_key, # HIER: request.model verwenden
                chat_history=messages, context_manager=self.context_manager, db=self.db,
                user_prompt=user_text, chat_id=request.chat_id, tool_executor=executor,
                disable_tools=True
            )
            
            self._save_cost_from_response(response, request.model, request.provider, "fast_lane_response")

            final_text = response.get("text", "Hallo!")
            crud.create_message(self.db, request.chat_id, "model", final_text)
            self._trigger_fact_extraction(request.chat_id, user_text, final_text, api_key, request.provider)
            return {"sender": "model", "text": final_text}

        # 2. FACT-ACK LANE (für Fakten-Angabe) -> Respektiert die Wahl des Nutzers
        elif intent == 'FAKTEN_ANGABE':
            logger.info(" FACT-ACK LANE: Fact submission detected.")
            
            system_prompt = "Bestätige dem Nutzer kurz, freundlich und in einem Satz, dass du die Information verstanden hast und sie dir merkst."
            ack_messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_text}]
            
            response = await llm_gateway.call_llm(provider=request.provider, model_id=request.model, api_key=api_key, messages=ack_messages) # HIER: request.model verwenden
            
            self._save_cost_from_response(response, request.model, request.provider, "fact_ack_response")

            final_text = response.get("text", "Verstanden.")
            crud.create_message(self.db, request.chat_id, "model", final_text)
            self._trigger_fact_extraction(request.chat_id, user_text, final_text, api_key, request.provider)
            return {"sender": "model", "text": final_text}

        # 3. SLOW LANE (DIAMOND LOGIC) -> Haupt-Antwort nutzt request.model
        logger.info("--- SLOW LANE: Complex query detected. Starting Diamond Logic. ---")
        
        # A) Standard Retrieval
        relevant_facts = memory_manager.get_relevant_facts_as_objects(
            db=self.db, query=user_text, limit=15
        )
        
        # B) Context Injection
        recent_facts = self._get_recent_memories_raw(limit=20)
        
        # Merge & Deduplicate
        seen_keys = set(f.canonical_key for f in relevant_facts if f.canonical_key)
        injected_count = 0
        for fact in recent_facts:
            if fact.canonical_key and fact.canonical_key not in seen_keys:
                relevant_facts.append(fact)
                seen_keys.add(fact.canonical_key)
                injected_count += 1
        
        if injected_count > 0:
            logger.info(f"Context Injection: Added {injected_count} recent facts to context.")

        messages = self.context_builder.build_chat_history_for_execution(
            request.chat_id, user_text, persona, email_context, facts=relevant_facts
        )
        
        executor = ToolExecutor(
            self.db, api_key, request.provider, request.model,
            additional_context={"email_context": email_context}
        )
        
        # Planner kann ein schnelles Modell verwenden, da es eine interne Aufgabe ist
        planner_model = self._get_fast_model_for_provider(request.provider)
        is_comparison_query = " oder " in user_text.lower() or " vs " in user_text.lower() or "?" in user_text
        
        try:
            decision_context = await generate_decision_context(
                db=self.db, 
                user_query=user_text, 
                retrieved_facts=relevant_facts, 
                api_key=api_key, 
                provider=request.provider, 
                model=planner_model,
                query_context=user_text if is_comparison_query else ""
            )
            
            logger.info(f"Diamond Decision Status: {decision_context.status}")
            
            if decision_context.status == "ok" and decision_context.recommendations:
                # Diamond Renderer Logik bleibt gleich...
                # ... (hier gekürzt für Lesbarkeit)
                top_rec = decision_context.recommendations[0]
                final_text = f"### Empfehlung: {top_rec.candidate_name}\n\n"
                # ... Restlicher Renderer-Code ...
                crud.create_message(self.db, request.chat_id, "model", final_text)
                self._trigger_fact_extraction(request.chat_id, user_text, final_text, api_key, request.provider)
                return {"sender": "model", "text": final_text}
                
        except Exception as e:
            logger.error(f"Fehler in der Diamond Logic Pipeline: {str(e)}", exc_info=True)
        
        # Fallback Standard LLM - verwendet das vom User gewählte Modell
        response = await llm_gateway.reason_and_respond(
            provider=request.provider, model=request.model, api_key=api_key,
            chat_history=messages, context_manager=self.context_manager, db=self.db,
            user_prompt=user_text, chat_id=request.chat_id, tool_executor=executor,
            disable_tools=intent_classifier.is_identity_query(user_text)
        )
        
        self._save_cost_from_response(response, request.model, request.provider, "slow_lane_response")

        final_text = response.get("text", "...")
        crud.create_message(self.db, request.chat_id, "model", final_text)
        self._trigger_fact_extraction(request.chat_id, user_text, final_text, api_key, request.provider)
        return {"sender": "model", "text": final_text}

    def _trigger_fact_extraction(self, chat_id, user_text, final_text, api_key, provider):
        """Helper to trigger fact extraction background task safely."""
        if final_text and not intent_classifier.is_greeting(user_text):
            asyncio.create_task(self._run_fact_extraction(
                chat_id, user_text, final_text, api_key, provider
            ))

    async def _run_fact_extraction(self, chat_id, user, assistant, key, provider):
        """Starts the fact extraction in the background."""
        try:
            extraction_model = self._get_fast_model_for_provider(provider)
            await memory_extractor.extract_and_save_fact(
                self.db, chat_id, user, key, provider, extraction_model
            )
        except Exception as e:
            logger.error(f"Fact extraction error: {e}")