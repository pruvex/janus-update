from fastapi import APIRouter, HTTPException
import httpx
import os
import json
from openai import OpenAI
import logging
import traceback





router = APIRouter()

async def _call_dalle_api(api_key: str, prompt: str, quality: str):
    client = OpenAI(api_key=api_key)
    
    response = client.images.generate(
        model="dall-e-3", # DALL-E 3 is the model for image generation
        prompt=prompt,
        size="1024x1024",
        quality=quality, # Use the passed quality
        n=1,
    )
    image_url = response.data[0].url
    return image_url # Return just the URL

# Tool definition for DALL-E
dalle_tool = {
    "type": "function",
    "function": {
        "name": "generate_image",
        "description": "Generiert ein Bild aus einer Textbeschreibung.",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Die Textbeschreibung des zu generierenden Bildes."
                },
                "quality": {
                    "type": "string",
                    "enum": ["standard", "hd"],
                    "description": "Die Qualität des Bildes. 'standard' ist schneller und günstiger, 'hd' bietet höhere Detailgenauigkeit."
                }
            },
            "required": ["prompt"]
        }
    }
}

# New function for OpenAI Chat Completion API calls
async def _call_chat_completion_api(api_key: str, prompt: str, model: str):
    client = OpenAI(api_key=api_key)
    
    messages = [{"role": "user", "content": prompt}]
    
    # Pass the tool definition to the API call
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=[dalle_tool], # Pass the tool here
        tool_choice="auto", # Allow the model to decide whether to use the tool
    )

    response_message = response.choices[0].message
    
    # Check if the model wants to call a tool
    if response_message.tool_calls:
        tool_call = response_message.tool_calls[0] # Assuming one tool call for simplicity
        function_name = tool_call.function.name
        
        if function_name == "generate_image":
            # Parse arguments
            function_args = json.loads(tool_call.function.arguments)
            image_prompt = function_args.get("prompt")
            image_quality = function_args.get("quality", "standard") # Default to standard
            
            # Call the DALL-E API
            image_url = await _call_dalle_api(api_key, image_prompt, image_quality)
            
            # Send the tool's response back to the model
            messages.append(response_message)
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": image_url,
                }
            )
            
            # Get the final response from the model
            second_response = client.chat.completions.create(
                model=model,
                messages=messages,
            )
            final_message_content = second_response.choices[0].message.content
            # If an image was generated, ensure the text content does not contain the image URL.
            if image_url:
                final_message_content = "Hier ist das Bild, das mit DALL·E 3 erstellt wurde."
            return {"text": final_message_content, "image_url": image_url}
    
    # If no tool call, return the regular chat response
    chat_response_text = response_message.content
    return {"text": chat_response_text} # Return as JSON object





async def call_llm(provider: str, model: str, prompt: str, api_key: str):
    print(f"Call LLM - Provider: {provider}, Model: {model}")
    if provider == "openai":
        return await _call_chat_completion_api(api_key, prompt, model)
    
    elif provider == "gemini":
            # Existing Gemini Chat Logic
        url = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, json=payload, timeout=30)
                response.raise_for_status()
                gemini_response = response.json()

                if "candidates" in gemini_response and gemini_response["candidates"]:
                    if "content" in gemini_response["candidates"][0] and "parts" in gemini_response["candidates"][0]["content"] and gemini_response["candidates"][0]["content"]["parts"]:
                        chat_response_text = gemini_response["candidates"][0]["content"]["parts"][0].get("text", "")
                        return {"text": chat_response_text}

                raise HTTPException(status_code=500, detail="Unerwartetes Antwortformat von der Gemini-API.")

            except httpx.RequestError as e:
                raise HTTPException(status_code=500, detail=f"Fehler bei der Kommunikation mit der Gemini-API: {e}")
            except json.JSONDecodeError:
                raise HTTPException(status_code=500, detail="Fehler beim Parsen der Gemini-API-Antwort.")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Ein unerwarteter Fehler ist aufgetreten: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="Unsupported provider.")

@router.get("/config")
async def get_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if not os.path.exists(config_path):
        raise HTTPException(status_code=404, detail="Config file not found.")
    with open(config_path, "r") as f:
        config = json.load(f)
    return config
