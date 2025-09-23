from pydantic import BaseModel, Field
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

# In backend/schemas.py (ersetzen Sie den gesamten Filesystem-Block)
# --- Filesystem Tool Schemas ---
class CreateFileArgs(BaseModel):
    path: str
    content: Optional[str] = ""

class ReadFileArgs(BaseModel):
    path: str

class DeleteFileArgs(BaseModel):
    path: str

# ERWEITERT: Füge einen optionalen Pattern-Parameter hinzu
class ListDirectoryArgs(BaseModel):
    path: str
    pattern: Optional[str] = None

class CreateDirectoryArgs(BaseModel):
    path: str

class DeleteDirectoryArgs(BaseModel):
    path: str

class MoveFileArgs(BaseModel):
    source_path: str
    destination_path: str

class RenameFileArgs(BaseModel):
    old_path: str
    new_path: str
    
class MoveFilesArgs(BaseModel):
    source_directory: str
    destination_directory: str
    pattern: str

class ListAllowedWorkspacesArgs(BaseModel):
    pass

class WebsearchToolArgs(BaseModel):
    query: str
    model: Optional[str] = None # Add model parameter

# Am Ende von backend/schemas.py hinzufügen

class CreatePdfFromMarkdownArgs(BaseModel):
    content: str = Field(..., description="Der Inhalt der PDF-Datei im Markdown-Format.")
    filename: str = Field(..., description="Der gewünschte Dateiname (z.B. 'zusammenfassung.pdf').")
    location: Optional[str] = Field("Documents", description="Der Speicherort. Mögliche Werte: 'Desktop', 'Documents', 'Downloads'. Standard ist 'Documents'.")
    include_image: Optional[bool] = Field(False, description="Setze dies auf 'true', wenn das letzte Bild aus dem Chatverlauf in die PDF eingefügt werden soll.")