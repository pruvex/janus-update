from typing import Any, Dict, List, Optional

from backend.data import contact_schemas, crud
from backend.data.database import get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/contacts", response_model=contact_schemas.ContactResponse)
async def create_contact(contact: contact_schemas.ContactCreate, db: Session = Depends(get_db)):
    if contact.email and crud.get_contact_by_email(db, email=contact.email):
        raise HTTPException(
            status_code=409, detail="Ein Kontakt mit dieser E-Mail existiert bereits."
        )
    try:
        created_contact = crud.create_contact(db=db, contact=contact)
        if created_contact is None:
            raise HTTPException(status_code=500, detail="Kontakt konnte nicht erstellt werden.")
        return created_contact
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Integritaetsfehler.")


@router.get("/contacts", response_model=List[contact_schemas.ContactResponse])
async def get_all_contacts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_contacts(db, skip=skip, limit=limit)


@router.get("/contacts/{contact_id}", response_model=contact_schemas.ContactResponse)
async def get_contact_details(contact_id: int, db: Session = Depends(get_db)):
    db_contact = crud.get_contact(db, contact_id=contact_id)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Kontakt nicht gefunden")
    return db_contact


@router.get("/contacts/{contact_id}/proposals", response_model=List[Dict[str, Any]])
async def get_contact_proposals(
    contact_id: int,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    db_contact = crud.get_contact(db, contact_id=contact_id)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Kontakt nicht gefunden")
    return crud.list_contact_proposals(db, contact_id=contact_id, status=status)


@router.put("/contacts/{contact_id}", response_model=contact_schemas.ContactResponse)
async def update_contact_details(
    contact_id: int, contact: contact_schemas.ContactUpdate, db: Session = Depends(get_db)
):
    update_data = contact.model_dump(exclude_unset=True)
    db_contact = crud.update_contact(db, contact_id=contact_id, updates=update_data)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Kontakt nicht gefunden")
    refreshed_contact = crud.get_contact(db, contact_id=contact_id)
    if refreshed_contact is None:
        raise HTTPException(status_code=404, detail="Kontakt nicht gefunden")
    return refreshed_contact


@router.delete("/contacts/{contact_id}")
async def delete_contact_entry(contact_id: int, db: Session = Depends(get_db)):
    success = crud.delete_contact(db, contact_id=contact_id)
    if not success:
        raise HTTPException(status_code=404, detail="Kontakt nicht gefunden")
    return {"message": "Kontakt erfolgreich geloescht"}
