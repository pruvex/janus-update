from backend.data import contact_schemas, crud, database
from backend.services import contact_manager


# Kontakt-Wrapper mit Session-Management
def list_contacts_wrapper() -> dict:
    db = next(database.get_db())
    try:
        return contact_manager.list_contacts(db=db)
    finally:
        db.close()


def delete_contact_by_id_wrapper(contact_id: int) -> dict:
    db = next(database.get_db())
    try:
        return contact_manager.delete_contact_by_id(db=db, contact_id=contact_id)
    finally:
        db.close()


async def create_or_update_contact_tool(name: str, **kwargs) -> dict:
    db = next(database.get_db())
    try:
        existing = crud.search_contacts_by_name(db, name_query=name)
        updates = {k: v for k, v in kwargs.items() if v is not None}

        if existing:
            contact = crud.update_contact(db, existing[0].id, updates)
            return {"status": "success", "message": f"Kontakt '{contact.name}' aktualisiert."}
        else:
            data = contact_schemas.ContactCreate(name=name, **updates)
            contact = crud.create_contact(db, data)
            return {"status": "success", "message": f"Kontakt '{contact.name}' erstellt."}
    finally:
        db.close()
