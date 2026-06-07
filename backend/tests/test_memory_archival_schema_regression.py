from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.data.database import Base
from backend.data import models


def test_memory_archive_metadata_fields_are_supported():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    chat = models.Chat(title="Archive Test Chat")
    db.add(chat)
    db.commit()

    archived = models.Memory(
        chat_id=chat.id,
        snippet="archived snippet",
        original_memory_id=42,
        archived_at=datetime.utcnow(),
    )
    db.add(archived)
    db.commit()
    db.refresh(archived)

    reloaded = db.query(models.Memory).filter(models.Memory.id == archived.id).first()

    assert reloaded is not None
    assert reloaded.original_memory_id == 42
    assert reloaded.archived_at is not None

    db.close()
