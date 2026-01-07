# backend/data/presets.py

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
import logging

logger = logging.getLogger("janus_backend")

# --- 1. DATENKLASSEN ---
@dataclass
class VisionCriterion:
    id: str
    description: str
    weight: int
    failure_hint: Optional[str] = None
    is_critical: bool = False

@dataclass
class PresetConfig:
    name: str
    version: str
    preset_intent: str
    recommended_use: str 
    
    # Physikalisches Modell
    camera: str
    lens: str
    film_stock: str
    lighting: str
    
    # Visuelle Signatur
    imperfections: List[str]
    forbidden: List[str]
    
    # --- NEU: Kulturelle & Soziale Regeln (für echte Zeitreisen) ---
    cultural_behavior: List[str] = field(default_factory=list) # z.B. "Formal posture"
    social_norms: List[str] = field(default_factory=list)      # z.B. "No smiling"
    
    # Provider-spezifische Übersetzung
    gemini_style_keywords: str = "Photorealistic"
    
    # Validierungs-Regeln
    vision_criteria: List[VisionCriterion] = field(default_factory=list)
    vision_pass_score: int = 75
    
    def __post_init__(self):
        required_fields = {
            'name': self.name,
            'version': self.version,
            'preset_intent': self.preset_intent,
            'recommended_use': self.recommended_use,
            'camera': self.camera,
            'lens': self.lens,
            'film_stock': self.film_stock,
            'lighting': self.lighting,
            'imperfections': self.imperfections,
            'forbidden': self.forbidden
        }
        
        missing_fields = [field for field, value in required_fields.items() if not value]
        if missing_fields:
            raise ValueError(f"Preset '{self.name}' Error: Fehlende Pflichtfelder: {', '.join(missing_fields)}")
            
        if not isinstance(self.vision_criteria, list) or not all(isinstance(c, VisionCriterion) for c in self.vision_criteria):
            raise ValueError("vision_criteria muss eine Liste von VisionCriterion-Objekten sein")

# --- 2. DIE PRESET-DATENBANK (Komplett auf DEUTSCH) ---

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
            
            gemini_style_keywords="Dokumentarischer Realismus, ungestellt, verfügbares Licht, RAW-Fotografie",
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
            gemini_style_keywords="Hochauflösende Porträtfotografie, professionelle Porträts",
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
            
            forbidden=["Schwebende Objekte", "Keine Schatten", "Perfekt zentriert", "CGI-artige Reflexionen", "Plastikoptik"],
            gemini_style_keywords="Kommerzielle Produktfotografie, sauberes Design, Studio-Beleuchtung",
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
    
    # --- NEUE KATEGORIE: Temporal Photorealism ---
    "Temporal Photorealism": {
        "1890 – Glass Plate Photography": PresetConfig(
            name="Early Photographic Realism (Glass Plate Era, ~1890)",
            version="1.1.0",
            preset_intent="To simulate the physical and cultural constraints of late 19th-century photography, focusing on technological and social norms of the era.",
            recommended_use="Ideal für historische Porträts, Stillleben oder Szenen, die eine authentische, ernste und unvollkommene Anmutung der Zeit erfordern.",
            
            # Physik
            camera="Large Format Glass Plate Camera",
            lens="Fixed focal length brass lens",
            film_stock="Orthochromatic glass plate emulsion",
            lighting="Strong natural daylight or window light",
            
            # Signatur & Regeln
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
            
            # Kulturelle & Soziale Regeln
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
            
            # Provider Keywords
            gemini_style_keywords=(
                "19th century photography, authentic glass plate photo, historical realism, "
                "early photographic process, natural light only, serious expression, victorian era"
            ),
            
            # Vision Gate
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
            
            gemini_style_keywords=(
                "1930s documentary photography, grainy black and white film, "
                "photojournalism realism, historical reportage, walker evans style"
            ),
            
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
            version="1.1.0", # Update für besseres Blending
            
            # Intent: Betonung auf Integration in die Umgebung trotz Blitz
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
                "Atmospheric haze blending subject and background", # WICHTIG: Verbindet Ebenen
                "Chromatic aberration typical of early zoom lenses"
            ],
            forbidden=[
                "Synthwave", "Retrowave", "Neon Grid", "CGI", "Illustration",
                "Vector art", "Modern HD", "Muted colors", "Digital noise",
                "Smartphones", "Flat screens", "Floating subject", "Bad compositing"
            ],
            
            # WICHTIG: Hier steuern wir Gemini
            gemini_style_keywords=(
                "1980s fashion photography, direct flash, fujicolor look, "
                "vibrant analog colors, soft focus highlights, editorial realism, "
                "volumetric lighting, subject grounded in environment" # Das zwingt zur Integration
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
    }
}

# --- 3. DEFAULT PRESET CONFIG ---
DEFAULT_GPT_PRESET_CONFIG = PresetConfig(
    name="Standard Fotorealismus",
    version="1.0.0",
    preset_intent="Standard-Preset für realistische Fotografie",
    recommended_use="Allgemeine Verwendung für realistische Bilder",
    camera="Standardkamera",
    lens="Standardobjektiv",
    film_stock="Standard-Film",
    lighting="Standardbeleuchtung",
    imperfections=["Leichtes Bildrauschen", "Natürliche Schärfe"],
    forbidden=["CGI", "Künstlich wirkende Elemente", "Unrealistische Beleuchtung"],
    cultural_behavior=["Natürliche Körpersprache", "Authentische Mimik"],
    social_norms=["Respektvoller Abstand", "Keine Berührung"]
)

