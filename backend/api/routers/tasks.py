# backend/api/routers/tasks.py
"""
Tasks API Router with Progress Tracking Support.

Provides endpoints for task management including:
- CRUD operations for tasks
- Progress tracking with history
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.data.database import get_db
from backend.data import models
from backend.data.schemas import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskProgressUpdate,
    TaskProgressResponse,
    ProgressLogEntry,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _update_progress_log(task: models.Task, new_progress: int, note: Optional[str] = None) -> dict:
    """
    Update the progress log with a new entry.
    
    Args:
        task: The task model instance
        new_progress: The new progress value (0-100)
        note: Optional note about this progress update
    
    Returns:
        The newly created log entry
    """
    # Initialize progress_log if None
    if task.progress_log is None:
        task.progress_log = []
    
    # Create new log entry
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "progress": new_progress,
        "note": note,
    }
    
    # Append to log
    task.progress_log.append(log_entry)
    
    return log_entry


def _convert_progress_log(log: Optional[List[dict]]) -> List[ProgressLogEntry]:
    """Convert stored JSON log to list of ProgressLogEntry schemas."""
    if not log:
        return []
    
    result = []
    for entry in log:
        try:
            # Parse timestamp string back to datetime
            timestamp_str = entry.get("timestamp", "")
            if timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str)
            else:
                timestamp = datetime.utcnow()
            
            result.append(ProgressLogEntry(
                timestamp=timestamp,
                progress=entry.get("progress", 0),
                note=entry.get("note"),
            ))
        except (ValueError, TypeError):
            # Skip invalid entries
            continue
    
    return result


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task."""
    db_task = models.Task(
        title=task.title,
        description=task.description,
        status=task.status,
        progress=task.progress,
        chat_id=task.chat_id,
        project_id=task.project_id,
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    return TaskResponse(
        id=db_task.id,
        title=db_task.title,
        description=db_task.description,
        status=db_task.status,
        progress=db_task.progress,
        progress_log=_convert_progress_log(db_task.progress_log),
        chat_id=db_task.chat_id,
        project_id=db_task.project_id,
        created_at=db_task.created_at,
        updated_at=db_task.updated_at,
        completed_at=db_task.completed_at,
    )


@router.get("/", response_model=List[TaskResponse])
def list_tasks(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    project_id: Optional[int] = None,
    chat_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """List all tasks with optional filtering."""
    query = db.query(models.Task)
    
    if status:
        query = query.filter(models.Task.status == status)
    if project_id:
        query = query.filter(models.Task.project_id == project_id)
    if chat_id:
        query = query.filter(models.Task.chat_id == chat_id)
    
    tasks = query.offset(skip).limit(limit).all()
    
    return [
        TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            status=task.status,
            progress=task.progress,
            progress_log=_convert_progress_log(task.progress_log),
            chat_id=task.chat_id,
            project_id=task.project_id,
            created_at=task.created_at,
            updated_at=task.updated_at,
            completed_at=task.completed_at,
        )
        for task in tasks
    ]


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get a specific task by ID."""
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )
    
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        progress=task.progress,
        progress_log=_convert_progress_log(task.progress_log),
        chat_id=task.chat_id,
        project_id=task.project_id,
        created_at=task.created_at,
        updated_at=task.updated_at,
        completed_at=task.completed_at,
    )


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task_update: TaskUpdate, db: Session = Depends(get_db)):
    """Update a task's general fields."""
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )
    
    # Store previous progress for logging
    previous_progress = task.progress
    
    # Update fields
    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    
    # If progress changed, log it
    if "progress" in update_data and update_data["progress"] != previous_progress:
        _update_progress_log(
            task,
            update_data["progress"],
            f"Progress updated from {previous_progress}% to {update_data['progress']}%"
        )
    
    # If status changed to completed, set completed_at
    if "status" in update_data and update_data["status"] == "completed":
        task.completed_at = datetime.utcnow()
        task.progress = 100
        # Log completion
        _update_progress_log(task, 100, "Task completed")
    
    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        progress=task.progress,
        progress_log=_convert_progress_log(task.progress_log),
        chat_id=task.chat_id,
        project_id=task.project_id,
        created_at=task.created_at,
        updated_at=task.updated_at,
        completed_at=task.completed_at,
    )


@router.patch("/{task_id}/progress", response_model=TaskProgressResponse)
def update_task_progress(
    task_id: int,
    progress_update: TaskProgressUpdate,
    db: Session = Depends(get_db),
):
    """
    Update a task's progress with a note.
    
    This endpoint specifically handles progress updates and maintains
    a history log of all progress changes.
    """
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )
    
    # Store previous progress
    previous_progress = task.progress
    
    # Validate progress is actually changing
    if progress_update.progress == previous_progress:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"New progress ({progress_update.progress}%) must be different from current progress ({previous_progress}%)",
        )
    
    # Validate progress is moving forward (optional, but good practice)
    if progress_update.progress < previous_progress:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Progress cannot decrease from {previous_progress}% to {progress_update.progress}%",
        )
    
    # Update progress
    task.progress = progress_update.progress
    
    # Update status if reaching 100%
    if task.progress == 100 and task.status != "completed":
        task.status = "completed"
        task.completed_at = datetime.utcnow()
    elif task.progress > 0 and task.status == "pending":
        task.status = "in_progress"
    
    # Add log entry
    log_entry_dict = _update_progress_log(task, task.progress, progress_update.note)
    
    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    
    # Convert log entry to schema
    log_entry = ProgressLogEntry(
        timestamp=datetime.fromisoformat(log_entry_dict["timestamp"]),
        progress=log_entry_dict["progress"],
        note=log_entry_dict["note"],
    )
    
    return TaskProgressResponse(
        task_id=task.id,
        progress=task.progress,
        previous_progress=previous_progress,
        status=task.status,
        note=progress_update.note,
        updated_at=task.updated_at,
        log_entry=log_entry,
    )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a task."""
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )
    
    db.delete(task)
    db.commit()
    
    return None


@router.get("/{task_id}/progress-history", response_model=List[ProgressLogEntry])
def get_task_progress_history(task_id: int, db: Session = Depends(get_db)):
    """Get the full progress history for a task."""
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )
    
    return _convert_progress_log(task.progress_log)
