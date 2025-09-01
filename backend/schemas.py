
# --- Tool Schemas ---
class GenerateImageToolArgs(BaseModel):
    prompt: str
    size: Optional[str] = "1024x1024"
    quality: Optional[str] = "standard"
    response_format: Optional[str] = "url"
