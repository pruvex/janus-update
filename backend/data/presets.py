# backend/data/presets.py

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
import logging

logger = logging.getLogger("janus_backend")

# --- GLOBALE REGELN FÜR ZEITREISE-PRESETS ---
# Diese Regeln gelten automatisch für alle Presets mit "(Time Portal)" im Namen.

TIME_PORTAL_GLOBAL_FORBIDDEN = [
    # Technologie & Material
    "Zippers", "Velcro", "Plastic", "Nylon", "Polyester", "Rubber soles",
    "Wristwatches", "Glasses", "Modern jewelry", "Machine stitching",
    
    # Ästhetik & Haare
    "Modern hairstyles", "Pixie cut", "Bob cut", "Fade cut", "Messy bun", 
    "Hairspray look", "Makeup contouring", "Lip gloss", "Botox face",
    
    # Bild-Stil
    "Sepia", "Vintage filter", "Film grain overlay", "Vignette", 
    "Ruins (unless specified)", "Museum display"
]

TIME_PORTAL_FRAMING_RULE = (
    "4. MANDATORY FRAMING (ANTI-SQUASH PLAN B):\n"
    "   - This image is generated in TALL format (1024x1536) and cropped later.\n"
    "   - LENS: '100mm telephoto lens' (to flatten features).\n"
    "   - FRAMING: 'American Shot (Knees up)'. Do NOT try to fit the feet.\n"
    "   - HEADROOM: 'Plenty of empty space above the head/headdress.'\n"
    "   - REWRITE: 'Waist-up' -> 'Knees-up with headroom'.\n"
)

# --- 1. DATENKLASSEN ---
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
    colors: List[str]
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
    
    global_forbidden: List[str] = field(default_factory=list)
    
    social_tiers: List[SocialTier] = field(default_factory=list)
    default_tier: str = "commoner"
    
    gemini_style_keywords: str = "Photorealistic"
    vision_criteria: List[VisionCriterion] = field(default_factory=list)
    vision_pass_score: int = 75
    
    # Alte Felder für Abwärtskompatibilität
    imperfections: List[str] = field(default_factory=list)
    forbidden: List[str] = field(default_factory=list)
    props_required: List[str] = field(default_factory=list)
    shot_menu: List[str] = field(default_factory=list)
    cultural_behavior: List[str] = field(default_factory=list)
    social_norms: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        # Wir prüfen nur noch die Kernfelder, die immer da sein müssen.
        # Alte Felder wie 'imperfections' sind jetzt optional.
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

