from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


def _normalize_string_list(value: Optional[object]) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        normalized = value.replace("\r", "\n").replace(",", "\n")
        return [item.strip() for item in normalized.split("\n") if item.strip()]
    text = str(value).strip()
    return [text] if text else []


class ContactBase(BaseModel):
    name: str = Field(..., description="Der vollstaendige Name des Kontakts.")
    nickname: Optional[str] = Field(None, description="Ein optionaler Kurz- oder Spitzname des Kontakts.")
    contact_type: str = Field(
        "private_person",
        description="Die Art des Kontakts: 'private_person' oder 'organization'.",
    )
    category: Optional[str] = Field(
        "Unkategorisiert",
        description="Eine Kategorie fuer den Kontakt (z.B. 'Familie', 'Arzt', 'Arbeit').",
    )
    email: Optional[str] = Field(None, description="Die primaere E-Mail-Adresse des Kontakts.")
    phone: Optional[str] = Field(None, description="Die primaere Telefonnummer des Kontakts.")
    address: Optional[str] = Field(None, description="Die physische Adresse des Kontakts.")
    website: Optional[str] = Field(None, description="Die Website oder URL des Kontakts.")
    preferences: List[str] = Field(
        default_factory=list,
        description="Strukturierte Vorlieben des Kontakts.",
    )
    dislikes: List[str] = Field(
        default_factory=list,
        description="Strukturierte Abneigungen des Kontakts.",
    )
    personal_details: List[str] = Field(
        default_factory=list,
        description="Weitere strukturierte, bestaetigte Kontaktdetails.",
    )
    notes: Optional[str] = Field(None, description="Zusaetzliche Notizen zum Kontakt.")
    proposal_status: str = Field(
        "confirmed",
        description="Vorschlagsstatus des Kontakts, z.B. 'confirmed' oder 'pending'.",
    )
    proposal_source_context: Optional[str] = Field(
        None,
        description="Kurzer Herkunftskontext fuer Kontakt- oder Update-Vorschlaege.",
    )
    proposal_last_outcome: Optional[str] = Field(
        None,
        description="Zuletzt dokumentiertes Ergebnis eines Kontaktvorschlags.",
    )
    memory_sync_status: str = Field(
        "unlinked",
        description="Status der Memory-Kopplung fuer diesen Kontakt.",
    )

    @field_validator("preferences", "dislikes", "personal_details", mode="before")
    @classmethod
    def _normalize_lists(cls, value: Optional[object]) -> List[str]:
        return _normalize_string_list(value)

    @field_validator("contact_type", "proposal_status", "memory_sync_status", mode="before")
    @classmethod
    def _default_required_strings(cls, value: Optional[object], info) -> str:
        if value is None or not str(value).strip():
            defaults = {
                "contact_type": "private_person",
                "proposal_status": "confirmed",
                "memory_sync_status": "unlinked",
            }
            return defaults[info.field_name]
        return str(value).strip()


class ContactCreate(ContactBase):
    pass


class ContactResponse(ContactBase):
    id: int
    created_at: datetime

    @field_serializer("created_at")
    def serialize_dt(self, dt: datetime, _info):
        return dt.isoformat()

    model_config = ConfigDict(
        from_attributes=True,
    )


class ContactExtractionArgs(BaseModel):
    text: str = Field(
        ...,
        description="Der Textblock, aus dem Kontaktinformationen extrahiert werden sollen, z.B. eine E-Mail-Signatur oder eine Visitenkarte.",
    )


class ContactListArgs(BaseModel):
    pass


class ContactSearchArgs(BaseModel):
    name_query: str = Field(
        ...,
        description="Der Name oder Teil des Namens, nach dem in den Kontakten gesucht werden soll.",
    )


class ContactUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Der neue vollstaendige Name des Kontakts.")
    nickname: Optional[str] = Field(None, description="Der neue Kurz- oder Spitzname des Kontakts.")
    contact_type: Optional[str] = Field(None, description="Die Art des Kontakts.")
    category: Optional[str] = Field(None, description="Die neue Kategorie fuer den Kontakt.")
    email: Optional[str] = Field(None, description="Die neue E-Mail-Adresse des Kontakts.")
    phone: Optional[str] = Field(None, description="Die neue Telefonnummer des Kontakts.")
    address: Optional[str] = Field(None, description="Die neue physische Adresse des Kontakts.")
    website: Optional[str] = Field(None, description="Die neue Website oder URL des Kontakts.")
    preferences: Optional[List[str]] = Field(None, description="Die neuen strukturierten Vorlieben.")
    dislikes: Optional[List[str]] = Field(None, description="Die neuen strukturierten Abneigungen.")
    personal_details: Optional[List[str]] = Field(
        None, description="Neue strukturierte Kontaktdetails."
    )
    notes: Optional[str] = Field(None, description="Die neuen Notizen zum Kontakt.")
    proposal_status: Optional[str] = Field(None, description="Der neue Vorschlagsstatus.")
    proposal_source_context: Optional[str] = Field(
        None, description="Der neue Herkunftskontext eines Vorschlags."
    )
    proposal_last_outcome: Optional[str] = Field(
        None, description="Das neue Ergebnis des letzten Vorschlags."
    )
    memory_sync_status: Optional[str] = Field(
        None, description="Der neue Memory-Kopplungsstatus."
    )

    @field_validator("preferences", "dislikes", "personal_details", mode="before")
    @classmethod
    def _normalize_optional_lists(cls, value: Optional[object]) -> Optional[List[str]]:
        if value is None:
            return None
        return _normalize_string_list(value)


