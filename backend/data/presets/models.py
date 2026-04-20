from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass
class VisionCriterion:
    id: str
    description: str
    weight: int
    failure_hint: Optional[str] = None
    is_critical: bool = False

@dataclass
class SocialTier:
    """Definiert Regeln für eine bestimmte soziale Schicht."""
    tier_id: str
    keywords: List[str]
    description: str
    textiles: List[str]
    colors: List[str]       # <--- HIER WAR DAS FEHLENDE FELD
    headwear: List[str]
    footwear: List[str]
    props: List[str]
    locations: List[str]
    forbidden: List[str]

@dataclass
class PresetConfig:
    name: str
    version: str
    preset_intent: str
    recommended_use: str 
    
    camera: str
    lens: str
    film_stock: str
    lighting: str
    capture_profile: Dict[str, str] = field(default_factory=dict)
    
    # NEU: Explizite Benchmark-Politik (Diamant-Standard Punkt 1)
    benchmark_composition_locked: bool = True 
    
    # NEU: Standardisierte Fehler-Modi für Auto-Fixing (Diamant-Standard Punkt 2)
    common_failure_modes: List[str] = field(default_factory=list)

    global_forbidden: List[str] = field(default_factory=list)
    
    social_tiers: List[SocialTier] = field(default_factory=list)
    default_tier: str = "commoner"
    
    gemini_style_keywords: str = "Photorealistic"
    vision_criteria: List[VisionCriterion] = field(default_factory=list)
    vision_pass_score: int = 75
    
    # Alte Felder für Abwärtskompatibilität (optional)
    imperfections: List[str] = field(default_factory=list)
    forbidden: List[str] = field(default_factory=list)
    props_required: List[str] = field(default_factory=list)
    shot_menu: List[str] = field(default_factory=list)
    cultural_behavior: List[str] = field(default_factory=list)
    social_norms: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        # Wir prüfen nur noch die Kernfelder, die immer da sein müssen.
        required_fields = {
            'name': self.name,
            'version': self.version,
            'preset_intent': self.preset_intent,
            'recommended_use': self.recommended_use,
            'camera': self.camera,
            'lens': self.lens,
            'film_stock': self.film_stock,
            'lighting': self.lighting
        }
        
        missing_fields = [field for field, value in required_fields.items() if not value]
        if missing_fields:
            raise ValueError(f"Preset '{self.name}' Error: Fehlende Pflichtfelder: {', '.join(missing_fields)}")