# --- 2. DIE PRESET-DATENBANK ---
PRESET_DATABASE = {
    "Fotorealismus": {
        "Authentic RAW Reality": PresetConfig(
            name="Ungestellte Realität (Sony Alpha)",
            version="2.0.0",
            preset_intent="Dieses Preset simuliert ungestellte, reale Fotografie und priorisiert physikalische Plausibilität über ästhetische Perfektion.",
            recommended_use="Ideal für Street Photography, Journalismus und Szenen, in denen 'Grit' und Authentizität wichtiger sind als Schönheit.",
            
            camera="Sony A7R V",
            lens="35mm f/1.8",
            film_stock="Unverarbeitetes RAW",
            lighting="Nur natürliches Licht",
            
            imperfections=[
                "Subtil optische Unvollkommenheiten",
                "Unschärfe durch Bewegung oder Fokusfehler",
                "Sichtbare Material-Mikrostruktur",
                "Natürliche Hauttextur und Poren bei Personen",
                "Leichtes Bildrauschen (ISO 800)"
            ],
            
            forbidden=["Studio-Beleuchtung", "Perfekt zentriert", "Symmetrie", "CGI", "Retuschiert", "Dramatische Beleuchtung"],
            
            gemini_style_keywords="8k ultra-realistic documentary photograph, RAW photo, natural lighting, sharp focus, high detail, tangible textures, -no digital art, -no CGI",
            vision_pass_score=80,
            
            vision_criteria=[
                VisionCriterion(
                    id="no_ai_polish", 
                    description="Keine künstliche Glättung oder 'CGI'-Optik.", 
                    weight=40,
                    failure_hint="Füge Mikrotexturen hinzu und reduziere den globalen Kontrast",
                    is_critical=True
                ),
                VisionCriterion(
                    id="lighting_physics", 
                    description="Natürliche Lichtführung mit einer plausiblen Lichtquelle.", 
                    weight=35,
                    failure_hint="Vereinfache die Beleuchtung auf eine natürliche Quelle"
                ),
                VisionCriterion(
                    id="optical_imperfection", 
                    description="Subtil optische Unvollkommenheiten wie weiche Kanten oder leichtes Rauschen.", 
                    weight=25,
                    failure_hint="Füge subtile Bewegungsunschärfe und Fokusfehler hinzu"
                )
            ]
        ),
        "Menschliche Porträt-Treue": PresetConfig(
            name="Hochauflösendes Porträt (Canon RF)",
            version="2.0.0",
            preset_intent="Erfasst menschliche Subjekte mit dermatologischer Genauigkeit und psychologischer Tiefe, vermeidet das 'perfekte KI-Gesicht'.",
            recommended_use="Perfekt für professionelle Headshots, Charakterstudien und Portraits, die menschliche Haut und Emotionen realistisch zeigen sollen.",
            
            camera="Canon EOS R5",
            lens="85mm f/1.2L",
            film_stock="Digitales Porträtprofil",
            lighting="Sanftes Aufhelllicht (Softbox oder Fenster)",
            
            imperfections=[
                "Natürliche Hautporen und Unreinheiten",
                "Asymmetrische Gesichtszüge",
                "Lebensechte Reflexe in den Augen",
                "Abstehende Haare"
            ],
            
            forbidden=["Glasige Augen", "Perfekt glatte Haut", "Symmetrisches Gesicht", "Ausdruckslose Mimik", "Harte Schatten"],
            gemini_style_keywords="ultra-realistic 8k professional portrait photograph, soft window lighting, sharp focus on eyes, detailed skin texture with pores, natural asymmetry, -no airbrushing, -no plastic skin",
            vision_pass_score=85,
            
            vision_criteria=[
                VisionCriterion(
                    id="skin_texture", 
                    description="Haut zeigt natürliche, detaillierte Poren und Textur, nicht plastikartig oder retuschiert.", 
                    weight=50,
                    failure_hint="Füge realistische Hauttextur und Poren hinzu",
                    is_critical=True
                ),
                VisionCriterion(
                    id="facial_asymmetry", 
                    description="Das Gesicht ist natürlich asymmetrisch und nicht perfekt gespiegelt.", 
                    weight=30,
                    failure_hint="Füge leichte Gesichtsasymmetrien hinzu"
                ),
                VisionCriterion(
                    id="eye_realism", 
                    description="Die Augen haben Tiefe und realistische, quellbasierte Lichreflexe.", 
                    weight=20,
                    failure_hint="Achte auf detaillierte Lichreflexe in den Augen"
                )
            ]
        ),
        "Kommerzieller Produkt-Realismus": PresetConfig(
            name="Fühlbare Produktaufnahme (Fuji GFX)",
            version="2.0.0",
            preset_intent="Präsentiert Objekte mit physikalischem Gewicht und realistischer Materialinteraktion für kommerzielle Zwecke.",
            recommended_use="Für hochwertige Produktfotos, Mockups und Werbung, bei denen Materialien und Haptik im Vordergrund stehen.",
            
            camera="Fujifilm GFX 100S",
            lens="120mm f/4 Macro",
            film_stock="Mittelformat Digital",
            lighting="Kontrolliertes, sauberes Studio-Licht mit mehreren Lichtquellen",
            
            imperfections=[
                "Kontaktschatten sind sichtbar",
                "Mikrokratzer oder Staub auf Oberflächen",
                "Leicht dezentrierte Komposition",
                "Realistische Materialreflexionen"
            ],
            
            forbidden=[
                "Schwebende Objekte", "Keine Schatten", "Perfekt zentriert", "CGI-artige Reflexionen", "Plastikoptik"
            ],
            gemini_style_keywords="ultra-realistic 8k commercial product photograph, clean studio lighting, sharp focus, macro details, tangible material surface, contact shadow, -no floating, -no CGI",
            vision_pass_score=75,
            
            vision_criteria=[
                VisionCriterion(
                    id="physical_presence", 
                    description="Das Objekt wirkt physisch präsent mit korrektem Gewicht und Kontaktschatten.", 
                    weight=40,
                    failure_hint="Füge einen weichen Kontaktschatten hinzu"
                ),
                VisionCriterion(
                    id="surface_details", 
                    description="Oberflächen zeigen Mikrodetails wie Staub, Kratzer oder Textur.", 
                    weight=35,
                    failure_hint="Füge subtile Oberflächenunvollkommenheiten hinzu"
                ),
                VisionCriterion(
                    id="no_render_signals", 
                    description="Reflexionen und Beleuchtung folgen den physikalischen Gesetzen der realen Welt.", 
                    weight=25,
                    failure_hint="Mache Reflexionen weniger perfekt",
                    is_critical=True
                )
            ]
        )
    },
    
    # --- KATEGORIE: Temporal Photorealism ---
    "Temporal Photorealism": {
        "1890 – Glass Plate Photography": PresetConfig(
            name="Early Photographic Realism (Glass Plate Era, ~1890)",
            version="1.1.0",
            preset_intent="To simulate the physical and cultural constraints of late 19th-century photography, focusing on technological and social norms of the era.",
            recommended_use="Ideal für historische Porträts, Stillleben oder Szenen, die eine authentische, ernste und unvollkommene Anmutung der Zeit erfordern.",
            
            camera="Large Format Glass Plate Camera",
            lens="Fixed focal length brass lens",
            film_stock="Orthochromatic glass plate emulsion",
            lighting="Strong natural daylight or window light",
            
            imperfections=[
                "Very long exposure time creating motion blur on moving elements",
                "Low contrast tonal range with milky blacks",
                "Soft edge sharpness and visible lens distortion",
                "Visible chemical inconsistencies, spots, or scratches",
                "Subtle vignette and uneven exposure across the plate"
            ],
            forbidden=[
                "Modern object", "Modern clothing", "Smiling", "Casual pose", "Electric lighting",
                "High contrast", "Sharp focus", "Cinematic framing",
                "Color photography", "Digital artifacts", "CGI"
            ],
            
            cultural_behavior=[
                "Formal posture, upright and stiff",
                "No casual body language or slouching",
                "Subjects look like they have to hold their breath for exposure",
                "Hands resting on a surface or holding an object for stability",
                "Minimal eye contact with the camera"
            ],
            social_norms=[
                "No smiling (teeth are hidden)",
                "Serious, stoic expression",
                "Direct eye contact is intense or absent",
                "Formal attire (high collars, corsets, vests, hats)",
                "Gender-specific poses (men standing, women seated with hands in lap)"
            ],
            
            gemini_style_keywords="authentic 1890s glass plate photograph, historical realism, victorian era, orthochromatic, long exposure, soft focus, milky blacks, chemical imperfections, -no digital filter, -no smiling",
            
            vision_pass_score=85,
            vision_criteria=[
                VisionCriterion(
                    id="full_temporal_coherence",
                    description=(
                        "The entire image—including environment, materials, clothing, and lighting—"
                        "appears native to the late 19th century. No modern cues (like asphalt, modern fabrics, zippers) are visible."
                    ),
                    weight=30,
                    is_critical=True,
                    failure_hint=(
                        "replace remaining modern visual cues (clothing/background) and fully re-render the scene using period-accurate materials"
                    )
                ),
                VisionCriterion(
                    id="cultural_authenticity",
                    description=(
                        "The image accurately reflects 1890s social norms, including formal posture, "
                        "clothing, and expressions. No anachronistic behaviors or attitudes."
                    ),
                    weight=30,
                    is_critical=True,
                    failure_hint="adjust posture, expression, and clothing to match Victorian era norms"
                ),
                VisionCriterion(
                    id="temporal_objects",
                    description="The scene contains no anachronistic objects, materials, or modern technology.",
                    weight=30,
                    is_critical=True,
                    failure_hint="remove any modern items and replace with period-appropriate alternatives (e.g., replace phone with a book)."
                ),
                VisionCriterion(
                    id="pose_expression",
                    description="Subjects appear posed, stiff, and have a serious or neutral expression, consistent with long exposure times.",
                    weight=15,
                    failure_hint="reduce facial expression to neutral and enforce a more static, formal posture."
                ),
                VisionCriterion(
                    id="photographic_process",
                    description="The image shows artifacts of an early chemical process (soft focus, low dynamic range, chemical spots), not a digital filter.",
                    weight=15,
                    failure_hint="soften sharp edges, reduce overall contrast, and add subtle chemical irregularities or plate damage."
                )
            ]
        ),
        "1930 – Interwar Documentary": PresetConfig(
            name="Interwar Documentary Realism (1930s)",
            version="1.0.0",
            preset_intent="To capture the gritty, candid realism of 1930s photojournalism using early 35mm film technology and uncoated optics.",
            recommended_use="Perfekt für 'Street Photography', Reportagen, dokumentarische Szenen und authentische Momente, die wie Zeitzeugenberichte aus den 30ern wirken sollen.",
            
            camera="35mm Rangefinder Camera (Leica II style)",
            lens="50mm f/3.5 uncoated lens",
            film_stock="Black and white panchromatic nitrate film",
            lighting="Available natural light (High Contrast)",
            
            imperfections=[
                "Noticeable organic film grain",
                "Moderate contrast with deep shadows (Noir feel)",
                "Slight motion blur due to handheld capture",
                "Lens softness towards the corners",
                "Uneven exposure in highlights (halo effect)"
            ],
            forbidden=[
                "Modern fashion", "Perfect digital sharpness", "Studio lighting",
                "High dynamic range", "Color", "Cinematic lighting", "CGI", "Smiling for the camera"
            ],
            
            gemini_style_keywords="authentic 1930s documentary photograph, grainy black and white nitrate film, high contrast, photojournalism realism, Leica rangefinder style, -no digital sharpness, -no color",
            
            vision_pass_score=80,
            vision_criteria=[
                VisionCriterion(
                    id="documentary_authenticity",
                    description="Image feels candid, unposed and documentary.",
                    weight=30,
                    failure_hint="remove posed elements and add spontaneity"
                ),
                VisionCriterion(
                    id="film_behavior",
                    description="Grain structure and tonal response match 1930s nitrate film.",
                    weight=25,
                    failure_hint="increase organic film grain and reduce clarity"
                ),
                VisionCriterion(
                    id="temporal_fashion",
                    description="Clothing, hair, and objects align strictly with the 1930s period.",
                    weight=30,
                    is_critical=True, 
                    failure_hint="replace modern clothing/objects with 1930s equivalents"
                ),
                VisionCriterion(
                    id="lens_character",
                    description="Lens rendering shows softness of uncoated optics.",
                    weight=15,
                    failure_hint="reduce edge sharpness and micro-contrast"
                )
            ]
        ),
        "1970 – Analog Color Realism": PresetConfig(
            name="Analog Color Realism (Kodachrome Era, 1970s)",
            version="1.1.0",
            preset_intent="To simulate the warm, earthy aesthetic of 1970s Kodachrome slide film. The look must be strictly vintage, avoiding any 1980s neon/noir aesthetics or modern cinematic grading.",
            recommended_use="Ideal für Nostalgie-Aufnahmen, Roadtrips, authentische Porträts und Szenen, die die Wärme, die Mode und das analoge Lebensgefühl der 70er Jahre einfangen sollen.",
            
            camera="35mm SLR (Canon AE-1 style)",
            lens="50mm f/1.8 vintage coating",
            film_stock="Vintage Kodachrome 64 (slightly aged)",
            lighting="Natural warm light or Tungsten (No Neon)",
            
            imperfections=[
                "Visible organic color grain",
                "Strong warm color cast (Yellow/Orange/Brown tones)",
                "Yellow/Green cast (typical for aged prints)",
                "Milky blacks (Low contrast in shadows)",
                "Subtle color fading",
                "Slight motion blur typical of consumer photography"
            ],
            
            forbidden=[
                "1980s style", "Neon lights", "Black shiny biker leather", "Mullet hairstyle",
                "Modern digital color grading", "HDR", "Teal and Orange",
                "Perfect skin smoothing", "CGI", "Cold digital sharpness", 
                "Modern fashion", "Smartphones"
            ],
            
            gemini_style_keywords=(
                "1970s color photography, kodachrome film look, vintage slr photo, "
                "earth tones, warm analog colors, nostalgic aesthetic, stephen shore style"
            ),
            
            vision_pass_score=78,
            vision_criteria=[
                VisionCriterion(
                    id="color_response",
                    description="Color palette consists of earth tones (browns, greens, oranges) and warm Kodachrome shifting. No cold blue/neon vibes.",
                    weight=35,
                    failure_hint="shift white balance to warm/yellow and remove blue/neon tones"
                ),
                VisionCriterion(
                    id="temporal_accuracy",
                    description="Clothing and styling must be strictly 1970s (polyester, corduroy, trench coats), avoiding 1980s punk/rocker leather styles.",
                    weight=35,
                    is_critical=True, 
                    failure_hint="change clothing to 1970s earth-tone fashion"
                ),
                VisionCriterion(
                    id="optical_characteristics",
                    description="Image shows analog softness and film grain, lacking digital clinical sharpness.",
                    weight=30,
                    failure_hint="add organic grain and soften edges"
                )
            ]
        ),
        "1980s – Vibrant High Gloss Realism": PresetConfig(
            name="Vibrant High Gloss Realism (1980s)",
            version="1.1.0",
            preset_intent="To simulate the high-contrast, saturated aesthetic of 1980s commercial photography using color negative film. The subject must be physically grounded in the environment with consistent light interaction, avoiding a cut-out look.",
            recommended_use="Perfekt für Mode, Lifestyle, 'Flashy'-Porträts und Szenen, die den bunten, konsumorientierten und blitzlicht-geladenen Look der 80er Jahre einfangen sollen.",
            
            camera="Nikon F3 (35mm SLR)",
            lens="35-70mm Zoom Lens (Early multi-coating)",
            film_stock="Fujicolor Super HR 100 (Vibrant Colors)",
            lighting="Direct Ring Flash mixed with Ambient City Light",
            
            imperfections=[
                "Halation (light blooming) around highlights",
                "Slight diffusion glow (Pro-Mist filter effect)",
                "High color saturation (especially Reds and Cyans)",
                "Atmospheric haze blending subject and background", 
                "Chromatic aberration typical of early zoom lenses"
            ],
            forbidden=[
                "Synthwave", "Retrowave", "Neon Grid", "CGI", "Illustration",
                "Vector art", "Modern HD", "Muted colors", "Digital noise",
                "Smartphones", "Flat screens", "Floating subject", "Bad compositing"
            ],
            
            gemini_style_keywords=(
                "1980s fashion photography, direct flash, fujicolor look, "
                "vibrant analog colors, soft focus highlights, editorial realism, "
                "volumetric lighting, subject grounded in environment"
            ),
            
            vision_pass_score=80,
            vision_criteria=[
                VisionCriterion(
                    id="lighting_integration",
                    description="The subject is realistically integrated into the lighting of the environment, despite the flash usage (light spill, reflections).",
                    weight=35,
                    failure_hint="add volumetric fog or light spill to connect subject with background"
                ),
                VisionCriterion(
                    id="temporal_80s",
                    description="Fashion, hair (volume!), and objects must strictly adhere to 1980s aesthetics.",
                    weight=35,
                    is_critical=True, 
                    failure_hint="replace clothing with 80s fashion"
                ),
                VisionCriterion(
                    id="no_synthwave",
                    description="Image looks like a photograph, NOT a digital artwork or synthwave cover.",
                    weight=30,
                    is_critical=True,
                    failure_hint="remove neon grids and laser effects"
                )
            ]
        )
    },
    
    # --- NEUE KATEGORIE: Zeitreise (Hyper-Realismus) ---
    "Zeitreise (Hyper-Realismus)": {
        
        # -------------------------------------------------------------------------
        # STEINZEIT (Paläolithikum)
        # Fokus: Keine Webstoffe, keine Metalle, schmutzige Realität.
        # -------------------------------------------------------------------------
        "Steinzeit (Paläolithikum)": PresetConfig(
            name="Paleolithic Survival (Time Portal)",
            version="2.3.0",
            preset_intent="Capture the raw Stone Age. NO WOVEN FABRIC. NO METAL. Clothing is raw animal hide/fur only. Humans are dirty, hair is matted. Survival focus.",
            recommended_use="Jäger & Sammler. Authentische Darstellung ohne Zivilisation.",
            
            camera="Fujifilm GFX 100S",
            lens="Fujinon GF 32-64mm",
            film_stock="Digital RAW (High Dynamic Range)",
            lighting="Campfire, Torchlight, or Harsh Sun",
            
            capture_profile={
                "Resolution": "8K, ultra-fine micro-contrast",
                "Color Pipeline": "Neutral documentary grade",
                "Texture": "High frequency details (pores, fur)"
            },
            
            imperfections=["Soot on skin", "Matted hair", "Dirt under fingernails", "Scarring", "Insect bites"],
            
            forbidden=[
                # Historische Fehler
                "Woven fabric", "Textiles", "Cotton", "Wool", "Linen", "Silk", "Felt",
                "Metal", "Iron", "Bronze", "Steel", 
                "Clean hair", "Shaved faces", "Modern teeth",
                "Roads", "Fences", "Houses", "Agriculture"
            ],
            
            props_required=[
                "Raw animal hides (untanned/furry)", "Flint tools (stone)", "Bone needles", 
                "Wooden spears (fire hardened)", "Ocher body paint"
            ],
            
            shot_menu=[
                "Low-angle hero shot of a hunter",
                "Close-up of hands making fire",
                "Wide shot of a cave entrance"
            ],
            
            cultural_behavior=["Primal alertness", "Squatting posture", "Huddling for warmth"],
            social_norms=["No personal space", "Tools always in hand", "Functional nudity/furs"],
            
            gemini_style_keywords="National Geographic paleolithic, raw survival, 8k, dirty skin, animal hides, flint tools",
            
            vision_pass_score=90,
            vision_criteria=[
                VisionCriterion(id="no_textiles", description="Clothing MUST be raw hide/fur. NO woven fabric.", weight=50, is_critical=True, failure_hint="replace cloth with fur"),
                VisionCriterion(id="no_metal", description="No metal objects allowed.", weight=30, is_critical=True, failure_hint="remove metal"),
                VisionCriterion(id="hygiene", description="Subjects must look dirty/unkempt.", weight=20, failure_hint="add dirt")
            ]
        ),
        
        # -------------------------------------------------------------------------
        # ALTES ÄGYPTEN (Neues Reich)
        # Fokus: Leinen (keine Wolle), Perücken/Kahl, keine Kamele, keine Ruinen.
        # -------------------------------------------------------------------------
        "Altes Ägypten (Neues Reich)": PresetConfig(
            name="Pharaonic Realism (Time Portal)",
            version="1.3.0", # Update für Haare
            preset_intent="Ancient Egypt (New Kingdom) in 8K. NOT A PAINTING. Historical accuracy: White Linen clothing only. Wigs or shaved heads (no modern hair). Painted temples (no ruins).",
            recommended_use="Alltag am Nil, Tempel, Paläste. Historisch korrektes Ägypten.",
            
            camera="Leica SL2 (High Contrast B&W or Muted Color)",
            lens="50mm f/0.95 Noctilux (Depth of Field)",
            film_stock="Digital RAW (Natural/Muted)",
            lighting="Harsh Mediterranean Sun or flickering Oil Lamps",
            
            capture_profile={
                "Resolution": "8K, photorealistic texture",
                "Color Pipeline": "Natural, slightly desaturated, dusty", 
                "Texture": "Tangible fabrics (wool/linen), skin pores, stone grit",
                "Style": "National Geographic Documentary Style (NOT 3D Render)"
            },
            
            imperfections=[
                "Dust in the air from unpaved roads",
                "Paint chipping on statues/columns (Polychromy)",
                "Sweat and grease on skin (specular highlights)",
                "Refuse/debris in street corners",
                "Harsh shadows, high contrast"
            ],
            
            forbidden=[
                "Illustration", "Digital Painting", "Drawing", "CGI", "3D Render", "Cartoon",
                "Knitted clothing", "Cardigans", "Buttons", "Zippers", "Tailored jackets with sleeves", 
                "Pure white marble city", "Modern Italian elements", "Glasses", "Asphalt", "Sepia"
            ],
            
            props_required=[
                "Wax tablets with stylus", "Amphorae (rough clay)", "Latin signage (hand-painted)", 
                "Oil lamps", "Rough woven baskets", "Frescoes with patina"
            ],
            
            shot_menu=[
                "Eye-level street photography in a crowd",
                "Close-up portrait emphasizing skin texture and imperfections",
                "Wide establishing shot with atmospheric dust",
                "Detail shot of rough Roman daily objects"
            ],
            
            cultural_behavior=[
                "Expressive Italian-style hand gestures",
                "Public life happens outdoors",
                "Visible social stratification"
            ],
            social_norms=[
                "Outerwear is DRAPED (Toga/Palla/Cloak), NEVER fitted/buttoned",
                "Tunic as base layer (linen/wool)",
                "Women wearing Stolas (layered)",
                "No public affection"
            ],
            
            gemini_style_keywords=(
                "Ancient Rome documentary photography, hyper-realistic photo, 8k, highly detailed textures, "
                "dusty streets, authentic roman clothing (draped wool/linen), chipping paint on marble, "
                "harsh sunlight, leica photography, raw sensor data, NOT an illustration"
            ),
            
            vision_pass_score=85,
            vision_criteria=[
                VisionCriterion(
                    id="photorealism_check",
                    description="Image must look like a PHOTO, not a drawing or 3D render. Skin must have pores, light must behave physically.",
                    weight=40,
                    is_critical=True,
                    failure_hint="add noise, skin texture and remove 'painterly' effects"
                ),
                VisionCriterion(
                    id="period_clothing_check",
                    description="Clothing must be draped (Toga/Palla/Tunic). NO buttons, NO zippers, NO knitted fabric, NO modern fitted jackets.",
                    weight=35,
                    is_critical=True,
                    failure_hint="replace jacket with a draped woolen cloak (Palla)"
                ),
                VisionCriterion(
                    id="polychromy_check",
                    description="Statues and buildings show signs of paint (or faded paint), not just white marble.",
                    weight=25,
                    failure_hint="add faded paint to stone surfaces"
                )
            ]
        ),
        
        "Altes Griechenland (Klassik)": PresetConfig(
            name="Hellenistic Light (Time Portal)",
            version="2.0.0",
            preset_intent="To capture the philosophical and aesthetic grandeur of Ancient Greece in perfect high definition. Emphasizing the unique 'Attic light', coastal atmosphere, and intellectual vibrancy.",
            recommended_use="Für Szenen auf der Agora, in Tempeln, Symposien. Symmetrie, Licht und Philosophie in 8K.",
            
            camera="Hasselblad X2D 100C",
            lens="80mm f/1.9",
            film_stock="Digital Medium Format (Vibrant Blues/Golds)",
            lighting="Golden Hour, reflected sea light, or open shade",
            
            capture_profile={
                "Resolution": "100MP detail",
                "Light Quality": "Hard-edged shadows, high clarity air",
                "Color Palette": "Gold, White, Deep Blue, Terracotta",
                "Atmosphere": "Salt haze, wind, crispness"
            },
            
            imperfections=[
                "Sun flare and strong atmospheric haze",
                "Sea salt texture in air/skin",
                "Wind-blown hair and clothing",
                "Pigment fading on sun-exposed painted friezes",
                "Organic fabric irregularities"
            ],
            forbidden=[
                "White ruins (buildings are intact)", "Concrete", "Modern tourism", 
                "Industrial smog", "Artificial light", "Paper books", "Medieval armor", 
                "Vintage Filter", "Tourist vibe"
            ],
            
            props_required=[
                "Clay amphorae/kylix (black/red figure)", "Olive branches/trees", 
                "Papyrus scrolls (rolled)", "Frankincense smoke", "Bronze tripods", 
                "Mosaic floors"
            ],
            
            shot_menu=[
                "Symmetrical composition centered on architecture",
                "Portrait with sea background (bokeh)",
                "Low angle looking up at a statue/temple",
                "Group conversation shot (Symposium)"
            ],
            
            cultural_behavior=[
                "Conversational groupings (circular)",
                "Athletic/Physical confidence (gymnasium culture)",
                "Contemplative, relaxed postures",
                "Reclining while eating/drinking"
            ],
            social_norms=[
                "Oiled skin (gymnasium context)",
                "Gender segregation in public spaces",
                "Civic pride/engagement visible",
                "Respectful distance in sacred spaces"
            ],
            
            gemini_style_keywords=(
                "Ancient Greece photorealism, assassin's creed odyssey aesthetic style but real photo, "
                "golden hour, mediterranean light, vivid colors, painted temples, "
                "historical accuracy, detailed fabrics, 8k resolution, crisp atmosphere"
            ),
            
            vision_pass_score=82,
            vision_criteria=[
                VisionCriterion(
                    id="coastal_atmosphere",
                    description="Lighting captures the sharp, golden quality of the Mediterranean sun with sea haze.",
                    weight=30,
                    failure_hint="increase lighting contrast, warmth and clarity"
                ),
                VisionCriterion(
                    id="intact_polychromy",
                    description="Temples are fully intact and painted. No ruins, no pure white stone.",
                    weight=35,
                    is_critical=True,
                    failure_hint="repair buildings and apply decorative paint"
                ),
                VisionCriterion(
                    id="period_materials_bronze",
                    description="Metal objects are Bronze (gold/brown), NOT Steel (grey). Pottery is Clay.",
                    weight=35,
                    is_critical=True,
                    failure_hint="change grey metal to bronze/gold color"
                )
            ]
        ),
        
        "Altes Ägypten (Neues Reich)": PresetConfig(
            name="Pharaonic Realism (Time Portal)",
            version="1.2.0",
            
            # INTENT: Fokus auf FOTO und ALLTAG
            preset_intent=(
                "Ancient Egypt (New Kingdom) captured through a time-portal as a modern documentary PHOTOGRAPH. "
                "THIS IS NOT A PAINTING. THIS IS A REAL PHOTO. "
                "Everyday life along the Nile: working, trading, farming, transport, household routines. "
                "Historically accurate clothing, materials, tools, architecture and color. "
                "Natural optics, natural skin, real weathered usage (lived-in) but NOT ruined or abandoned."
            ),
            
            recommended_use=(
                "Für Alltagsszenen am Nil: Dörfer, Felder, Flussufer, Markt, Handwerk. "
                "Ziel: National-Geographic-artige Dokumentarfotografie ohne Film-Look, ohne Illustration."
            ),
            
            # TECHNIK: Neutral und Dokumentarisch
            camera="High-resolution documentary photograph (RAW-like)",
            lens="Natural perspective, 50-85mm equivalent",
            film_stock="Digital RAW (Neutral / True Color)",
            lighting="Natural Nile daylight: harsh sun with warm sand bounce fill, or open-shade",
            
            capture_profile={
                "Resolution": "High-resolution photo realism",
                "Texture": "Tangible micro-textures (skin pores, linen weave, wood grain, fired clay)",
                "Style": "Documentary photojournalism (live action)",
                "Color": "True-to-life daylight color, mineral pigments, no oversaturation",
                "Optics": "Natural depth of field, no painterly rendering"
            },
            
            imperfections=[
                "Fine dust on sandals",
                "Sweat sheen on skin (heat)",
                "Fly wisps or insects",
                "Oily residue on skin (scented oils)",
                "Heat shimmer"
            ],
            
            forbidden=[
                "Illustration", "Digital painting", "Concept art", "3D render", "CGI", "Cartoon",
                "Cel shading", "Lineart", "Brushstrokes", "Painterly", "Anime style",
                "Sepia", "Vintage filter", "Film grain overlay", "Teal and orange", "HDR halos",
                "Waxy skin", "Plastic skin", "Over-smoothed faces",
                "Ruins", "Collapsed temple", "Post-apocalyptic", "Museum exhibit", "Tourists",
                "Camels", "Iron", "Steel", "Cotton", "Silk", "Mummy wrappings on living people",
                "Leather belt", "Buckles",
                "Modern hairstyles", "Pixie cut", "Bob cut", "Loose flowing hair", "Bangs", "Messy hair"
            ],
            
            props_required=[
                "White pleated linen (semi-sheer)", "Faience jewelry (Turquoise/Blue)", 
                "Gold collars", "Kohl eyeliner",
                "Heavy black braided wigs OR Linen head-cloths (Khat)",
                "Mudbrick architecture", "Papyrus"
            ],
            
            shot_menu=[
                "Wide shot of Nile riverbank with workers and boats",
                "Medium shot of craftsmen at work (pottery, weaving, metalwork)",
                "Close-up of hands working with tools or materials",
                "Market scene with vendors and customers"
            ],
            
            cultural_behavior=[
                "Formal, dignified postures in public spaces",
                "Hierarchical social interactions visible",
                "Ritual and religious gestures in appropriate contexts"
            ],
            
            social_norms=[
                "Hair is either SHAVED, covered by a HEADCLOTH, or a braided black WIG. No loose/modern hair.",
                "Heavy Kohl eyeliner on men and women",
                "Clothing is White Linen",
                "Feet are bare or reed sandals"
            ],
            
            gemini_style_keywords=(
                "Ancient Egypt documentary photography, hyper-realistic photo, 8k, highly detailed textures, "
                "Nile riverbank, authentic egyptian clothing (white linen, pleated), kohl eyeliner, "
                "harsh sunlight, documentary photography, raw sensor data, NOT an illustration"
            ),
            
            vision_pass_score=90,
            vision_criteria=[
                VisionCriterion(
                    id="photo_not_art_hard_gate",
                    description="Must read as a real documentary PHOTOGRAPH (no painterly strokes, no illustration lines, no CGI smoothness).",
                    weight=50,
                    is_critical=True,
                    failure_hint="Make it look like an ungraded RAW photo; remove illustration/CGI effects."
                ),
                VisionCriterion(
                    id="historical_material_culture",
                    description="Includes credible New Kingdom materials: linen, pottery, reed, wood, mudbrick. No modern items.",
                    weight=25,
                    is_critical=True,
                    failure_hint="Replace modern objects with linen, pottery, reed, wood."
                ),
                VisionCriterion(
                    id="no_ruins_no_tourist",
                    description="Scene must NOT look like ruins, excavation, or museum. It should feel lived-in and functioning.",
                    weight=15,
                    is_critical=True,
                    failure_hint="Make the settlement maintained and active; remove ruins and museum cues."
                ),
                VisionCriterion(
                    id="daylight_color_realism",
                    description="Natural daylight color: no sepia/vintage, no heavy grading. Realistic shadow density.",
                    weight=10,
                    failure_hint="Use neutral RAW-like color with natural daylight."
                )
            ]
        ),
        
        "Altes Rom (Imperium)": PresetConfig(
            name="Ancient Rome Unfiltered (Time Portal)",
            version="2.3.0",
            preset_intent="Imperial Rome in 8K. NO FANTASY LEATHER. Clothing is draped Wool/Linen (Toga/Tunica). City is crowded, painted, and dirty. Not a museum.",
            recommended_use="Straßen, Senat, Alltag. Das echte, dreckige, bunte Rom.",
            
            camera="Leica SL2",
            lens="50mm f/0.95",
            film_stock="Digital RAW (Natural)",
            lighting="Harsh Sun or Oil Lamps",
            
            capture_profile={
                "Resolution": "8K",
                "Color": "Natural, dusty, vibrant paint",
                "Texture": "Wool, Linen, Stone, Sweat"
            },
            
            imperfections=["Dust", "Paint chipping", "Graffiti", "Sweat", "Street debris"],
            
            forbidden=[
                "Leather armor on civilians", "Leather bracers", "Fantasy leather", 
                "Tailored jackets", "Buttons", "Zippers", "Knitted fabric", 
                "Pure white city", "Ruins", "Modern Italy"
            ],
            
            props_required=[
                "Woolen Togas (Citizens)", "Linen Tunics (Commoners)", "Wax tablets", 
                "Oil lamps", "Graffiti on walls", "Painted statues"
            ],
            
            shot_menu=["Street crowd", "Close-up portrait", "Wide temple shot"],
            
            cultural_behavior=["Expressive gestures", "Public life outdoors"],
            social_norms=[
                "Clothing is DRAPED (wrapped), never buttoned or fitted.",
                "Leather is for soldiers/sandals only.",
                "Women wear Stolas (layered)."
            ],
            
            gemini_style_keywords="Ancient Rome photorealism, crowded streets, wool togas, graffiti, dust, 8k, raw",
            
            vision_pass_score=85,
            vision_criteria=[
                VisionCriterion(id="draped_clothing", description="Clothing must be wrapped/draped. No buttons/seams.", weight=40, is_critical=True, failure_hint="change to draped toga/tunic"),
                VisionCriterion(id="no_fantasy_leather", description="No leather arm guards or vests on civilians.", weight=30, is_critical=True, failure_hint="remove leather armor"),
                VisionCriterion(id="living_city", description="City is painted and lived-in, not white ruins.", weight=30, failure_hint="add paint and dirt")
            ]
        ),
        
        "Altes Griechenland (Klassik)": PresetConfig(
            name="Hellenistic Light (Time Portal)",
            version="2.0.0",
            preset_intent="To capture the philosophical and aesthetic grandeur of Ancient Greece in perfect high definition. Emphasizing the unique 'Attic light', coastal atmosphere, and intellectual vibrancy.",
            recommended_use="Für Szenen auf der Agora, in Tempeln, Symposien. Symmetrie, Licht und Philosophie in 8K.",
            
            camera="Hasselblad X2D 100C",
            lens="80mm f/1.9",
            film_stock="Digital Medium Format (Vibrant Blues/Golds)",
            lighting="Golden Hour, reflected sea light, or open shade",
            
            capture_profile={
                "Resolution": "100MP detail",
                "Light Quality": "Hard-edged shadows, high clarity air",
                "Color Palette": "Gold, White, Deep Blue, Terracotta",
                "Atmosphere": "Salt haze, wind, crispness"
            },
            
            imperfections=[
                "Sun flare and strong atmospheric haze",
                "Sea salt texture in air/skin",
                "Wind-blown hair and clothing",
                "Pigment fading on sun-exposed painted friezes",
                "Organic fabric irregularities"
            ],
            forbidden=[
                "White ruins (buildings are intact)", "Concrete", "Modern tourism", 
                "Industrial smog", "Artificial light", "Paper books", "Medieval armor", 
                "Vintage Filter", "Tourist vibe"
            ],
            
            props_required=[
                "Clay amphorae/kylix (black/red figure)", "Olive branches/trees", 
                "Papyrus scrolls (rolled)", "Frankincense smoke", "Bronze tripods", 
                "Mosaic floors"
            ],
            
            shot_menu=[
                "Symmetrical composition centered on architecture",
                "Portrait with sea background (bokeh)",
                "Low angle looking up at a statue/temple",
                "Group conversation shot (Symposium)"
            ],
            
            cultural_behavior=[
                "Conversational groupings (circular)",
                "Athletic/Physical confidence (gymnasium culture)",
                "Contemplative, relaxed postures",
                "Reclining while eating/drinking"
            ],
            social_norms=[
                "Oiled skin (gymnasium context)",
                "Gender segregation in public spaces",
                "Civic pride/engagement visible",
                "Respectful distance in sacred spaces"
            ],
            
            gemini_style_keywords=(
                "Ancient Greece photorealism, assassin's creed odyssey aesthetic style but real photo, "
                "golden hour, mediterranean light, vivid colors, painted temples, "
                "historical accuracy, detailed fabrics, 8k resolution, crisp atmosphere"
            ),
            
            vision_pass_score=82,
            vision_criteria=[
                VisionCriterion(
                    id="coastal_atmosphere",
                    description="Lighting captures the sharp, golden quality of the Mediterranean sun with sea haze.",
                    weight=30,
                    failure_hint="increase lighting contrast, warmth and clarity"
                ),
                VisionCriterion(
                    id="intact_polychromy",
                    description="Temples are fully intact and painted. No ruins, no pure white stone.",
                    weight=35,
                    is_critical=True,
                    failure_hint="repair buildings and apply decorative paint"
                ),
                VisionCriterion(
                    id="period_materials_bronze",
                    description="Metal objects are Bronze (gold/brown), NOT Steel (grey). Pottery is Clay.",
                    weight=35,
                    is_critical=True,
                    failure_hint="change grey metal to bronze/gold color"
                )
            ]
        )
    },
    
    # --- NEUE, INTELLIGENTE ZEITREISE-KATEGORIE ---
    "Zeitreise (Hyper-Realismus)": {
        "Steinzeit": PresetConfig(
            name="Paleolithic Era (Time Portal)", version="3.0-Tiered",
            preset_intent="Capture the raw Stone Age. NO WOVEN FABRIC. NO METAL. Clothing is raw animal hide/fur only.",
            recommended_use="Jäger & Sammler. Authentische Darstellung ohne Zivilisation.",
            camera="Fujifilm GFX 100S", lens="50mm f/1.4", film_stock="Digital RAW", lighting="Natural Light or Firelight",
            capture_profile={"Style": "Documentary Realism"},
            global_forbidden=["Woven Fabric", "Metal", "Agriculture", "Roads", "Modern Teeth"],
            default_tier="hunter",
            social_tiers=[
                SocialTier(tier_id="hunter", keywords=["hunter", "gatherer", "jäger", "sammler", "frau", "mann"], description="A standard member of a hunter-gatherer tribe.",
                           textiles=["Raw, untanned animal hides with fur", "Leather thongs"], colors=["Natural brown, grey, white"],
                           headwear=["None", "Simple bone/feather ornaments"], footwear=["Barefoot", "Simple hide wrappings"],
                           props=["Flint spearhead", "Wooden spear", "Bone needle", "Stone axe"], locations=["Cave entrance", "Forest", "Rocky outcrop"],
                           forbidden=[])
            ]
        ),
        "Altes Ägypten": PresetConfig(
            name="Ancient Egypt (Time Portal)", version="2.0-Tiered",
            preset_intent="Capture authentic life in Ancient Egypt (New Kingdom), adapting to social class.",
            recommended_use="Alltag am Nil. Beschreibe den Status (Bauer, Priester, Pharao).",
            camera="Hasselblad H6D-100c", lens="80mm f/2.8", film_stock="Digital RAW", lighting="Harsh Desert Sun or Oil Lamps",
            capture_profile={"Style": "Documentary"},
            global_forbidden=["Ruins", "Camels", "Iron/Steel", "Cotton", "Silk", "Modern Hairstyles"],
            default_tier="commoner",
            social_tiers=[
                SocialTier(tier_id="commoner", keywords=["commoner", "peasant", "farmer", "worker", "craftsman", "bauer", "arbeiter"], description="A poor worker or farmer by the Nile.",
                           textiles=["Coarse, undyed (off-white) linen"], colors=["Natural beige"],
                           headwear=["Shaved head", "Simple linen head-cloth"], footwear=["Barefoot", "Reed sandals"],
                           props=["Clay pottery", "Reed baskets", "Wooden farming tools"], locations=["Mudbrick village", "Fields by the Nile"],
                           forbidden=["Gold", "Lapis Lazuli", "Fine pleated linen"]),
                SocialTier(tier_id="noble", keywords=["noble", "priest", "priestess", "pharaoh", "queen", "adel", "priester", "pharao"], description="A high-status individual in a temple or palace.",
                           textiles=["Fine, pleated white linen", "Sheer fabrics"], colors=["White, with accents of blue, red"],
                           headwear=["Heavy black braided wig", "Royal headdress"], footwear=["Elaborate sandals"],
                           props=["Gold Usekh collar", "Lapis Lazuli jewelry", "Bronze mirror"], locations=["Polished stone temple", "Throne room"],
                           forbidden=["Mud", "Farming tools"])
            ]
        ),
        "Altes Rom": PresetConfig(
            name="Ancient Rome (Time Portal)", version="3.0-Tiered",
            preset_intent="Capture authentic life in Imperial Rome, adapting to social class. NO FANTASY LEATHER.",
            recommended_use="Straßen, Senat, Alltag. Beschreibe den Status (Bürger, Senator, Soldat).",
            camera="Leica SL2", lens="50mm f/0.95", film_stock="Digital RAW", lighting="Harsh Sun or Oil Lamps",
            capture_profile={"Style": "Street/Documentary"},
            global_forbidden=["Ruins", "Modern Italy", "Fantasy Armor", "Knitted Fabric"],
            default_tier="plebeian",
            social_tiers=[
                SocialTier(tier_id="plebeian", keywords=["plebeian", "citizen", "worker", "craftsman", "bürger", "arbeiter"], description="A common citizen in the bustling, dirty streets of Rome.",
                           textiles=["Coarse wool tunic"], colors=["Undyed off-white, earth tones"],
                           headwear=["None"], footwear=["Leather sandals (caligae)"],
                           props=["Clay amphorae", "Woven baskets", "Simple tools"], locations=["Crowded market street", "Insulae apartments"],
                           forbidden=["Toga", "Purple cloth", "Silk"]),
                SocialTier(tier_id="patrician", keywords=["patrician", "senator", "noble", "patrizier"], description="A wealthy patrician or senator in a formal setting.",
                           textiles=["Fine wool toga", "Linen undertunic"], colors=["White, with purple stripe (toga praetexta)"],
                           headwear=["None"], footwear=["Fine leather sandals"],
                           props=["Papyrus scrolls", "Marble busts", "Mosaic floors"], locations=["Marble villa", "Senate house (Curia)"],
                           forbidden=["Peasant tools", "Mudbrick"]),
                SocialTier(tier_id="legionary", keywords=["legionary", "soldier", "centurion", "legionär", "soldat"], description="A Roman legionary soldier on duty.",
                           textiles=["Wool tunic (red)"], colors=["Red, brown"],
                           headwear=["Iron helmet (galea)"], footwear=["Hobnailed sandals (caligae)"],
                           props=["Segmented armor (lorica segmentata)", "Shield (scutum)", "Short sword (gladius)"], locations=["Fortress wall", "Marching on a stone road"],
                           forbidden=["Toga", "Civilian life props"])
            ]
        ),
        "Altes Griechenland": PresetConfig(
            name="Ancient Greece (Time Portal)", version="3.0-Tiered",
            preset_intent="Capture authentic life in Classical Greece, adapting to social class. POLYCHROMY (painted world).",
            recommended_use="Agora, Tempel, Schlachtfeld. Beschreibe den Status (Bürger, Philosoph, Hoplit).",
            camera="Hasselblad X2D 100C", lens="50mm f/1.8", film_stock="Digital RAW", lighting="Harsh Attic Light",
            capture_profile={"Style": "Documentary"},
            global_forbidden=["Ruins", "White marble statues", "Steel", "Medieval armor"],
            default_tier="citizen",
            social_tiers=[
                SocialTier(tier_id="citizen", keywords=["citizen", "philosopher", "orator", "bürger", "philosoph"], description="A citizen or philosopher in public life.",
                           textiles=["Linen or light wool chiton/himation"], colors=["White, saffron, light blue"],
                           headwear=["None"], footwear=["Barefoot", "Simple leather sandals"],
                           props=["Papyrus scrolls", "Walking stick", "Clay kylix (cup)"], locations=["Agora (market)", "Painted stoa"],
                           forbidden=["Armor", "Weapons"]),
                SocialTier(tier_id="hoplite", keywords=["hoplite", "soldier", "spartan", "soldat"], description="A hoplite soldier in formation.",
                           textiles=["Linen tunic (linothorax reinforcement)"], colors=["Red, white"],
                           headwear=["Bronze Corinthian helmet"], footwear=["Leather sandals"],
                           props=["Bronze cuirass", "Round shield (Hoplon)", "Long spear (Dory)"], locations=["Battlefield", "Phalanx formation"],
                           forbidden=["Toga", "Scrolls"])
            ]
        ),
        "Mittelalter": PresetConfig(
            name="High Middle Ages (Time Portal)", version="2.0-Tiered",
            preset_intent="Capture authentic life in High Middle Ages (c. 1250, N. Europe), adapting to social class.",
            recommended_use="Dörfer, Höfe, Schlachten. Beschreibe den Status (Bauer, Ritter, König).",
            camera="Sony A7S III", lens="50mm f/1.2", film_stock="Digital RAW", lighting="Natural/Candlelight",
            capture_profile={"Style": "Gritty Documentary"},
            global_forbidden=["Plate Armor (anachronistic)", "Fantasy elements", "Cleanliness", "Modern boots", "Modern belt buckles", "Factory-made belts"],
            default_tier="peasant",
            social_tiers=[
                SocialTier(tier_id="peasant", keywords=["peasant", "farmer", "craftsman", "bauer", "handwerker"], description="A peasant or craftsman in a muddy village.",
                           textiles=["Coarse wool tunic", "Linen undertunic"], colors=["Undyed, earth tones"],
                           headwear=["Linen coif or hood"], footwear=["Leather turnshoes"],
                           props=["Wooden bucket", "Iron tools", "Clay pottery", "Simple leather belt (tied, no buckle)"], locations=["Muddy village street", "Thatched-roof hut"],
                           forbidden=["Silk", "Velvet", "Crowns", "Swords", "Metal buckles"]),
                SocialTier(tier_id="noble", keywords=["noble", "knight", "king", "queen", "adel", "ritter", "könig", "herrscher", "königin"], description="A noble or knight at court or in the field.",
                           textiles=["Fine wool, silk trim, velvet, fur"], colors=["Vibrant plant/insect dyes (red, blue)"],
                           headwear=["Circlet", "Linen veil (women)"], footwear=["Pointed leather shoes"],
                           props=["Sword", "Tapestries", "Gold goblet", "Chainmail hauberk", "Leather belt with historical ring buckle"], locations=["Stone castle interior", "Tournament field"],
                           forbidden=["Farming tools", "Mudbrick huts", "Modern belt buckles"])
            ]
        )
    },
    
    # --- NEUE, INTELLIGENTE ZEITREISE-KATEGORIE ---
}

