from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer


# --- Contact Schemas ---
class ContactBase(BaseModel):
    name: str = Field(..., description="Der vollständige Name des Kontakts.")
    category: Optional[str] = Field(
        "Unkategorisiert",
        description="Eine Kategorie für den Kontakt (z.B. 'Familie', 'Arzt', 'Arbeit').",
    )
    email: Optional[str] = Field(None, description="Die primäre E-Mail-Adresse des Kontakts.")
    phone: Optional[str] = Field(None, description="Die primäre Telefonnummer des Kontakts.")
    address: Optional[str] = Field(None, description="Die physische Adresse des Kontakts.")
    website: Optional[str] = Field(None, description="Die Website oder URL des Kontakts.")
    notes: Optional[str] = Field(None, description="Zusätzliche Notizen zum Kontakt.")


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


# --- Contact Tool Schemas ---
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
    name: Optional[str] = Field(None, description="Der neue vollständige Name des Kontakts.")
    category: Optional[str] = Field(None, description="Die neue Kategorie für den Kontakt.")
    email: Optional[str] = Field(None, description="Die neue E-Mail-Adresse des Kontakts.")
    phone: Optional[str] = Field(None, description="Die neue Telefonnummer des Kontakts.")
    address: Optional[str] = Field(None, description="Die neue physische Adresse des Kontakts.")
    website: Optional[str] = Field(None, description="Die neue Website oder URL des Kontakts.")
    notes: Optional[str] = Field(None, description="Die neuen Notizen zum Kontakt.")


class ContactUpdateArgs(BaseModel):
    contact_id: int = Field(..., description="Die ID des zu aktualisierenden Kontakts.")
    updates: ContactUpdate = Field(
        ..., description="Die zu aktualisierenden Felder und ihre neuen Werte."
    )


class ContactDeleteArgs(BaseModel):
    contact_id: int = Field(..., description="Die ID des zu löschenden Kontakts.")


class UpdateContactToolArgs(BaseModel):
    """Argumente zum Suchen und Aktualisieren eines bestehenden Kontakts."""

    name_query: str = Field(
        ..., description="Der exakte Name des Kontakts, der aktualisiert werden soll."
    )
    new_name: Optional[str] = Field(
        None, description="Der neue vollständige Name des Kontakts, falls er geändert werden soll."
    )
    category: Optional[str] = Field(None, description="Die neue Kategorie für den Kontakt.")
    email: Optional[str] = Field(None, description="Die neue E-Mail-Adresse des Kontakts.")
    phone: Optional[str] = Field(None, description="Die neue Telefonnummer des Kontakts.")
    address: Optional[str] = Field(None, description="Die neue physische Adresse des Kontakts.")
    website: Optional[str] = Field(None, description="Die neue Website oder URL des Kontakts.")
    notes: Optional[str] = Field(
        None, description="Die neuen oder zu ergänzenden Notizen zum Kontakt."
    )


class CreateOrUpdateContactArgs(BaseModel):
    """Argumente zum Erstellen oder Aktualisieren eines Kontakts."""

    name: str = Field(..., description="Der vollständige Name des Kontakts.")
    email: Optional[str] = Field(None, description="Die E-Mail-Adresse des Kontakts.")
    phone: Optional[str] = Field(None, description="Die Telefonnummer des Kontakts.")
    address: Optional[str] = Field(None, description="Die physische Adresse des Kontakts.")
    notes: Optional[str] = Field(None, description="Zusätzliche Notizen zum Kontakt.")
    category: Optional[str] = Field(
        "Privat", description="Die Kategorie des Kontakts, z.B. 'Privat' oder 'Business'."
    )
