from fastapi import APIRouter, HTTPException
import httpx
import os
import json
import openai # Changed from 'from openai import OpenAI'
import logging
import traceback
import re # Added for potential future use, not in current snippet but good practice
import google.generativeai as genai
from .cost_calculator import calculate_cost

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

        # --- DEBUG-OUTPUT FÜR OPENAI ---
        if response.usage:
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            total_cost = calculate_cost(model, input_tokens, output_tokens)
            print("\n--- OPENAI USAGE TRACKING ---")
            print(f"Model: {model}")
            print(f"Input Tokens: {input_tokens}")
            print(f"Output Tokens: {output_tokens}")
            print(f"Calculated Cost: {total_cost:.6f} €")
            print("-----------------------------\\n")
        # --- ENDE DEBUG-OUTPUT ---

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

async def _call_gemini_api(api_key, prompt, model_name):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    try:
        response = await model.generate_content_async(prompt)
        usage_metadata = getattr(response, 'usage_metadata', None)
        if usage_metadata:
            input_tokens = usage_metadata.prompt_token_count
            output_tokens = usage_metadata.candidates_token_count
            total_cost = calculate_cost(model_name, input_tokens, output_tokens)
            # --- NEUER DEBUG-OUTPUT IM TERMINAL ---
            print("\n--- GEMINI USAGE TRACKING ---")
            print(f"Model: {model_name}")
            print(f"Input Tokens: {input_tokens}")
            print(f"Output Tokens: {output_tokens}")
            print(f"Calculated Cost: {total_cost:.6f} €")
            print("-----------------------------\n")
            # --- ENDE DEBUG-OUTPUT ---
            return {
                "text": response.text,
                "usage": { "prompt_tokens": input_tokens, "completion_tokens": output_tokens },
                "cost": { "total_cost": total_cost }
            }
        else:
            return {"text": response.text}
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return {"text": f"An error occurred with the Gemini API: {e}"}

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