def _compile_instruction(config: PresetConfig, provider: str, user_prompt: str) -> str:
    """Baut eine universelle, intelligente und abwärtskompatible Instruktion."""
    
    framing_rule_text = (
        "4. MANDATORY FRAMING (PLAN B): Generate in 1024x1536 and crop later. Use 'American Shot (Knees up)' with headroom.\n"
    )
    
    # 1. Prüfen, ob das neue TIER-System verwendet wird
    if config.social_tiers:
        # Hierarchische Tier-Auswahl
        selected_tier = None
        tier_hierarchy = ["legionary", "hoplite", "noble", "patrician", "plebeian", "citizen", "commoner", "peasant", "hunter"]
        sorted_tiers = sorted(config.social_tiers, key=lambda t: tier_hierarchy.index(t.tier_id) if t.tier_id in tier_hierarchy else 99)
        for tier in sorted_tiers:
            if any(keyword.lower() in user_prompt.lower() for keyword in tier.keywords):
                selected_tier = tier
                break
        if not selected_tier:
            selected_tier = next((t for t in config.social_tiers if t.tier_id == config.default_tier), config.social_tiers[0])
        
        # Regelblöcke für TIER-System
        tier_options_text = ""
        for tier in config.social_tiers:
            tier_options_text += f"- Tier ID '{tier.tier_id}': Triggered by {tier.keywords}\n"
        
        analysis_instruction = (
            "STEP 1: ANALYZE AND SELECT TIER\n"
            f"Scan 'USER REQUEST' and select ONE social tier. Default is '{config.default_tier}'.\n{tier_options_text}\n"
            "STEP 2: APPLY RULES\n"
            "Use ONLY the rules for the selected tier.\n\n"
        )
        
        all_tier_rules_text = ""
        for tier in config.social_tiers:
            all_tier_rules_text += (
                f"--- RULES FOR TIER '{tier.tier_id}' ---\n"
                f"Description: {tier.description}\n"
                f"Textiles: {', '.join(tier.textiles)}\n"
                f"Props: {', '.join(tier.props)}\n"
                f"Locations: {', '.join(tier.locations)}\n"
                f"Forbidden: {', '.join(tier.forbidden)}\n\n"
            )
        
        final_forbidden = config.global_forbidden
    
    # 2. FALLBACK für ALTE PRESETS (ohne Tiers)
    else:
        analysis_instruction = ""
        all_tier_rules_text = (
             f"RULES:\n"
             f"- Imperfections: {', '.join(getattr(config, 'imperfections', []))}\n"
             f"- Social Norms: {', '.join(getattr(config, 'social_norms', []))}\n"
        )
        final_forbidden = getattr(config, 'forbidden', [])

    forbidden_list = ", ".join([f"'{f}'" for f in final_forbidden])
    
    provider_specific_style_command = ""
    if provider == 'gemini':
        provider_specific_style_command = f"CRITICAL: Adhere to these style keywords: {config.gemini_style_keywords}\n\n"
    
    # 3. Finalen Prompt zusammenbauen
    return (
        f"ROLE:\n"
        f"You are a photographic prompt engineer. Your task is to apply a strict ruleset to a user request.\n"
        f"CRITICAL: The final image must look like a PHOTOGRAPH, not a painting.\n\n"
        
        f"{analysis_instruction}"
        f"AVAILABLE RULESETS:\n{all_tier_rules_text}"
        
        f"GLOBAL RULES (APPLY ALWAYS):\n"
        f"- Global Forbidden: {forbidden_list}\n"
        f"- Camera: {config.camera}, {config.lens}\n"
        f"{provider_specific_style_command}"
        
        f"GLOBAL FRAMING RULE (APPLY ALWAYS):\n{framing_rule_text}\n"
        
        f"EXECUTION:\nRewrite the user request according to the rules and generate the image.\n\n"
        
        f"USER REQUEST:\n"
        f"{user_prompt}"
    )

