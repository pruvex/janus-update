from typing import List, Dict
from .models import VisionCriterion, PresetConfig

# --- GLOBAL DIAMOND STANDARD QUALITY GATE (v1.0.0) ---
# Ziel: Preset-agnostische Mindestqualität + harte Stopper gegen typische KI-Artefakte.
# Nutzung: Diese Criteria werden automatisch in alle Fotorealismus/Zeitreise Presets injiziert.

# 1. Standardisierte Failure Modes (für Auto-Fixing und Feedback)
COMMON_FAILURE_MODES: List[Dict[str, str]] = [
    {
        "id": "extra_fingers",
        "symptoms": "Zu viele Finger, verschmolzene Finger, verdrehte Handgelenke.",
        "fix": "Pose vereinfachen; Hände größer rendern; klare Fingertrennung."
    },
    {
        "id": "wax_skin",
        "symptoms": "Wachsige Haut, porenlos, Beauty-Filter, 'AI doll face'.",
        "fix": "Skin microtexture erhöhen, SSS reduzieren, Glättung entfernen."
    },
    {
        "id": "text_artifacts",
        "symptoms": "Zufällige Buchstaben, Signaturen, Wasserzeichen.",
        "fix": "Hintergründe vereinfachen; Schilder/Labels entfernen."
    },
    {
        "id": "hdr_halos",
        "symptoms": "Glow um Kanten, HDR-Look, harte Oversharpen-Halos.",
        "fix": "Sharpening reduzieren, Bloom deaktivieren, Kontrast moderater."
    },
    {
        "id": "inconsistent_shadows",
        "symptoms": "Schatten zeigen in verschiedene Richtungen oder fehlen.",
        "fix": "Dominante Key-Quelle definieren; Kontakt-/Fallschatten erzwingen."
    },
    {
        "id": "floating_objects",
        "symptoms": "Objekte wirken schwebend, keine Kontaktfläche.",
        "fix": "Kontaktfläche + weichen Kontaktschatten hinzufügen."
    }
]

# Für die einfache Verwendung als String-Liste im PresetConfig
COMMON_FAILURES_LIST = [f["id"] for f in COMMON_FAILURE_MODES]

# 2. Die 10 Goldenen Regeln (Vision Criteria)
GLOBAL_VISION_CRITERIA: List[VisionCriterion] = [
    VisionCriterion(
        id="no_text_artifacts",
        description="Kein Text, keine Wasserzeichen, keine UI-Elemente, keine Signage-Artefakte.",
        weight=12,
        is_critical=True,
        failure_hint="Entferne Text/Wasserzeichen; vereinfache Hintergrund."
    ),
    VisionCriterion(
        id="hand_anatomy",
        description="Hände/Finger anatomisch korrekt (5 Finger), keine Deformationen.",
        weight=14,
        is_critical=True,
        failure_hint="Pose vereinfachen; klare Fingertrennung; Hände im Fokus halten."
    ),
    VisionCriterion(
        id="face_integrity",
        description="Gesicht/Augen wirken lebendig und plausibel (keine Glasigkeit), sofern sichtbar.",
        weight=10,
        is_critical=False,
        failure_hint="Plausible Catchlights, Irisdetail erhöhen, Glasigkeit reduzieren."
    ),
    VisionCriterion(
        id="shadow_consistency",
        description="Konsistente Lichtlogik: plausible Lichtquelle(n), Schattenrichtung stimmt.",
        weight=14,
        is_critical=True,
        failure_hint="Schattenrichtung vereinheitlichen; Kontakt-/Fallschatten ergänzen."
    ),
    VisionCriterion(
        id="grounding",
        description="Physische Verankerung: Kontaktfläche/Kontaktschatten wo nötig (kein Schweben).",
        weight=10,
        is_critical=True,
        failure_hint="Kontaktfläche + weichen Kontaktschatten hinzufügen."
    ),
    VisionCriterion(
        id="no_oversharpening",
        description="Kein HDR-Glow, keine Oversharpen-Halos, keine unnatürlichen Kanten.",
        weight=10,
        is_critical=True,
        failure_hint="Sharpening reduzieren; Bloom/Glow deaktivieren; echtes Grain statt Halos."
    ),
    VisionCriterion(
        id="material_physics",
        description="Materialien verhalten sich plausibel (Roughness, Fresnel), kein CGI-Glanz.",
        weight=10,
        is_critical=True,
        failure_hint="Roughness-Variation; Reflexe weniger perfekt machen."
    ),
    VisionCriterion(
        id="clean_edges",
        description="Keine Doppelkonturen, kein Ghosting, keine unbeabsichtigten Outlines.",
        weight=8,
        is_critical=False,
        failure_hint="Kanten bereinigen; weniger aggressive Schärfung."
    ),
    VisionCriterion(
        id="focus_priority",
        description="Wichtige Bereiche sind klar: Gesicht, Hände, Held-Material.",
        weight=8,
        is_critical=True,
        failure_hint="Fokus auf Augen/Hände/Prop setzen; DOF reduzieren."
    ),
    VisionCriterion(
        id="pose_plausibility",
        description="Pose/Proportionen plausibel, keine verdrehten Gelenke.",
        weight=4,
        is_critical=True,
        failure_hint="Neutralere Pose; Perspektive weniger extrem."
    )
]

# 3. Helper Funktion
def inject_global_quality_gate(presets_dict: Dict[str, PresetConfig]) -> Dict[str, PresetConfig]:
    """
    Nimmt ein Dictionary von Presets und injiziert die globalen Qualitätsregeln.
    Verhindert Duplikate, falls Regeln schon manuell hinzugefügt wurden.
    """
    for key, config in presets_dict.items():
        # Füge Global Criteria hinzu (am Anfang der Liste für Priorität)
        # Wir filtern, damit wir keine IDs doppelt haben (falls lokal überschrieben)
        existing_ids = {c.id for c in config.vision_criteria}
        
        new_criteria = []
        for global_crit in GLOBAL_VISION_CRITERIA:
            if global_crit.id not in existing_ids:
                new_criteria.append(global_crit)
        
        # Globale Regeln kommen ZUERST, dann die spezifischen
        config.vision_criteria = new_criteria + config.vision_criteria
        
        # Injiziere Common Failure Modes wenn leer
        if not config.common_failure_modes:
            config.common_failure_modes = COMMON_FAILURES_LIST
            
    return presets_dict
