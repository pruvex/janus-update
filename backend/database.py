import sqlite3
import os
import logging
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

logger = logging.getLogger('janus_backend')

# --- Kosten-Datenbank (bestehend) ---
COSTS_DATABASE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "costs.db")

# --- Chat-Datenbank (neu) ---
CHAT_DATABASE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{CHAT_DATABASE_FILE}"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- SQLAlchemy Modelle für Chat-Historie ---
class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship("Message", back_populates="chat")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"))
    sender = Column(String)
    content = Column(String)
    image_path = Column(String, nullable=True) # NEU: Pfad zum lokal gespeicherten Bild
    timestamp = Column(DateTime, default=datetime.utcnow)

    chat = relationship("Chat", back_populates="messages")

# --- Datenbank-Initialisierung ---
def init_db():
    # Initialisiere Kosten-Datenbank (bestehend)
    conn_costs = sqlite3.connect(COSTS_DATABASE_FILE)
    cursor_costs = conn_costs.cursor()
    cursor_costs.execute("""
        CREATE TABLE IF NOT EXISTS costs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            model TEXT NOT NULL,
            input_tokens INTEGER,
            output_tokens INTEGER,
            image_quality TEXT,
            image_cost REAL,
            total_cost REAL NOT NULL
        )
    """)
    conn_costs.commit()
    conn_costs.close()
    logger.info("Costs database initialized.")

    # Initialisiere Chat-Datenbank (neu)
    Base.metadata.create_all(bind=engine)
    logger.info("Chat database initialized.")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Bestehende Funktionen für Kosten-Datenbank ---
def save_cost_entry(date: str, model: str, input_tokens: int, output_tokens: int, image_quality: str, image_cost: float, total_cost: float):
    conn = sqlite3.connect(COSTS_DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO costs (date, model, input_tokens, output_tokens, image_quality, image_cost, total_cost)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (date, model, input_tokens, output_tokens, image_quality, image_cost, total_cost))
    conn.commit()
    conn.close()
    

def get_costs_for_month(year: int, month: int) -> float:
    conn = sqlite3.connect(COSTS_DATABASE_FILE)
    cursor = conn.cursor()
    # Query to sum total_cost for the given month and year
    cursor.execute("""
        SELECT SUM(total_cost) FROM costs
        WHERE STRFTIME('%Y', date) = ? AND STRFTIME('%m', date) = ?
    """, (str(year), f"{month:02d}"))
    total_cost = cursor.fetchone()[0]
    conn.close()
    return total_cost if total_cost is not None else 0.0

def get_all_cost_entries():
    conn = sqlite3.connect(COSTS_DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT date, model, input_tokens, output_tokens, image_quality, image_cost, total_cost
        FROM costs
        ORDER BY date DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    
    
    # Convert rows to a list of dictionaries for easier processing
    results = []
    for row in rows:
        results.append({
            "date": row[0],
            "model": row[1],
            "input_tokens": row[2],
            "output_tokens": row[3],
            "image_quality": row[4],
            "image_cost": row[5],
            "total_cost": row[6]
        })
    return results

def get_costs_summary_by_model_for_current_month():
    conn = sqlite3.connect(COSTS_DATABASE_FILE)
    try:
        c = conn.cursor()
        first_day_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        c.execute('''
            SELECT 
                model,
                SUM(input_tokens) as total_input,
                SUM(output_tokens) as total_output,
                SUM(CASE WHEN image_quality IS NOT NULL THEN 1 ELSE 0 END) as image_count,
                SUM(total_cost) as total_cost
            FROM costs
            WHERE date >= ?
            GROUP BY model
        ''', (first_day_of_month,))
        
        summary = []
        for row in c.fetchall():
            summary.append({
                "model": row[0],
                "total_input_tokens": row[1] or 0,
                "total_output_tokens": row[2] or 0,
                "image_count": row[3] or 0,
                "total_cost": row[4] or 0
            })
        return summary
    finally:
        conn.close()