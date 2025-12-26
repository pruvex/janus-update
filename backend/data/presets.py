# backend/data/presets.py

from dataclasses import dataclass, field
from typing import List, Optional, Dict
import logging

logger = logging.getLogger("janus_backend")

# --- 1. DIE MATRIX (Datenstruktur) ---

@dataclass
class PresetConfig:
    name: str
    # Identität
    camera: str
    lens: str
    film_stock: str      # z.B. "Unprocessed RAW" oder "Kodak Portra 400"
    lighting: str        # z.B. "Available Light" oder "Studio Strobe"
    
    # Die "Signatur" (Was macht diesen Look einzigartig?)
    imperfections: List[str] 
    forbidden: List[str]      
    
    # Gemini spezifisch (Optional, falls abweichend)
    gemini_style_keywords: str = "Photorealistic, Raw, Detailed"
    
    # Qualitätskriterien für das Quality Gate
    vision_criteria: List[str] = field(default_factory=list)

# --- 2. DIE DATENBANK (Hier definierst du neue Presets) ---

PRESET_DATABASE = {
    "Fotorealistisch": {
        "Fotorealismus 1": PresetConfig(
            name="High-End RAW (Sony Alpha)",
            camera="Sony A7R V",
            lens="50mm f/1.2 GM",
            film_stock="Unprocessed RAW",
            lighting="Natural / Available Light",
            imperfections=[
                "Extremely shallow depth of field",
                "Smooth but imperfect bokeh",
                "Visible skin texture and pores",
                "Subtle film-like grain",
                "Slight focus falloff toward edges",
                "Natural vignette"
            ],
            forbidden=[
                "Studio lighting", "Perfect sharpness", "Synthetic clarity", 
                "Cinematic framing", "Symmetry perfection", "CGI", "3D Render"
            ],
            gemini_style_keywords="Raw Photography, National Geographic Style, 8k",
            vision_criteria=[
                "Does the skin look like real skin with pores (not plastic)?",
                "Is the background bokeh natural and not just a gaussian blur?",
                "Are there subtle imperfections like noise or slight focus miss?",
                "Does the lighting look physically plausible (no weird rim lights)?",
                "Are the textures (fabric, skin, surfaces) photorealistic with fine details?",
                "Is the depth of field consistent with the focal length and aperture?",
                "Are there any visible AI artifacts (distortions, weird patterns, or glitches)?"
            ]
        ),
        "Fotorealismus 2": PresetConfig(
            name="Editorial Studio (Hasselblad)",
            camera="Hasselblad X2D 100C",
            lens="80mm f/1.9",
            film_stock="Digital Medium Format",
            lighting="Professional Studio Strobes (Butterfly Lighting)",
            imperfections=[
                "Sharp focus falloff",
                "Makeup texture visible",
                "Flash reflections in eyes",
                "Micro-contrast"
            ],
            forbidden=[
                "Natural Light", "Blurry", "Amateur", "Grainy", "Low resolution"
            ],
            gemini_style_keywords="Studio Photography, Vogue Magazine Style, Editorial"
        )
    }
    # Hier können später einfach neue Kategorien wie "Comic" hin
}

# --- 3. DIE DSL (Logik / Builder) ---

def _compile_gpt_instruction(config: PresetConfig, user_prompt: str) -> str:
    """Baut die 'Diamond Standard' System-Instruktion für GPT-5.2"""
    
    imperfections_list = "\n- ".join(config.imperfections)
    forbidden_list = ", ".join([f"'{f}'" for f in config.forbidden])
    
    return (
        f"ROLE:\n"
        f"You are a photographic prompt engineer specialized in OpenAI's gpt-image-1.5.\n"
        f"You enforce a single, consistent look: {config.name}.\n\n"
        
        f"PRESET IDENTITY:\n"
        f"- Camera: {config.camera}\n"
        f"- Lens: {config.lens}\n"
        f"- Material: {config.film_stock}\n"
        f"- Lighting: {config.lighting}\n\n"
        
        f"STRICT RULES:\n"
        f"1. FORBIDDEN TOKENS: Do NOT use {forbidden_list}.\n"
        f"2. REQUIRED SIGNATURE: You MUST describe these exact imperfections:\n"
        f"- {imperfections_list}\n"
        f"3. PHYSICS: Simulate the sensor behavior of a {config.camera}.\n\n"
        
        f"EXECUTION:\n"
        f"1. Rewrite the user request to strictly conform to this preset.\n"
        f"2. DO NOT output the text to the user.\n"
        f"3. You MUST call the 'image_generation' tool with the rewritten prompt.\n\n"
        
        f"USER REQUEST:\n"
        f"{user_prompt}"
    )

def _compile_gemini_prompt(config: PresetConfig, user_prompt: str) -> str:
    """Baut den strukturierten Prompt für Gemini (Imagen 3)"""
    return (
        f"Generate a {config.gemini_style_keywords} image of {user_prompt}. "
        f"Camera: {config.camera} with {config.lens}. "
        f"Lighting: {config.lighting}. "
        f"Details: {', '.join(config.imperfections)}. "
        f"Quality: Best quality, high fidelity."
    )

# --- 4. PUBLIC API (Schnittstelle) ---

def get_preset(provider: str, style: str, variation: str, user_prompt: str) -> str:
    """
    Öffentliche Funktion, die von images.py aufgerufen wird.
    Sucht das Config-Objekt und wählt den richtigen Builder.
    """
    try:
        # 1. Config suchen
        category = PRESET_DATABASE.get(style)
        if not category:
            return user_prompt
            
        config = category.get(variation)
        if not config:
            return user_prompt

        # 2. Prompt bauen je nach Provider
        if provider == "openai":
            return _compile_gpt_instruction(config, user_prompt)
        elif provider == "gemini":
            return _compile_gemini_prompt(config, user_prompt)
            
    except Exception as e:
        logger.error(f"Fehler beim Bauen des Presets: {e}")
    
    return user_prompt