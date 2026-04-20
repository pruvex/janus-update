import logging
from typing import Dict, Tuple, Optional

# 1. Importiere Modelle
from .models import PresetConfig, SocialTier, VisionCriterion

# 2. Importiere Logik
from .logic import _compile_context, generate_preview_prompt

# 3. Importiere die Global Quality Gate Injection
from .library import inject_global_quality_gate

# 4. Importiere die Daten-Definitionen
from .definitions import photorealism, temporal, time_travel, comics, fine_art

logger = logging.getLogger("janus_backend")

# 5. Rekonstruktion der Datenbank (Zentrales Register)
# Die Keys hier (links) sind die Namen, die im Dropdown-Menü erscheinen.
PRESET_DATABASE = {
    # Kategorie 1: Fotorealismus (mit Global Quality Gate Injection)
    "Fotorealismus": inject_global_quality_gate(photorealism.presets),
    
    # Kategorie 2: Historische Fotografie (ehemals "Temporal Photorealism")
    # WICHTIG: temporal.py hat seine eigene Injection bereits intern durchgeführt.
    # Deshalb hier KEIN inject_global_quality_gate aufrufen, sonst haben wir Regeln doppelt.
    "Historische Fotografie": temporal.presets,
    
    # Kategorie 3: Zeitreise (mit Global Quality Gate Injection)
    "Zeitreise (Hyper-Realismus)": inject_global_quality_gate(time_travel.presets),
    
    # Kategorie 4: Illustrative & Comic Kunst (mit Global Quality Gate Injection)
    "Illustrative & Comic Kunst": inject_global_quality_gate(comics.presets),
    "Meisterwerke der Kunstgeschichte": inject_global_quality_gate(fine_art.presets) # <--- NEU
}

# 6. Die Public API Funktion
def get_preset(provider: str, style: str, variation: str, user_prompt: str) -> Tuple[Optional[PresetConfig], Dict]:
    """
    Sucht das Config-Objekt und gibt es zusammen mit dem kompilierten Kontext-Dictionary zurück.
    """
    try:
        # Datenbank Lookup
        category_data = PRESET_DATABASE.get(style)
        if not category_data:
            logger.warning(f"Kategorie nicht gefunden: {style}")
            # Wichtig: Gib ein valides Fallback-Context-Dict zurück
            return None, _compile_context(None, user_prompt)
            
        preset_config = category_data.get(variation)
        if not preset_config:
            logger.warning(f"Preset Variation nicht gefunden: {variation} in {style}")
            # Wichtig: Gib ein valides Fallback-Context-Dict zurück
            return None, _compile_context(None, user_prompt)

        # Kompilierung des Kontexts (Delegation an logic.py)
        context_dict = _compile_context(preset_config, user_prompt)
        
        return preset_config, context_dict
        
    except Exception as e:
        logger.error(f"Fehler beim Laden des Presets {style}/{variation}: {str(e)}")
        logger.error(f"Stacktrace: {e}", exc_info=True)
        # Wichtig: Gib ein valides Fallback-Context-Dict zurück
        return None, _compile_context(None, user_prompt)

# Expose für externe Importe
__all__ = [
    "PRESET_DATABASE",
    "PresetConfig",
    "SocialTier",
    "VisionCriterion",
    "generate_preview_prompt",
    "get_preset",
]