# --- 4. PUBLIC API ---

def get_preset(provider: str, style: str, variation: str, user_prompt: str) -> Tuple[Optional[PresetConfig], str]:
    """
    Sucht das Config-Objekt und gibt es zusammen mit dem kompilierten Prompt zurück.
    Gibt (None, user_prompt) zurück, wenn kein Preset gefunden wird.
    """
    try:
        # 1. Preset in der Datenbank suchen
        preset = PRESET_DATABASE.get(style, {}).get(variation)
        if not preset:
            logger.warning(f"Preset nicht gefunden: {style} / {variation}")
            return None, user_prompt
            
        # 2. Instruktion kompilieren
        instruction = _compile_instruction(preset, provider, user_prompt)
        
        # 3. Falls der User einen Prompt hat, diesen anhängen
        final_prompt = instruction
        if user_prompt and user_prompt.strip():
            final_prompt = f"{instruction}\n\n{user_prompt}"
            
        return preset, final_prompt
        
    except Exception as e:
        logger.error(f"Fehler beim Laden des Presets {style}/{variation}: {str(e)}")
        logger.error(f"Fehler beim Bauen des Presets: {e}", exc_info=True)
        return None, user_prompt


def generate_preview_prompt(config: PresetConfig) -> str:
    """
    Generiert den 'Diamant-Standard' Master-Prompt für ein einheitliches Vorschaubild.
    Füllt Slots (Material, Prop, Welt) dynamisch basierend auf der Preset-Konfiguration.
    """
    
    # 1. WORLD_TAG (Aus Namen und Intent ableiten)
    world_tag = f"{config.name} ({config.preset_intent[:80]}...)"
    
    # 2. MATERIAL_FOCUS & PROP LOGIK (Aus Tiers oder Defaults ableiten)
    material_hint = "fabric/leather/metal"
    prop_choice = "small coin with worn relief engraving" # Default für Historie
    
    if config.social_tiers:
        # Nimm den ersten Tier als Referenz für das Hauptmaterial
        tier = config.social_tiers[0]
        if tier.textiles:
            # Nimm das erste Textil als Material-Hinweis
            material_hint = tier.textiles[0]
        
        # Intelligente Prop-Wahl basierend auf dem Namen
        lower_name = config.name.lower()
        if "sci-fi" in lower_name or "cyber" in lower_name:
            prop_choice = "small data chip with micro-structure and contacts"
        elif "fantasy" in lower_name or "magic" in lower_name:
            prop_choice = "small amulet with etched patterns"
        elif "medieval" in lower_name or "ancient" in lower_name or "rome" in lower_name or "egypt" in lower_name or "stone" in lower_name:
            prop_choice = "small coin with worn relief engraving" # Historisch neutral
        else:
            prop_choice = "small key with teeth detail" # Modern/Neutral

    # 3. HERO_MATERIAL (Automatisch zusammengebaut)
    # Priorität A: Belt + Hardware (funktioniert fast immer)
    hero_material = f"belt with {material_hint} texture and crisp edges"
    
    # 4. DER SUPERPROMPT (Diamant-Standard Template)
    master_prompt = (
        f"TASK: Generate one single preview image showcasing the style: '{config.name}'. "
        f"STYLE: Render strictly in the selected preset's style. Maximize signature strengths, keeping composition identical. "
        f"COMPOSITION (locked): One single adult female character, centered, medium shot (mid-torso to head), facing camera, neutral expression, clear silhouette. "
        f"WARDROBE: Typical everyday clothing for {world_tag}. Include one prominent 'hero material' element: {hero_material}. It must have visible texture and crisp edges. "
        f"HAND PROP: One hand holds a {prop_choice} at chest level with crisp micro-detail. "
        f"BACKGROUND (locked): Simple environment with 1-2 large shapes (wall/arch), calm, out of focus. No crowds. "
        f"LIGHTING (locked): Clear readable setup: key light 45 deg front, soft fill, subtle rim light. "
        f"CAMERA (locked): Eye level, neutral perspective, 50mm equivalent. "
        f"QUALITY: High clarity on face, hands, and prop. Balanced exposure. "
        f"OUTPUT: Single image only. No text, no watermark."
    )
    
    return master_prompt