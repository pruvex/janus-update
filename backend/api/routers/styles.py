import json
import logging
import os
from typing import List

import keyring
from backend.services.creative_writer import generate_style_profile_from_rag
from backend.utils.paths import resource_path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger("janus_backend")


class StyleProfile(BaseModel):
    genre: str
    author_style: str
    key_elements: List[str]
    complexity: str


class StyleProfileSaveRequest(BaseModel):
    profile_key: str
    profile_data: StyleProfile


@router.post("/rag/collections/{collection_name}/analyze-style", response_model=StyleProfile)
async def analyze_collection_style(collection_name: str):
    logger.info(f"Analyzing style for collection: {collection_name}")
    try:
        key = keyring.get_password("Janus-Projekt", "openai")
        return await generate_style_profile_from_rag(
            collection_name=collection_name,
            api_key=key,
            model="gpt-4o-mini",
            provider="openai",
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Collection not found.")
    except Exception as e:
        logger.error(f"Style analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/styles/profiles")
async def save_style_profile(request: StyleProfileSaveRequest):
    profiles_path = resource_path("backend/config/style_profiles.json")
    try:
        profiles = {}
        if os.path.exists(profiles_path):
            with open(profiles_path, "r", encoding="utf-8-sig") as f:
                profiles = json.load(f)

        profiles[request.profile_key] = request.profile_data.dict()

        with open(profiles_path, "w", encoding="utf-8") as f:
            json.dump(profiles, f, indent=2, ensure_ascii=False)

        return {"message": f"Style profile '{request.profile_key}' saved."}
    except Exception as e:
        logger.error(f"Failed to save style profile: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
