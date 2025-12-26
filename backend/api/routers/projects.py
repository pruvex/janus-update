import asyncio
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.data import crud, schemas, database
from backend.services.project_service import initialize_project_knowledge  # Diese Funktion erstellen wir gleich

router = APIRouter()
logger = logging.getLogger("janus_backend")

@router.post("/projects", response_model=schemas.ProjectResponse)
async def create_new_project(request: schemas.ProjectCreateWithContext, db: Session = Depends(database.get_db)):
    """
    Erstellt ein neues Projekt und startet die autonome Wissensbeschaffung.
    """
    try:
        db_project = crud.create_project(db, name=request.name, description=request.description)
        
        # Starte den autonomen Agenten im Hintergrund (non-blocking)
        asyncio.create_task(
            initialize_project_knowledge(
                db=db,
                project_id=db_project.id,
                project_name=request.name,
                active_provider=request.active_provider,
                active_model=request.active_model
            )
        )
        
        return schemas.ProjectResponse.model_validate(db_project)
    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Projekts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Projekt konnte nicht erstellt werden.")

@router.get("/projects", response_model=List[schemas.ProjectResponse])
def get_all_projects(db: Session = Depends(database.get_db)):
    """Gibt eine Liste aller Projekte zurück."""
    projects = crud.get_all_projects(db)
    return [schemas.ProjectResponse.model_validate(p) for p in projects]

# Hier kommen später Endpunkte für Datei-Upload, Löschen, Umbenennen, etc.
