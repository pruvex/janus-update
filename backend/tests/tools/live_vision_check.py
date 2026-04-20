import argparse
import asyncio
import base64
import json
import os
from pathlib import Path
from typing import List

from backend.data import crud, schemas
from backend.data.database import SessionLocal
from backend.services.chat_orchestrator import ChatOrchestrator
from backend.services.context_manager import ContextManager
from backend.utils.config_loader import load_model_catalog
from backend.utils.paths import get_app_data_dir


def build_request(image_b64: str, provider: str, model: str, prompt: str) -> schemas.ChatRequest:
    content: List[schemas.ContentPart] = [
        schemas.ContentPart(type="text", text=prompt),
        schemas.ContentPart(type="image_url", image_url=f"data:image/jpeg;base64,{image_b64}"),
    ]
    return schemas.ChatRequest(
        prompt=prompt,
        content=content,
        provider=provider,
        model=model,
    )


async def main():
    parser = argparse.ArgumentParser(description="Live-Integration-Check für Vision + Orchestrator")
    parser.add_argument("--image", type=Path, default=Path("Bilder/18.jpg"), help="Pfad zum Testbild")
    parser.add_argument("--prompt", type=str, default="Beschreibe die Person auf dem Bild.", help="Textprompt")
    parser.add_argument("--provider", type=str, default="gemini", help="Provider, z.B. gemini oder openai")
    parser.add_argument("--model", type=str, default="gemini-3-flash-preview", help="Modellalias aus dem Katalog")
    args = parser.parse_args()

    with SessionLocal() as db:
        chat = crud.create_chat(db, title="Live Vision Check", project_id=None)

    with open(args.image, "rb") as img_file:
        image_b64 = base64.b64encode(img_file.read()).decode("ascii")

    mc = load_model_catalog()
    cm = ContextManager(model_catalog=mc.values())
    orchestrator = ChatOrchestrator(
        db=SessionLocal(),
        context_manager=cm,
        model_catalog=mc,
        config_file_path=os.path.join(get_app_data_dir(), "config.json"),
        template_config_file_path=os.path.join("backend", "config", "config.json"),
        personalities_file_path=os.path.join(get_app_data_dir(), "personalities.json"),
        template_personalities_file_path=os.path.join("backend", "config", "personalities.json"),
    )

    request = build_request(image_b64, args.provider, args.model, args.prompt)
    request.chat_id = chat.id
    request.project_id = None

    response = await orchestrator.handle_chat_request(request)
    print(f"Live-Check Chat {chat.id} abgeschlossen.")
    print(json.dumps(response, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
