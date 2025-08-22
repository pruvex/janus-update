import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base, Chat

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    # Erstelle alle Tabellen
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
        
    # Erstelle einen Dummy-Chat für Tests, die eine existierende Chat-ID benötigen
    dummy_chat = Chat(title="Dummy Chat")
    db.add(dummy_chat)
    db.commit()
    db.refresh(dummy_chat)
    db.dummy_chat_id = dummy_chat.id
        
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)