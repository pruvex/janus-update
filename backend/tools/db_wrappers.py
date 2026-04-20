import logging
import time

from backend.data import contact_schemas, crud, database
from backend.data.schemas_tools import ToolResultV1
from backend.services import contact_manager
from backend.tools.tool_contract_v1 import tool_err_v1, tool_ok_v1

logger = logging.getLogger("janus_backend")


def list_contacts_wrapper() -> ToolResultV1:
    started_at = time.perf_counter()
    try:
        rows = contact_manager.list_contacts()
        contacts = [c.model_dump(mode="json") for c in rows]
        return tool_ok_v1(
            {"contacts": contacts, "count": len(contacts)},
            message=f"{len(contacts)} Kontakt(e) geladen.",
            tags=["contacts"],
            started_at=started_at,
            suggest_follow_up=len(contacts) > 0,
        )
    except Exception as e:
        logger.error("list_contacts_wrapper failed", exc_info=True)
        return tool_err_v1(
            "CONTACTS_LIST_FAILED",
            str(e),
            started_at=started_at,
            tags=["contacts"],
        )


def delete_contact_by_id_wrapper(contact_id: int) -> ToolResultV1:
    started_at = time.perf_counter()
    try:
        raw = contact_manager.delete_contact_by_id(contact_id=contact_id)
        if raw.get("success"):
            return tool_ok_v1(
                {"contact_id": contact_id, "deleted": True},
                message=raw.get("message"),
                tags=["contacts"],
                started_at=started_at,
                primary_entity_id=str(contact_id),
            )
        return tool_err_v1(
            "NOT_FOUND",
            raw.get("message") or f"Kontakt mit ID {contact_id} nicht gefunden.",
            details={"contact_id": contact_id},
            started_at=started_at,
            tags=["contacts"],
        )
    except Exception as e:
        logger.error("delete_contact_by_id_wrapper failed", exc_info=True)
        return tool_err_v1(
            "CONTACT_DELETE_FAILED",
            str(e),
            details={"contact_id": contact_id},
            started_at=started_at,
            tags=["contacts"],
        )


async def create_or_update_contact_tool(name: str, **kwargs) -> ToolResultV1:
    started_at = time.perf_counter()
    db = next(database.get_db_sync())
    try:
        existing = crud.search_contacts_by_name(db, name_query=name)
        updates = {k: v for k, v in kwargs.items() if v is not None}

        if existing:
            contact = crud.update_contact(db, existing[0].id, updates)
            payload = contact_schemas.ContactResponse.model_validate(contact).model_dump(mode="json")
            return tool_ok_v1(
                {"contact": payload, "action": "updated"},
                message=f"Kontakt '{contact.name}' aktualisiert.",
                tags=["contacts"],
                started_at=started_at,
                primary_entity_id=str(contact.id),
            )
        data = contact_schemas.ContactCreate(name=name, **updates)
        contact = crud.create_contact(db, data)
        payload = contact_schemas.ContactResponse.model_validate(contact).model_dump(mode="json")
        return tool_ok_v1(
            {"contact": payload, "action": "created"},
            message=f"Kontakt '{contact.name}' erstellt.",
            tags=["contacts"],
            started_at=started_at,
            primary_entity_id=str(contact.id),
        )
    except Exception as e:
        logger.error("create_or_update_contact_tool failed", exc_info=True)
        return tool_err_v1(
            "CONTACT_UPSERT_FAILED",
            str(e),
            started_at=started_at,
            tags=["contacts"],
        )
    finally:
        db.close()
