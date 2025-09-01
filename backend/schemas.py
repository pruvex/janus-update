from pydantic import BaseModel
from typing import Optional, List

# --- Tool Schemas ---
class GenerateImageToolArgs(BaseModel):
    prompt: str
    size: Optional[str] = "1024x1024"
    quality: Optional[str] = "standard"
    response_format: Optional[str] = "url"


class Message(BaseModel):
    id: int
    chat_id: int
    role: str
    content: str
    timestamp: str

    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    id: int
    chat_id: int
    role: str
    content: str
    timestamp: str

    class Config:
        from_attributes = True

class ChatBase(BaseModel):
    title: str

class ChatCreate(ChatBase):
    pass

class Chat(ChatBase):
    id: int
    created_at: str
    updated_at: str
    messages: List[Message] = []

    class Config:
        from_attributes = True

class ChatResponse(BaseModel):
    id: int
    title: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class ChatTitleUpdate(BaseModel):
    title: str
