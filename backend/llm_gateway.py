from fastapi import APIRouter, HTTPException
import httpx
import os
import json
import openai # Changed from 'from openai import OpenAI'
import logging
import traceback
import re # Added for potential future use, not in current snippet but good practice

router = APIRouter()

# Existing _call_dalle_api (renamed to _call_dalle_api_old to avoid conflict)
# This will be removed later or adapted if needed.
async def _call_dalle_api_old(api_key: str, prompt: str, quality: str):
    client = openai.OpenAI(api_key=api_key) # Use openai.OpenAI
    
    response = client.images.generate(
        model="dall-e-3", # DALL-E 3 is the model for image generation
        prompt=prompt,
        size="1024x1024",
        quality=quality, # Use the passed quality
        n=1,
    )
    image_url = response.data[0].url
    return image_url # Return just the URL

# Tool definition for DALL-E (remains as is)
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

# Refactored _call_chat_completion_api to _call_openai_api
async def _call_openai_api(api_key: str, prompt: str, model: str):
    async with openai.AsyncOpenAI(api_key=api_key) as client:
        messages = [{"role": "user", "content": prompt}]
        
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            tools=[dalle_tool], # Re-add tool call
            tool_choice="auto", # Re-add tool call
        )

        response_message = response.choices[0].message
        
        if response_message.tool_calls:
            tool_call = response_message.tool_calls[0]
            function_name = tool_call.function.name
            
            if function_name == "generate_image":
                function_args = json.loads(tool_call.function.arguments)
                image_prompt = function_args.get("prompt")
                image_quality = function_args.get("quality", "standard")
                
                # Call the NEW _call_dalle_api
                dalle_response = await _call_dalle_api(api_key, image_prompt, f"dall-e-3-{image_quality}") # Pass model for quality
                
                messages.append(response_message)
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": json.dumps({"image_url": dalle_response.get("image_url")}), # Use image_url from new dalle_response
                    }
                )
                
                second_response = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                )
                final_message_content = second_response.choices[0].message.content
                
                print(f"DEBUG (_call_openai_api): dalle_response.get('image_url') = {dalle_response.get('image_url')}")
                return {
                    "text": final_message_content,
                    "image_url": dalle_response.get("image_url"), # This is correct!
                    "usage": dalle_response.get("usage"),
                    "cost": dalle_response.get("cost")
                }
        
        chat_response_text = response_message.content
        return {"text": chat_response_text}

# Refactored Gemini Chat Logic to _call_gemini_api
async def _call_gemini_api(api_key: str, prompt: str, model: str):
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
                    
                    # Estimate token usage
                    input_tokens = len(prompt.split())
                    output_tokens = len(chat_response_text.split())

                    return {
                        "text": chat_response_text,
                        "usage": {
                            "input_tokens": input_tokens,
                            "output_tokens": output_tokens
                        }
                    }

            raise HTTPException(status_code=500, detail="Unerwartetes Antwortformat von der Gemini-API.")

        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Fehler bei der Kommunikation mit der Gemini-API: {e}")
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Fehler beim Parsen der Gemini-API-Antwort.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ein unerwarteter Fehler ist aufgetreten: {str(e)}")

# NEW, DEDICATED FUNCTION FOR DALL-E (from user's plan)
async def _call_dalle_api(api_key, prompt, model_id): # Renamed 'model' to 'model_id' to avoid conflict with client.images.generate(model=...)
    client = openai.AsyncOpenAI(api_key=api_key)
        
    quality = "standard"
    if model_id == "dall-e-3-hd":
        quality = "hd"
    
    try:
        response = await client.images.generate(
            model="dall-e-3", # The REAL model name
            prompt=prompt,
            n=1,
            size="1024x1024",
            quality=quality,
            response_format="url",
        )
        image_url = response.data[0].url
                
        # Create a response that our backend understands
        image_cost = 0.04 if quality == "standard" else 0.08
        print(f"DEBUG (_call_dalle_api): image_url = {image_url}")
        return {
            "text": response.data[0].revised_prompt or "Hier ist das Bild, das mit DALL·E erstellt wurde.",
            "image_url": image_url, # Direct URL
            "usage": {"image_quality": quality, "image_cost": image_cost},
            "cost": {"total_cost": image_cost}
        }
    except Exception as e:
        print(f"Error calling DALL-E API: {e}")
        raise

# Replaced call_llm with the new switch logic
async def call_llm(provider: str, model: str, prompt: str, api_key: str):
    print(f"Call LLM - Provider: {provider}, Model: {model}")
    # --- NEW SWITCH for DALL-E ---
    if model.startswith("dall-e-3"):
        return await _call_dalle_api(api_key, prompt, model) # Pass model_id for quality check
        
    if provider == "openai":
        return await _call_openai_api(api_key, prompt, model)
    elif provider == "gemini":
        return await _call_gemini_api(api_key, prompt, model)
    else:
        raise ValueError(f"Unknown provider: {provider}")

@router.get("/config")
async def get_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if not os.path.exists(config_path):
        raise HTTPException(status_code=404, detail="Config file not found.")
    with open(config_path, "r") as f:
        config = json.load(f)
    return config