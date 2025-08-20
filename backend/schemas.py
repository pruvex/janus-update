from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class MessageBase(BaseModel):
    sender: str
    content: str
    image_path: Optional[str] = None # NEU: Pfad zum lokal gespeicherten Bild

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: int
    chat_id: int # NEU: Foreign Key
    timestamp: datetime

    class Config:
        from_attributes = True

class ChatBase(BaseModel):
    title: Optional[str] = "New Chat"

class ChatCreate(ChatBase):
    pass

class Chat(ChatBase):
    id: int
    created_at: datetime
    messages: List[Message] = []

    class Config:
        from_attributes = True