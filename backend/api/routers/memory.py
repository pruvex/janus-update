from typing import List

from backend.data import crud, schemas
from backend.data.database import get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/memory", response_model=List[schemas.MemoryResponse])
async def get_all_memory_entries(db: Session = Depends(get_db)):
    return crud.get_all_memories(db)


@router.put("/memory/{memory_id}", response_model=schemas.MemoryResponse)
async def update_memory_entry(
    memory_id: int, update_data: schemas.MemoryUpdate, db: Session = Depends(get_db)
):
    updated_memory = crud.update_memory(db, memory_id, update_data.snippet, update_data.category)
    if not updated_memory:
        raise HTTPException(status_code=404, detail="Memory entry not found")
    return updated_memory


@router.delete("/memory/{memory_id}")
async def delete_memory_entry(memory_id: int, db: Session = Depends(get_db)):
    success = crud.delete_memory(db, memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory entry not found")
    return {"message": "Memory entry deleted successfully"}
