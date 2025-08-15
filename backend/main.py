import json
import os
import keyring
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from . import llm_gateway
import traceback
from fastapi.responses import JSONResponse
from datetime import datetime
from . import database
from typing import List, Optional

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    database.init_db()
    print("Database initialized.") # Optional: Debugging-Meldung

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Erlaube alle Ursprünge für die lokale Entwicklung
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
MODEL_CATALOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model_catalog.json")

def load_model_catalog():
    print(f"DEBUG: Attempting to load model catalog from: {MODEL_CATALOG_FILE}")
    print(f"DEBUG: Does model catalog file exist? {os.path.exists(MODEL_CATALOG_FILE)}")
    if not os.path.exists(MODEL_CATALOG_FILE):
        return []
    try:
        with open(MODEL_CATALOG_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"ERROR: Invalid JSON in model catalog file: {MODEL_CATALOG_FILE}")
        return []
    except Exception as e:
        print(f"ERROR: Unexpected error loading model catalog: {e}")
        raise

# Helper function for cost saving (re-adding)
def save_cost_entry(model: str, input_tokens: int = None, output_tokens: int = None, image_quality: str = None, image_cost: float = None, total_cost: float = 0):
    """Helper function to save a cost entry to the database."""
    try:
        print(f"DEBUG: Speichere Kosteneintrag: total_cost={total_cost}")
        database.save_cost_entry(
            date=datetime.now().isoformat(),
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            image_quality=image_quality,
            image_cost=image_cost,
            total_cost=total_cost
        )
    except Exception as e:
        print(f"ERROR: Kosteneintrag konnte nicht gespeichert werden: {e}")

class ChatRequest(BaseModel):
    prompt: str
    provider: str
    model: str

class ApiKey(BaseModel):
    provider: str
    api_key: str

class ModelSelection(BaseModel):
    provider: str
    models: list[str]

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {} # Leere Konfiguration, wenn Datei nicht existiert
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {} # Leere Konfiguration, wenn JSON ungültig ist
    except Exception:
        raise # Re-raise other exceptions

def save_config(config):
    try:
        # Sicherstellen, dass das Verzeichnis existiert
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        raise

@app.get("/api/health")
async def read_health():
    return {"status": "ok", "message": "Hello from Janus Backend"}

@app.get("/api/keys")
async def get_api_keys():
    try:
        available_providers = ["openai", "gemini"] # Annahme: Diese Liste kommt von llm_gateway
        stored_api_keys = {}
        for provider in available_providers:
            if keyring.get_password("Janus-Projekt", provider) is not None:
                stored_api_keys[provider] = "********" # Maskiere den Key für die UI
        return {"api_keys": stored_api_keys}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading API keys: {str(e)}")

@app.get("/api/models/selection/{provider}")
async def get_model_selection(provider: str):
    try:
        catalog = load_model_catalog()
        # Filter models by provider and return their IDs
        selected_models = [model["id"] for model in catalog if model["provider"] == provider]
        return {"selected_models": selected_models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading model selection: {str(e)}")

@app.post("/api/models/selection")
async def save_model_selection(selection: ModelSelection):
    try:
        config = load_config()
        if "model_selection" not in config:
            config["model_selection"] = {}
        config["model_selection"][selection.provider] = selection.models
        save_config(config)
        return {"message": "Model selection saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving model selection: {str(e)}")

@app.post("/api/keys")
async def add_api_key(key: ApiKey):
    try:
        keyring.set_password("Janus-Projekt", key.provider, key.api_key)
        return {"message": "API Key saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving API key: {str(e)}")

@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        api_key = keyring.get_password("Janus-Projekt", request.provider)
        if not api_key:
            raise HTTPException(status_code=400, detail=f"API Key for provider {request.provider} not found.")
        
        # Der Gateway gibt jetzt ein sauberes, flaches Dictionary zurück
        gateway_response = await llm_gateway.call_llm(request.provider, request.model, request.prompt, api_key)
        
        # --- Korrekte Kosten-Speicherung ---
        usage = gateway_response.get("usage")
        print(f"DEBUG (main.py): Received usage from gateway: {usage}") # NEW
        cost = gateway_response.get("cost")

        if usage and cost:
            total_cost = cost.get("total_cost", 0)
            
            save_cost_entry(
                    model=request.model,
                    input_tokens=usage.get("input_tokens"),
                    output_tokens=usage.get("output_tokens"),
                    image_quality=usage.get("image_quality"),
                    image_cost=usage.get("image_cost"),
                    total_cost=total_cost
                )

        # --- Korrekte Erstellung der finalen Antwort ---
        final_response = {
            "sender": "model",
            "text": gateway_response.get("text", ""),
            "image_url": gateway_response.get("image_url")
        }

        return final_response

    except HTTPException as e:
        raise e
    except Exception as e:
        tb_str = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"Ein interner Serverfehler ist aufgetreten.\nTraceback:\n{tb_str}")

# --- Hinzugefügt für Kosten-Visualisierung ---
class CostDashboard(BaseModel):
    current_month_cost: float
    monthly_budget: float

@app.get("/api/costs/dashboard", response_model=CostDashboard)
async def get_costs_dashboard():
    today = datetime.now()
    current_month_cost = database.get_costs_for_month(today.year, today.month)
    
    config = load_config()
    budget = config.get("monthly_budget", 10.00) # Default to 10.00 if not set
    return CostDashboard(current_month_cost=current_month_cost, monthly_budget=budget)

class BudgetUpdate(BaseModel):
    budget: float

@app.post("/api/budget")
async def update_budget(budget_update: BudgetUpdate):
    try:
        config = load_config()
        config["monthly_budget"] = budget_update.budget
        save_config(config)
        return {"message": "Budget updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class CostDetail(BaseModel):
    date: datetime
    model: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    image_quality: Optional[str] = None
    image_cost: Optional[float] = None
    total_cost: float

@app.get("/api/costs/details", response_model=List[CostDetail])
async def get_costs_details():
    details = database.get_all_cost_entries()
    return details

@app.get("/api/costs/summary-by-model")
async def get_costs_summary_by_model():
    summary = database.get_costs_summary_by_model_for_current_month()
    return summary

@app.get("/api/costs/summary")
async def get_costs_summary():
    all_entries = database.get_all_cost_entries()
    model_catalog = load_model_catalog() # Load model catalog

    summary = {} # Aggregate costs here

    for entry in all_entries:
        model_name = entry["model"]
        total_cost = entry["total_cost"]
        input_tokens = entry["input_tokens"]
        output_tokens = entry["output_tokens"]
        image_quality = entry["image_quality"]
        image_cost = entry["image_cost"]

        # Get model type from catalog
        model_type = "unknown"
        for model_info in model_catalog:
            if model_info["id"] == model_name:
                model_type = model_info.get("type", "unknown")
                break

        if model_name not in summary:
            summary[model_name] = {
                "model": model_name,
                "total_cost": 0.0,
                "input_tokens": 0,
                "output_tokens": 0,
                "image_count": 0,
                "type": model_type # Initialize type from catalog
            }
        
        summary[model_name]["total_cost"] += total_cost

        if model_type == "text":
            summary[model_name]["input_tokens"] += (input_tokens if input_tokens is not None else 0)
            summary[model_name]["output_tokens"] += (output_tokens if output_tokens is not None else 0)
        elif model_type == "image":
            summary[model_name]["image_count"] += 1 # Count each image generation

    # Convert dictionary to list of values
    return list(summary.values())
