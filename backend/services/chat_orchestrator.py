import logging
import json
import os
import base64
import asyncio
import keyring
from datetime import datetime
from typing import Dict, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.data import crud, database, schemas
from backend.services import llm_gateway, image_manager, memory_extractor
from backend.services.context_manager import ContextManager
from backend.services.tool_executor import ToolExecutor
from backend.services.chat.tool_selector import ToolSelector
from backend.services.chat.context_builder import ContextBuilder
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
        
        # Initialize Helpers
        initialize_file_from_template(template_config_file_path, config_file_path)
        initialize_file_from_template(template_personalities_file_path, personalities_file_path)
        
        self.context_builder = ContextBuilder(db)
        
        # State Caches
        self.last_response_id_per_chat = {}
        self.last_ssml_response_per_chat = {}
        self.last_email_list_per_chat = {}  # Simple dict is enough

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

    async def handle_chat_request(self, request: schemas.ChatRequest) -> Dict:
        logger.info(f"--- ORCHESTRATOR (Refactored): {request.provider} / {request.model} ---")
        
        # 1. Input Processing & Validation
        if not request.chat_id:
            raise HTTPException(400, "Missing chat_id")
        
        user_text = request.prompt or ""
        image_url = None
        
        # Extract text/image from content list if present
        if request.content:
            for part in request.content:
                if part.type == "text":
                    user_text = part.text
                elif part.type == "image_url":
                    image_url = part.image_url
        
        if not user_text and not image_url:
            raise HTTPException(400, "Empty request")

        api_key = keyring.get_password("Janus-Projekt", request.provider)
        if not api_key:
            raise HTTPException(400, "API Key missing")

        # 2. Image Handling (Upload & Context retrieval)
        active_image_data = self.context_builder.prepare_image_input(
            image_url, request.chat_id, user_text
        )
        
        # Save uploaded image locally if new
        local_image_path = None
        if image_url:
            try:
                # Simple save logic
                header, encoded = image_url.split(",", 1)
                data = base64.b64decode(encoded)
                local_image_path = image_manager.save_image_from_bytes(
                    data, description="upload", subdirectory="uploads"
                )
            except Exception as e:
                logger.error(f"Image save failed: {e}")

        # Save User Message to DB
        crud.create_message(
            self.db, request.chat_id, "user", user_text, image_path=local_image_path
        )

        # 3. Context Building
        config = self._load_config()
        persona = self._load_active_personality(config)
        email_context = self.last_email_list_per_chat.get(request.chat_id)
        
        system_msg = self.context_builder.build_system_message(
            persona, user_text, email_context
        )
        
        # === NEU: Projekt-Wissen injizieren ===
        project_context = ""
        if request.project_id:
            from backend.rag_manager import query_knowledge_base
            
            project = crud.get_project(self.db, request.project_id)
            if project:
                collection_name = f"project_{project.id}"
                
                # Relevante Dokumenten-Schnipsel via RAG holen
                rag_results = await asyncio.to_thread(query_knowledge_base, user_text, collection_name, n_results=3)
                
                if rag_results:
                    project_context = "\n\n--- WISSEN AUS PROJEKT-DATEIEN ---\n" + "\n\n---\n\n".join(rag_results)

        # System-Nachricht mit Projekt-Wissen anreichern
        if project_context and system_msg and "content" in system_msg:
            system_msg["content"] += project_context
        # ======================================
        
        history = self.context_builder.build_chat_history(request.chat_id)
        
        # Assemble final messages
        messages = []
        if system_msg:
            messages.append(system_msg)
        messages.extend(history)
        
        # Add current user message
        if active_image_data:
            messages.append({
                "role": "user", 
                "content": [
                    {"type": "text", "text": user_text},
                    {"type": "image_url", "image_url": {"url": active_image_data}}
                ]
            })
        else:
            messages.append({"role": "user", "content": user_text})

        # 4. Tool Selection
        tools = ToolSelector.select_tools(user_text, email_context)
        
        # 5. Execution (Gateway)
        # Executor für State-Injection vorbereiten
        executor = ToolExecutor(
            self.db, api_key, request.provider, request.model,
            additional_context={
                "last_ssml": self.last_ssml_response_per_chat.get(request.chat_id),
                "email_context": email_context
            }
        )

        response = await llm_gateway.reason_and_respond(
            provider=request.provider,
            model=request.model,
            api_key=api_key,
            chat_history=messages,
            context_manager=self.context_manager,
            db=self.db,
            user_prompt=user_text,
            chat_id=request.chat_id,
            tool_executor=executor,
            tools_override=tools,
            disable_tools=intent_classifier.is_identity_query(user_text),
            image_data=active_image_data  # For legacy gateway logic
        )

        # 6. Response Handling
        final_text = response.get("text", "")
        final_image_url = response.get("image_url", None) # NEU: image_url aus der Response holen
        
        if not final_text and not final_image_url: # NEU: Wenn weder Text noch Bild, dann "..."
            final_text = "..."
        
        crud.create_message(self.db, request.chat_id, "model", final_text, image_path=final_image_url) # NEU: image_path übergeben
        
        # Update Config (Last Used)
        config["last_used_provider"] = request.provider
        config["last_used_model"] = request.model
        self._save_config(config)

        # 7. Background Tasks (Fact Extraction)
        if final_text and not intent_classifier.is_greeting(user_text):
            asyncio.create_task(self._run_fact_extraction(
                request.chat_id, user_text, final_text, api_key, request.provider
            ))

        return {"sender": "model", "text": final_text}

    async def _run_fact_extraction(self, chat_id, user, assistant, key, provider):
        """
        Startet die Fakten-Extraktion im Hintergrund.
        WICHTIG: Arbeitet autark mit dem Provider des aktuellen Chats.
        """
        try:
            # Wir wählen ein effizientes Modell passend zum Provider
            extraction_model = None
            
            if provider == "openai":
                extraction_model = "gpt-4o-mini"
            elif provider == "gemini":
                # UPDATE: Nutzung von gemini-3-flash-preview für Faktenextraktion
                extraction_model = "gemini-3-flash-preview" 
            elif provider == "anthropic":
                extraction_model = "claude-3-haiku-20240307"
            elif provider == "groq":
                extraction_model = "llama3-8b-8192"
            else:
                # Fallback: Wenn kein Mapping existiert, brechen wir ab, statt zu raten.
                logger.warning(f"Fact extraction skipped: No dedicated extraction model mapping for provider '{provider}'.")
                return

            # Der Aufruf nutzt nun strikt den übergebenen Key und Provider
            await memory_extractor.extract_and_save_fact(
                self.db, 
                chat_id, 
                f"U: {user}\nA: {assistant}", 
                key, 
                provider, 
                extraction_model
            )
        except Exception as e:
            logger.error(f"Fact extraction error: {e}")
