import os, json, subprocess, shutil
import logging
from fastapi import APIRouter, HTTPException
from backend.services.image_engine_checker import (
    get_engine_type_and_status,
    has_nvidia_gpu,
    start_engine_process,
    stop_engine_process,
)

router = APIRouter()
logger = logging.getLogger("janus_backend")

CATALOG_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend", "data", "image_models.json")
)


def _load_catalog() -> list[dict]:
    if not os.path.exists(CATALOG_PATH):
        return []
    with open(CATALOG_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def _get_model(models: list[dict], model_id: str) -> dict:
    model = next((m for m in models if m.get("id") == model_id), None)
    if not model:
        raise HTTPException(status_code=404, detail="Modell nicht gefunden")
    return model


def _ensure_cpu_run_script(install_dir: str, project_root: str) -> str:
    run_script = os.path.join(install_dir, "run_engine.bat")
    lines = [
        "@echo off",
        "title Janus CPU Image Engine",
        'cd /d "%~dp0"',
        "call venv\\Scripts\\activate.bat",
        f"set PYTHONPATH={project_root}",
        "python -m backend.services.local_image_server",
    ]
    os.makedirs(install_dir, exist_ok=True)
    with open(run_script, "w", encoding="utf-8") as file:
        file.write("\n".join(lines) + "\n")
    return run_script


@router.get("/catalog")
async def get_catalog():
    models = _load_catalog()
    gpu_available = has_nvidia_gpu()
    for model in models:
        base = os.path.exists(model.get("install_dir", ""))
        if model.get("type") == "gpu":
            model["is_installed"] = base and gpu_available
        else:
            model["is_installed"] = base
    return models


@router.get("/status")
async def get_engine_status():
    return await get_engine_type_and_status()


@router.post("/install/{model_id}")
async def install_model(model_id: str):
    logger.info("API CALL: Installiere Modell %s", model_id)
    models = _load_catalog()
    model = _get_model(models, model_id)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    script_path = os.path.normpath(os.path.join(base_dir, model.get("install_script", "")))
    if not os.path.exists(script_path):
        raise HTTPException(status_code=404, detail="Installationsskript fehlt")

    subprocess.Popen(f'cmd.exe /c "{script_path}"', shell=True)
    return {"status": "started"}


@router.post("/start/{model_id}")
async def start_model(model_id: str):
    logger.info("API CALL: Starte Modell %s", model_id)
    models = _load_catalog()
    model = _get_model(models, model_id)
    install_dir = model.get("install_dir", "")
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

    if model.get("id") == "sd15-cpu" and install_dir:
        run_script = _ensure_cpu_run_script(install_dir, base_dir)
        start_engine_process(run_script)
        return {"status": "started", "mode": "run_script_rewritten"}

    run_script = os.path.join(install_dir, "run_engine.bat")
    if os.path.exists(run_script):
        start_engine_process(run_script)
        return {"status": "started", "mode": "run_script"}

    # Fallback: installer script can bootstrap/start if run script is missing.
    script_path = os.path.normpath(os.path.join(base_dir, model.get("install_script", "")))
    if not os.path.exists(script_path):
        raise HTTPException(status_code=404, detail="Startskript fehlt")
    subprocess.Popen(f'cmd.exe /c "{script_path}"', shell=True)
    return {"status": "started", "mode": "install_script"}


@router.post("/stop")
async def stop_model():
    logger.info("API CALL: Stoppe lokale Bild-Engine")
    stop_engine_process()
    return {"status": "stopped"}


@router.post("/uninstall/{model_id}")
async def uninstall_model(model_id: str):
    logger.info("API CALL: Deinstalliere Modell %s", model_id)
    models = _load_catalog()
    model = next((m for m in models if m.get("id") == model_id), None)
    if model:
        install_path = model.get("install_dir")
        if install_path and os.path.exists(install_path):
            try:
                shutil.rmtree(install_path)
                logger.info("Erfolgreich gelöscht: %s", install_path)
                return {"status": "uninstalled"}
            except Exception as exc:
                logger.error("Konnte Verzeichnis %s nicht löschen: %s", install_path, exc)
                raise HTTPException(status_code=500, detail=f"Löschfehler: {str(exc)}")
        return {"status": "already_gone"}
    raise HTTPException(status_code=404, detail="Modell nicht gefunden")
