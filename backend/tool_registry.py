# backend/tool_registry.py
import inspect
from typing import Callable, Dict, Any, Optional
from pydantic import BaseModel
from backend import llm_gateway, schemas

class Tool:
    def __init__(self, func: Callable, args_schema: BaseModel):
        self.func = func
        self.args_schema = args_schema
        self.name = func.__name__
        self.description = inspect.getdoc(func)
        self.llm_definition = self._build_llm_definition()

    def _build_llm_definition(self) -> Dict[str, Any]:
        schema = self.args_schema.model_json_schema()
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": schema.get("properties", {}),
                    "required": schema.get("required", []),
                },
            },
        }

TOOL_REGISTRY: Dict[str, Tool] = {}

def register_tool(tool: Tool):
    TOOL_REGISTRY[tool.name] = tool

async def generate_image_tool(api_key: str, prompt: str, size: str = "1024x1024", quality: str = "standard", response_format: str = "url"):
    """
    Generates an image based on a text prompt using DALL-E 3.
    Use this tool whenever a user asks to create, draw, or generate an image.
    """
    return await llm_gateway.generate_image_tool(
        api_key=api_key, prompt=prompt, size=size, quality=quality, response_format=response_format
    )

register_tool(Tool(func=generate_image_tool, args_schema=schemas.GenerateImageToolArgs))

def get_all_tool_definitions():
    return [tool.llm_definition for tool in TOOL_REGISTRY.values()]
