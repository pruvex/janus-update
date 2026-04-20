# backend/data/crud_vision.py
import pickle
import logging
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from backend.data.models import PersonProfile

logger = logging.getLogger("janus_backend")

def create_person_container(db: Session, name: str, features: dict = None):
    """
    Erstellt einen neuen Personen-Container ohne direktes Gesichts-Encoding.
    """
    try:
        db_person = PersonProfile(
            name=name,
            features=features or {},
            created_at=datetime.utcnow(),
            last_seen=datetime.utcnow()
        )
        db.add(db_person)
        db.commit()
        db.refresh(db_person)
        logger.info(f"VISION: Neuer Personen-Container erstellt: {name}")
        return db_person
    except Exception as e:
        logger.error(f"VISION: Fehler beim Erstellen des Personen-Containers für {name}: {e}")
        db.rollback()
        return None

def add_face_encoding(db: Session, person_id: int, encoding):
    """Fügt ein neues Gesichts-Encoding zu einer bestehenden Person hinzu."""
    from backend.data.models import FaceEncoding # Importiere hier, um Zirkelabhängigkeiten zu vermeiden
    try:
        encoding_blob = pickle.dumps(encoding)
        db_encoding = FaceEncoding(
            person_id=person_id,
            encoding=encoding_blob
        )
        db.add(db_encoding)
        db.commit()
        db.refresh(db_encoding)
        logger.info(f"VISION: Neues Encoding für Person {person_id} hinzugefügt.")
        return db_encoding
    except Exception as e:
        logger.error(f"VISION: Fehler beim Hinzufügen des Encodings für Person {person_id}: {e}")
        db.rollback()
        return None

def get_person_by_name(db: Session, name: str):
    """Sucht eine Person nach Namen."""
    return db.query(PersonProfile).filter(PersonProfile.name == name).first()

def update_last_seen(db: Session, name: str):
    """Aktualisiert den Zeitstempel, wann die Person zuletzt gesehen wurde."""
    person = get_person_by_name(db, name)
    if person:
        person.last_seen = datetime.utcnow()
        db.commit()

def get_person_fact_count(db: Session, person_name: str) -> int:
    """Gibt die Anzahl der für eine Person gespeicherten Fakten zurück."""
    from backend.data.models import Memory # Vermeide Zirkelreferenz
    return db.query(Memory).filter(
        Memory.canonical_key.like(f"{person_name.lower()}:%")
    ).count()

def get_all_known_faces(db: Session):
    known_encodings = []
    known_names = []
    persons = db.query(PersonProfile).options(joinedload(PersonProfile.encodings)).all()
    for person in persons:
        for face_encoding in person.encodings:
            known_encodings.append(pickle.loads(face_encoding.encoding))
            known_names.append(person.name)
    return known_encodings, known_names