def _compile_gpt_instruction(config: PresetConfig, user_prompt: str) -> str:
    """Baut die 'Reference Standard' System-Instruktion für GPT-5.2.
    """
    
    imperfections_list = "\n- ".join(config.imperfections)
    forbidden_list = ", ".join([f"'{f}'" for f in config.forbidden])
    
    # Neue Listen verarbeiten
    behavior_list = "\n- ".join(config.cultural_behavior) if config.cultural_behavior else "- Natural behavior"
    norms_list = "\n- ".join(config.social_norms) if config.social_norms else "- Standard norms"
    
    return (
        f"ROLE:\n"
        f"You are a photographic prompt engineer. You enforce a single, consistent look: {config.name}.\n"
        f"INTENT: {config.preset_intent}\n\n"
        
        f"HIERARCHY OF AUTHORITY (MANDATORY):\n"
        f"1. Preset physics and era accuracy override user intent.\n"
        f"2. Cultural and temporal rules override visual appeal.\n"
        f"3. User request is only adapted within these constraints.\n\n"
        
        f"PRESET IDENTITY:\n"
        f"- Camera: {config.camera}\n"
        f"- Lens: {config.lens}\n"
        f"- Material: {config.film_stock}\n"
        f"- Lighting: {config.lighting}\n\n"
        
        f"CULTURAL & SOCIAL CONSTRAINTS (THE 'VIBE'):\n"
        f"Behaviors:\n- {behavior_list}\n"
        f"Social Norms:\n- {norms_list}\n\n"
        
        f"STRICT RULES:\n"
        f"1. FORBIDDEN TOKENS: Do NOT use {forbidden_list}.\n"
        f"2. REQUIRED SIGNATURE: You MUST describe these exact imperfections:\n- {imperfections_list}\n"
        f"3. PHYSICS: Simulate the sensor behavior of a {config.camera}.\n\n"
        
        f"ANTI-DEVIATION:\n" 
        f"- Do not reinterpret the preset creatively.\n"
        f"- Do not adapt the style to the subject.\n\n"
        
        f"FAILURE CONDITION:\n" 
        f"If the user request conflicts with the preset, keep the preset and degrade the request.\n\n"

        f"EXECUTION INSTRUCTIONS (CRITICAL):\n"
        f"1. Rewrite the user request to strictly conform to this preset.\n"
        f"2. You MUST call the 'image_generation' tool.\n"
        f"3. The 'prompt' argument for the tool must contain ONLY your rewritten visual description.\n"
        f"4. Do NOT include these instructions in the tool prompt.\n\n"
        
        f"USER REQUEST:\n"
        f"{user_prompt}"
    )

def _compile_gemini_prompt(config: PresetConfig, user_prompt: str) -> str:
    """Baut den strikten Prompt für Gemini (Imagen 3)"""
    # Füge kulturelle Verhaltensweisen und soziale Normen hinzu, falls vorhanden
    cultural_context = ""
    if config.cultural_behavior or config.social_norms:
        cultural_context = " " + ". ".join(config.cultural_behavior + config.social_norms) + ". "
    
    return (
        f"Generate a strictly era-accurate {config.gemini_style_keywords} image of {user_prompt}. "
        f"Do NOT include any modern elements, digital aesthetics, or anachronistic details. "
        f"The result must appear as a genuine photograph from the specified era, not a modern recreation. "
        f"{cultural_context}"
        f"Camera: {config.camera} with {config.lens}. "
        f"Lighting: {config.lighting}. "
        f"Details: {', '.join(config.imperfections)}. "
        f"Quality: Best quality, high fidelity. "
        f"Strictly avoid: {', '.join(config.forbidden)}."
    )

# --- 4. PUBLIC API ---

def get_preset(provider: str, style: str, variation: str, user_prompt: str) -> Tuple[Optional[PresetConfig], str]:
    """
    Sucht das Config-Objekt und gibt es zusammen mit dem kompilierten Prompt zurück.
    Gibt (None, user_prompt) zurück, wenn kein Preset gefunden wird.
    """
    try:
        # 1. Config suchen
        category = PRESET_DATABASE.get(style)
        if not category:
            if provider == "openai":
                logger.info("Kein Preset gefunden. Fallback auf Default.")
                return DEFAULT_GPT_PRESET_CONFIG, _compile_gpt_instruction(DEFAULT_GPT_PRESET_CONFIG, user_prompt)
            return None, user_prompt
            
        config = category.get(variation)
        if not config:
            if provider == "openai":
                return DEFAULT_GPT_PRESET_CONFIG, _compile_gpt_instruction(DEFAULT_GPT_PRESET_CONFIG, user_prompt)
            return None, user_prompt

        logger.info(
            f"Preset applied",
            extra={"preset": config.name, "version": config.version, "provider": provider}
        )

        # 2. Prompt bauen
        if provider == "openai":
            return config, _compile_gpt_instruction(config, user_prompt)
        elif provider == "gemini":
            return config, _compile_gemini_prompt(config, user_prompt)
        else:
            return None, user_prompt
            
    except Exception as e:
        logger.error(f"Fehler beim Bauen des Presets: {e}", exc_info=True)
        # Safe Fallback
        if provider == "openai":
            return DEFAULT_GPT_PRESET_CONFIG, _compile_gpt_instruction(DEFAULT_GPT_PRESET_CONFIG, user_prompt)
        return None, user_prompt