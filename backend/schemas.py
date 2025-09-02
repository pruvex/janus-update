from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

# --- Tool Schemas ---
class GenerateImageToolArgs(BaseModel):
    prompt: str
    size: Optional[str] = "1024x1024"
    quality: Optional[str] = "standard"
    response_format: Optional[str] = "url"

class CrossChatMemoryToolArgs(BaseModel):
    query: str

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

class Chat(ChatBase):
    id: int
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True

class ChatResponse(ChatBase):
    id: int
    title: str
    created_at: datetime
    is_archived: bool

    class Config:
        from_attributes = True

class ChatTitleUpdate(BaseModel):
    title: str
