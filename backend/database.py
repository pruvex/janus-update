import logging
import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

logger = logging.getLogger('janus_backend')

# --- Haupt-Datenbank für Chats und Memory ---
DATABASE_URL = "sqlite:///./chat_history.db"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Modelle ---
class Chat(Base):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, default="New Chat")
    created_at = Column(DateTime, default=datetime.datetime.now)
    is_archived = Column(Boolean, default=False)
    summary = Column(Text, nullable=True)
    summary_embedding_json = Column(Text, nullable=True)
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"))
    sender = Column(String)
    content = Column(Text)
    image_path = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.now)
    chat = relationship("Chat", back_populates="messages")

class Memory(Base):
    __tablename__ = "memory"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"))
    snippet = Column(Text, nullable=False)
    embedding_json = Column(Text, nullable=True) # Die wichtige Spalte
    created_at = Column(DateTime, default=datetime.datetime.now)

# --- Kosten-Datenbank ---
COSTS_DATABASE_URL = "sqlite:///./costs.db"
costs_engine = create_engine(COSTS_DATABASE_URL, connect_args={"check_same_thread": False})
CostsSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=costs_engine)
CostsBase = declarative_base()

class Cost(CostsBase):
    __tablename__ = "costs"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.datetime.now)
    model = Column(String)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    image_quality = Column(String, nullable=True)
    image_cost = Column(Float, nullable=True)
    total_cost = Column(Float)

# --- Initialisierungs-Funktion ---
def init_db():
    try:
        # Erstellt alle Tabellen für Chat/Memory und Kosten
        Base.metadata.create_all(bind=engine)
        CostsBase.metadata.create_all(bind=costs_engine)
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

# --- Kosten-spezifische DB-Funktionen ---
def get_costs_for_month(year, month):
    db = CostsSessionLocal()
    # Implementierung hier ... (angenommen, sie ist korrekt)
    return 0.0

def get_costs_summary_by_model_for_current_month():
    db = CostsSessionLocal()
    # Implementierung hier ...
    return []
    
def save_cost_entry(date, model, input_tokens, output_tokens, image_quality, image_cost, total_cost):
    db = CostsSessionLocal()
    new_cost = Cost(
        date=date, model=model, input_tokens=input_tokens, output_tokens=output_tokens,
        image_quality=image_quality, image_cost=image_cost, total_cost=total_cost
    )
    db.add(new_cost)
    db.commit()
    db.close()