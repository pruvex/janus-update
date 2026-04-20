import logging
from typing import Optional, Dict
from .models import PresetConfig

logger = logging.getLogger("janus_backend")

# --- KONSTANTEN ---
TIME_PORTAL_FRAMING_RULE = (
    "4. MANDATORY FRAMING (ANTI-SQUASH PLAN B):\n"
    "   - This image is generated in TALL format (1024x1536) and cropped later.\n"
    "   - LENS: '100mm telephoto lens' (to flatten features).\n"
    "   - FRAMING: 'American Shot (Knees up)'. Do NOT try to fit the feet.\n"
    "   - HEADROOM: 'Plenty of empty space above the head/headdress.\n"
    "   - REWRITE: 'Waist-up' -> 'Knees-up with headroom'.\n"
)

# NEU: Die "Smart Localization" Regel
CULTURAL_FALLBACK_RULE = (
    "5. SMART LOCALIZATION (CULTURAL FALLBACK):\n"
    "   - CHECK: Does the USER REQUEST contain a specific location (e.g. 'London', 'Kyoto', 'Wild West')?\n"
    "   - IF YES: Follow the user's location strictly.\n"
    "   - IF NO: Deduce the setting from the LANGUAGE of the prompt.\n"
    "     * German Prompt -> Set scene in Germany/Central Europe (Architecture, Fashion, Ethnicity matches region).\n"
    "     * Japanese Prompt -> Set scene in Japan.\n"
    "     * French Prompt -> Set scene in France.\n"
    "     * English Prompt -> Default to UK or US (depending on context).\n"
    "   - GOAL: The image should feel 'local' to the user's language unless told otherwise.\n"
)

def _compile_context(config: Optional[PresetConfig], user_prompt: str) -> Dict:
    """
    Sammelt alle Regeln und Kontextinformationen basierend auf dem Preset und User-Prompt.
    Gibt ein strukturiertes Dictionary zurück.
    """
    if not config:
        return {
            "has_preset": False,
            "user_prompt": user_prompt
        }

    # --- Tier-Auswahl (bestehende Logik, leicht angepasst) ---
    selected_tier = None
    if config.social_tiers:
        for tier in config.social_tiers:
            if any(keyword.lower() in user_prompt.lower() for keyword in tier.keywords):
                selected_tier = tier
                break
        if not selected_tier:
            selected_tier = next((t for t in config.social_tiers if t.tier_id == config.default_tier), config.social_tiers[0])

    # --- Zusammenstellung des Kontext-Objekts ---
    context = {
        "has_preset": True,
        "user_prompt": user_prompt,
        "film_stock": config.film_stock,
        "lens": config.lens,
        "camera": config.camera,
        "lighting": config.lighting,
        "gemini_style_keywords": config.gemini_style_keywords,
        "rules": {
            "era_intent": config.preset_intent,
            "tier_description": selected_tier.description if selected_tier else "N/A",
            "textiles": selected_tier.textiles if selected_tier else getattr(config, 'social_norms', []),
            "props": selected_tier.props if selected_tier else getattr(config, 'props_required', []),
            "forbidden_items": config.global_forbidden + (selected_tier.forbidden if selected_tier else getattr(config, 'forbidden', [])),
            "imperfections": getattr(config, 'imperfections', [])
        }
    }
    return context

def generate_preview_prompt(config: PresetConfig) -> str:
    """
    Generiert den Master-Prompt für ein einheitliches Vorschaubild.
    FIX: Entfernt 'Reference Sheet' Begriffe, um Ränder bei DALL-E zu unterbinden.
    """
    style_name = config.name
    style_definition = config.preset_intent
    style_keywords = getattr(config, "gemini_style_keywords", "")
    
    # Tier-Logik für Kleidung/Props
    if config.social_tiers and len(config.social_tiers) > 0:
        default_tier = config.social_tiers[0]
        wardrobe = f"Attire matches the '{default_tier.tier_id}' social tier ({', '.join(default_tier.textiles)})."
        prop = f"Holding a {default_tier.props[0] if default_tier.props else 'typical object'}."
    else:
        wardrobe = f"Attire must be perfectly typical for the setting: '{style_definition}'."
        prop = f"Holding a small, complex object (e.g. a device, a tool, or a geometric shape)."

    return (
        f"TASK: Create a definitive, high-fidelity full-bleed example of the following style.\n"
        f"TARGET STYLE: {style_name}\n"
        f"STYLE DEFINITION: {style_definition}\n"
        f"STYLE KEYWORDS: {style_keywords}\n\n"
        f"COMPOSITION (LOCKED):\n"
        f"- Subject: One adult female fictional character.\n"
        f"- Framing: Medium shot (mid-torso to head), centered, facing camera.\n"
        f"- Pose: Neutral, professional, holding an object at chest level.\n"
        f"- Background: Simple background matching the style, slightly out of focus.\n\n"
        f"MANDATORY FRAMING REGULATION:\n"
        f"- ZERO BORDERS. ZERO MARGINS. ZERO WHITE SPACE.\n"
        f"- The artwork must be a FULL-BLEED digital file.\n"
        f"- The illustration must touch all four physical edges of the image canvas.\n\n"
        f"ADAPTIVE ELEMENTS:\n"
        f"- WARDROBE: {wardrobe}\n"
        f"- PROP: {prop}\n"
        f"- LIGHTING: Lighting setup matches: '{config.lighting}'.\n\n"
        f"OUTPUT GOAL: Showcase material, skin/surface, and light in this exact style. No text. Edge-to-edge art only."
    )