class ContactUpdateArgs(BaseModel):
    contact_id: int = Field(..., description="Die ID des zu aktualisierenden Kontakts.")
    updates: ContactUpdate = Field(
        ..., description="Die zu aktualisierenden Felder und ihre neuen Werte."
    )


class ContactDeleteArgs(BaseModel):
    contact_id: int = Field(..., description="Die ID des zu loeschenden Kontakts.")


class UpdateContactToolArgs(BaseModel):
    """Argumente zum Suchen und Aktualisieren eines bestehenden Kontakts."""

    name_query: str = Field(
        ..., description="Der exakte Name des Kontakts, der aktualisiert werden soll."
    )
    new_name: Optional[str] = Field(
        None, description="Der neue vollstaendige Name des Kontakts, falls er geaendert werden soll."
    )
    nickname: Optional[str] = Field(None, description="Der neue Kurz- oder Spitzname des Kontakts.")
    contact_type: Optional[str] = Field(None, description="Die Art des Kontakts.")
    category: Optional[str] = Field(None, description="Die neue Kategorie fuer den Kontakt.")
    email: Optional[str] = Field(None, description="Die neue E-Mail-Adresse des Kontakts.")
    phone: Optional[str] = Field(None, description="Die neue Telefonnummer des Kontakts.")
    address: Optional[str] = Field(None, description="Die neue physische Adresse des Kontakts.")
    website: Optional[str] = Field(None, description="Die neue Website oder URL des Kontakts.")
    preferences: Optional[List[str]] = Field(None, description="Neue strukturierte Vorlieben.")
    dislikes: Optional[List[str]] = Field(None, description="Neue strukturierte Abneigungen.")
    personal_details: Optional[List[str]] = Field(
        None, description="Neue strukturierte Kontaktdetails."
    )
    notes: Optional[str] = Field(
        None, description="Die neuen oder zu ergaenzenden Notizen zum Kontakt."
    )
    proposal_status: Optional[str] = Field(None, description="Der neue Vorschlagsstatus.")
    proposal_source_context: Optional[str] = Field(
        None, description="Der neue Herkunftskontext eines Vorschlags."
    )
    proposal_last_outcome: Optional[str] = Field(
        None, description="Das neue Ergebnis des letzten Vorschlags."
    )
    memory_sync_status: Optional[str] = Field(
        None, description="Der neue Memory-Kopplungsstatus."
    )


class CreateOrUpdateContactArgs(BaseModel):
    """Argumente zum Erstellen oder Aktualisieren eines Kontakts."""

    name: str = Field(..., description="Der vollstaendige Name des Kontakts.")
    nickname: Optional[str] = Field(None, description="Ein optionaler Kurz- oder Spitzname des Kontakts.")
    contact_type: Optional[str] = Field(None, description="Die Art des Kontakts.")
    email: Optional[str] = Field(None, description="Die E-Mail-Adresse des Kontakts.")
    phone: Optional[str] = Field(None, description="Die Telefonnummer des Kontakts.")
    address: Optional[str] = Field(None, description="Die physische Adresse des Kontakts.")
    website: Optional[str] = Field(None, description="Die Website oder URL des Kontakts.")
    preferences: Optional[List[str]] = Field(None, description="Strukturierte Vorlieben.")
    dislikes: Optional[List[str]] = Field(None, description="Strukturierte Abneigungen.")
    personal_details: Optional[List[str]] = Field(
        None, description="Weitere strukturierte Kontaktdetails."
    )
    notes: Optional[str] = Field(None, description="Zusaetzliche Notizen zum Kontakt.")
    category: Optional[str] = Field(
        "Privat", description="Die Kategorie des Kontakts, z.B. 'Privat' oder 'Business'."
    )
    proposal_status: Optional[str] = Field(None, description="Der Vorschlagsstatus.")
    proposal_source_context: Optional[str] = Field(
        None, description="Der Herkunftskontext eines Vorschlags."
    )
    proposal_last_outcome: Optional[str] = Field(
        None, description="Das Ergebnis des letzten Vorschlags."
    )
    memory_sync_status: Optional[str] = Field(
        None, description="Der Memory-Kopplungsstatus."
    )
