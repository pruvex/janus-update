from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.data import database, schemas
from backend.services import memory_manager

router = APIRouter()

@router.get("/memory", response_model=List[schemas.MemoryResponse])
def get_all_memories(db: Session = Depends(database.get_db)):
    """Holt alle Memories für das Frontend, sortiert nach Wichtigkeit (Diamond Standard)."""
    return memory_manager.get_memories_for_management(db)

@router.post("/memory", response_model=schemas.MemoryResponse, status_code=status.HTTP_201_CREATED)
def create_manual_memory(memory: schemas.MemoryCreate, db: Session = Depends(database.get_db)):
    """Erstellt manuell einen Fakt. Weist ihn dem letzten Chat zu (Workaround für FK)."""
    last_chat = db.query(database.Chat).order_by(database.Chat.id.desc()).first()
    chat_id_to_use = last_chat.id if last_chat else 1 

    db_memory = memory_manager.save_memory_snippet(
        db,
        chat_id=chat_id_to_use, 
        snippet_text=memory.snippet,
        category=memory.category,
        is_core=memory.is_core_fact,
        core_priority=memory.core_priority
    )
    
    if not db_memory:
        raise HTTPException(status_code=500, detail="Fehler beim Speichern (Embedding Service?).")
    return db_memory

@router.put("/memory/{memory_id}", response_model=schemas.MemoryResponse)
def update_memory(memory_id: int, update_data: schemas.MemoryUpdate, db: Session = Depends(database.get_db)):
    """Aktualisiert einen Fakt."""
    existing = db.query(database.Memory).filter(database.Memory.id == memory_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Memory not found")
        
    snippet_to_use = update_data.snippet if update_data.snippet is not None else existing.snippet
    
    db_memory = memory_manager.update_memory_snippet(
        db,
        memory_id=memory_id,
        new_snippet=snippet_to_use,
        is_core=update_data.is_core_fact,
        core_priority=update_data.core_priority
    )
    
    # Manuelles Update der Kategorie, falls geändert
    if update_data.category is not None:
        db_memory.category = update_data.category
        db.commit()
        db.refresh(db_memory)

    if not db_memory:
        raise HTTPException(status_code=500, detail="Update failed.")
    return db_memory

@router.delete("/memory/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_memory(memory_id: int, db: Session = Depends(database.get_db)):
    """Löscht einen Fakt."""
    memory_item = db.query(database.Memory).filter(database.Memory.id == memory_id).first()
    if not memory_item:
        raise HTTPException(status_code=404, detail="Memory not found")
    db.delete(memory_item)
    db.commit()
    return None
