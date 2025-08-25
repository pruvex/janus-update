import logging
import datetime
import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, func
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from .utils.paths import get_app_data_dir

logger = logging.getLogger('janus_backend')

# --- Haupt-Datenbank für Chats und Memory ---
DB_PATH = os.path.join(get_app_data_dir(), 'chat_history.db')
DATABASE_URL = f"sqlite:///{DB_PATH}"
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
COSTS_DB_PATH = os.path.join(get_app_data_dir(), 'costs.db')
COSTS_DATABASE_URL = f"sqlite:///{COSTS_DB_PATH}"
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
    try:
        total_cost = db.query(func.sum(Cost.total_cost)).filter(
            func.strftime('%Y', Cost.date) == str(year),
            func.strftime('%m', Cost.date) == str(month).zfill(2)
        ).scalar()
        return total_cost if total_cost is not None else 0.0
    finally:
        db.close()

def get_costs_summary_by_model_for_current_month():
    db = CostsSessionLocal()
    try:
        today = datetime.datetime.now()
        current_month_costs = db.query(Cost).filter(
            func.strftime('%Y', Cost.date) == str(today.year),
            func.strftime('%m', Cost.date) == str(today.month).zfill(2)
        ).all()

        summary = {}
        for cost_entry in current_month_costs:
            model_name = cost_entry.model
            if model_name not in summary:
                summary[model_name] = {
                    "model": model_name,
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                    "image_count": 0,
                    "total_cost": 0.0
                }
            
            summary[model_name]["total_cost"] += cost_entry.total_cost

            if cost_entry.input_tokens is not None:
                summary[model_name]["total_input_tokens"] += cost_entry.input_tokens
            if cost_entry.output_tokens is not None:
                summary[model_name]["total_output_tokens"] += cost_entry.output_tokens
            if cost_entry.image_cost is not None and cost_entry.image_cost > 0:
                summary[model_name]["image_count"] += 1 # Assuming 1 image per entry if image_cost > 0

        return list(summary.values())
    finally:
        db.close()
    
def save_cost_entry(date, model, input_tokens, output_tokens, image_quality, image_cost, total_cost):
    db = CostsSessionLocal()
    new_cost = Cost(
        date=date, model=model, input_tokens=input_tokens, output_tokens=output_tokens,
        image_quality=image_quality, image_cost=image_cost, total_cost=total_cost
    )
    db.add(new_cost)
    db.commit()
    db.close()