from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

# --- Message Schemas ---
class MessageBase(BaseModel):
    sender: str
    content: str
    image_path: Optional[str] = None

class MessageCreate(MessageBase):
    pass

class MessageResponse(MessageBase):
    id: int
    chat_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

# --- Chat Schemas ---
class ChatBase(BaseModel):
    title: str

class ChatCreate(ChatBase):
    pass

class ChatResponse(ChatBase):
    id: int
    created_at: datetime
    is_archived: bool

    class Config:
        from_attributes = True