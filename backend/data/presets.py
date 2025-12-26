# backend/data/presets.py

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger("janus_backend")

# --- 1. NEUE DATENKLASSE FÜR STRUKTURIERTE VISION-KRITERIEN ---
@dataclass
class VisionCriterion:
    id: str               # Eindeutiger Name für das Kriterium (z.B. "skin_texture")
    description: str      # Was soll der Vision-Checker prüfen?
    weight: int           # Wie wichtig ist dieses Kriterium für den Gesamt-Score?
    failure_hint: Optional[str] = None # Anweisung für die automatische Korrektur (Degradation)

# --- 2. VERBESSERTE MATRIX-DATENSTRUKTUR ---
@dataclass
class PresetConfig:
    name: str
    camera: str
    lens: str
    film_stock: str
    lighting: str
    imperfections: List[str]
    forbidden: List[str]
    
    gemini_style_keywords: str = "Photorealistic, Raw, Detailed"
    
    # NEU: Strukturierte Kriterien und ein Pass-Score
    vision_criteria: List[VisionCriterion] = field(default_factory=list)
    vision_pass_score: int = 75 # Standard-Schwelle, kann pro Preset überschrieben werden

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
            gemini_style_keywords="Raw photography, documentary realism, natural imperfections",
            vision_pass_score=80, # Für dieses Preset wollen wir strenger sein
            vision_criteria=[
                VisionCriterion(
                    id="skin_texture",
                    description="Skin shows natural pores and micro texture, not plastic or airbrushed.",
                    weight=30,
                    failure_hint="add more realistic skin texture and pores"
                ),
                VisionCriterion(
                    id="bokeh_realism",
                    description="Background blur (bokeh) looks optically plausible, not like a simple gaussian blur.",
                    weight=20,
                    failure_hint="make the bokeh less uniform and add optical imperfections"
                ),
                VisionCriterion(
                    id="lighting_physics",
                    description="Lighting appears physically plausible, coming from a clear, natural source.",
                    weight=25,
                    failure_hint="simplify the lighting to a single, strong natural light source"
                ),
                VisionCriterion(
                    id="ai_artifacts",
                    description="There are no obvious signs of AI, like overly smooth surfaces or weird details.",
                    weight=25,
                    failure_hint="reduce synthetic smoothness and add micro-textures"
                )
            ]
        ),
        "Fotorealismus 2": PresetConfig(
            name="Editorial Studio (Hasselblad)",
            camera="Hasselblad X2D 100C",
            lens="80mm f/1.9",
            film_stock="Digital Medium Format",
            lighting="Professional Studio Strobes (Butterfly Lighting)",
            imperfections=["Sharp focus falloff", "Makeup texture visible", "Flash reflections in eyes"],
            forbidden=["Natural Light", "Blurry", "Amateur", "Grainy"],
            gemini_style_keywords="Studio Photography, Vogue Magazine Style, Editorial"
        )
    }
    # Weitere Kategorien können hier hinzugefügt werden
}

# --- 3. DIE DSL (Logik / Builder) ---

def _compile_gpt_instruction(config: PresetConfig, prompt: str) -> str:
    """Baut die 'Diamond Standard' System-Instruktion für GPT-5.2"""
    
    imperfections_list = "\n- ".join(config.imperfections)
    forbidden_list = ", ".join([f"'{f}'" for f in config.forbidden])
    
    return (
        f"ROLE:\n"
        f"You are a photographic prompt engineer. You enforce a single, consistent look: {config.name}.\n\n"
        
        f"PRESET IDENTITY:\n"
        f"- Camera: {config.camera}\n"
        f"- Lens: {config.lens}\n"
        f"- Material: {config.film_stock}\n"
        f"- Lighting: {config.lighting}\n\n"
        
        f"STRICT RULES:\n"
        f"1. FORBIDDEN TOKENS: Do NOT use {forbidden_list}.\n"
        f"2. REQUIRED SIGNATURE: You MUST describe these exact imperfections:\n- {imperfections_list}\n"
        f"3. PHYSICS: Simulate the sensor behavior of a {config.camera}.\n\n"
        
        f"ANTI-DEVIATION:\n" 
        f"- Do not reinterpret the preset creatively.\n"
        f"- Do not adapt the style to the subject. The preset overrides artistic intent.\n\n"
        
        f"FAILURE CONDITION:\n" 
        f"If the user request conflicts with the preset, keep the preset and degrade the request.\n\n"

        f"EXECUTION:\n"
        f"1. Rewrite the user request to strictly conform to this preset.\n"
        f"2. You MUST call the 'image_generation' tool with the rewritten prompt.\n\n"
        
        f"USER REQUEST:\n"
        f"{prompt}"
    )

def _compile_gemini_prompt(config: PresetConfig, prompt: str) -> str:
    """Baut den strukturierten Prompt für Gemini (Imagen 3)"""
    return (
        f"Generate a {config.gemini_style_keywords} image of {prompt}. "
        f"Camera: {config.camera} with {config.lens}. "
        f"Lighting: {config.lighting}. "
        f"Details: {', '.join(config.imperfections)}. "
        f"Quality: Best quality, high fidelity."
    )

# --- 4. PUBLIC API (Schnittstelle) ---

def get_preset(provider: str, style: str, variation: str, prompt: str) -> str:
    """
    Öffentliche Funktion, die von images.py aufgerufen wird.
    Sucht das Config-Objekt und wählt den richtigen Builder.
    """
    try:
        # 1. Config suchen
        category = PRESET_DATABASE.get(style)
        if not category:
            return prompt
            
        config = category.get(variation)
        if not config:
            return prompt

        # 2. Prompt bauen je nach Provider
        if provider == "openai":
            return _compile_gpt_instruction(config, prompt)
        elif provider == "gemini":
            return _compile_gemini_prompt(config, prompt)
            
    except Exception as e:
        logger.error(f"Fehler beim Bauen des Presets: {e}")
    
    return prompt