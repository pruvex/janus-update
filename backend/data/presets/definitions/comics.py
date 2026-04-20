from ..models import PresetConfig, VisionCriterion

# v1.8.0 — The Ultimate Illustrative & Manga Diamond Standard (Merged Edition)
# Fix: Alle 8 Stile sind auf "Strict Full-Bleed" optimiert, um GPT-Ränder zu vermeiden.

presets = {
    # --- WESTLICHE COMIC-STILE ---

    "Golden Age (Vintage 1940s)": PresetConfig(
        name="Golden Age Style",
        version="1.8.0",
        preset_intent="Illustrationsstil von 1945. Fokus auf CMYK-Druckästhetik.",
        recommended_use="Superhelden-Stil der 40er Jahre.",
        camera="Professional Digital Scan", lens="Flat Field",
        film_stock="CMYK Ink Textures", lighting="Flat High-Contrast Inking",
        gemini_style_keywords=(
            "Digital art in 1940s ink-and-paint style. CMYK ink textures, thick clean black outlines. "
            "STRICT EDGE-TO-EDGE MANDATE: No borders, no margins, no paper edges. 100% canvas occupancy."
        ),
        vision_criteria=[VisionCriterion(id="zero_border_ga", description="Kein Rand.", weight=40, is_critical=True)]
    ),

    "Noir Graphic Novel (Tusche)": PresetConfig(
        name="Modern Noir Ink",
        version="1.8.0",
        preset_intent="Harter Schwarz-Weiß-Kontrast. Randlos.",
        recommended_use="Crime Stories, Thriller.",
        camera="Digital Ink", lens="Wide",
        film_stock="Pure Black & White", lighting="High Contrast Chiaroscuro",
        gemini_style_keywords=(
            "Noir graphic novel ink style, chiaroscuro. "
            "STRICT BORDERLESS: Full-bleed composition. No margins. Black ink touches all boundaries."
        ),
        vision_criteria=[VisionCriterion(id="noir_full_bleed", description="Keine Ränder.", weight=20, is_critical=True)]
    ),

    "Ligne Claire (Moebius Style)": PresetConfig(
        name="Ligne Claire Aesthetic",
        version="1.8.0",
        preset_intent="Präzise, gleichmäßig dicke Linien, flache Farben. Fokus auf architektonische Klarheit.",
        recommended_use="Sci-Fi, Architektur, europäische Graphic Novels.",
        camera="Technical Pen 0.5mm", lens="Infinite Depth",
        film_stock="Matte CMYK Profile", lighting="Uniform Ambient Light",
        gemini_style_keywords=(
            "Ligne claire style, Moebius aesthetic, clean outlines, flat colors, no hatching. "
            "STRICTLY BORDERLESS: Edge-to-edge illustration, no white space, artwork touches all boundaries."
        ),
        vision_criteria=[VisionCriterion(id="line_purity", description="Konstante Linienstärke.", weight=30)]
    ),

    "90s Extreme (Gritty Style)": PresetConfig(
        name="90s Gritty Comic",
        version="1.8.0",
        preset_intent="Aggressives Cross-Hatching, dynamische Perspektiven, Neon-Akzente.",
        recommended_use="Dark Fantasy, Action, Cyberpunk.",
        camera="Digital Action Camera", lens="Fisheye POV",
        film_stock="Vibrant Coated Ink", lighting="Multi-Directional Neon",
        gemini_style_keywords=(
            "90s gritty comic style, extreme cross-hatching, vibrant neon accents, dynamic perspective. "
            "MANDATORY: Full bleed, artwork fills every pixel of the canvas, no frames."
        ),
        vision_criteria=[VisionCriterion(id="hatching_check", description="Detaillierte Kreuzschraffur.", weight=20)]
    ),

    "Digital Painterly (Modern)": PresetConfig(
        name="Modern Graphic Novel",
        version="1.8.0",
        preset_intent="Malerischer digitaler Stil. Weiche Pinselstriche kombiniert mit scharfen Fokus-Linien.",
        recommended_use="Storytelling, Fantasy, emotionale Szenen.",
        camera="Cintiq 4K Rendering", lens="Digital Focus",
        film_stock="Digital Canvas", lighting="Volumetric Lighting",
        gemini_style_keywords=(
            "Painterly graphic novel style, digital art, volumetric light, soft brushstrokes, sharp focus lines. "
            "BORDERLESS: Edge-to-edge professional digital art, no frames, no white margins."
        ),
        vision_criteria=[VisionCriterion(id="focal_sharpness", description="Scharfe Linien am Motiv.", weight=20)]
    ),

    # --- JAPANISCHE MANGA & ANIME STILE ---

    "Studio Ghibli (Lush Fantasy)": PresetConfig(
        name="Ghibli Aesthetic",
        version="1.8.0",
        preset_intent="Simuliert handgezeichnete Gouache-Hintergründe und analoge Cel-Wärme.",
        recommended_use="Nostalgische, malerische Szenen, Natur.",
        camera="35mm Rostrum Camera", lens="Soft Focus Prime",
        film_stock="Fujicolor Animation Cel", lighting="Soft Ethereal Daylight",
        gemini_style_keywords=(
            "Studio Ghibli anime style, lush hand-painted gouache backgrounds, soft charcoal outlines. "
            "STRICTLY NO BORDERS: Full-bleed edge-to-edge, the art fills the entire canvas."
        ),
        vision_criteria=[VisionCriterion(id="gouache_check", description="Malerische Hintergrund-Textur.", weight=30)]
    ),

    "Neo-Tokyo 1988 (Cyberpunk-Stil)": PresetConfig( # 'Akira' aus dem Key entfernt
        name="Neo-Tokyo Seinen", # 'Akira' aus dem Namen entfernt
        version="1.8.1",
        preset_intent=(
            "Simuliert den extrem detaillierten technologischen Manga-Stil der späten 80er Jahre. "
            "Fokus auf komplexe mechanische Details und hartes Cel-shading."
        ),
        recommended_use="Dystopie, technischer Detailgrad, Cyberpunk.",
        camera="Cinemascope Animation POV", lens="Anamorphic Prime",
        film_stock="High-Grain Film Stock", lighting="Harsh Neon Shadows",
        
        # DER TRICK: Wir beschreiben den Stil, ohne den Namen zu nennen
        gemini_style_keywords=(
            "Late 80s masterpiece anime style, futuristic urban dystopia, "
            "extreme industrial architectural detail, hyper-detailed mechanical pipes and wires, "
            "sharp hand-drawn line art, high-contrast cel-shading, cinematic gritty atmosphere, "
            "cybernetic realism. "
            "MANDATORY: Full-bleed, edge-to-edge, NO white borders, illustration fills 100% of the canvas."
        ),
        
        vision_criteria=[
            VisionCriterion(id="industrial_detail", description="Maximale mechanische Komplexität.", weight=35),
            VisionCriterion(id="hard_shading_check", description="Harte Schattenkanten (Cel-shading).", weight=25, is_critical=True)
        ]
    ),

    "90s Cyber-Seinen (GiTS Stil)": PresetConfig(
        name="Cyber-Seinen Style",
        version="1.8.0",
        preset_intent="Technische Präzision, kühle Farbpaletten, filmische Komposition.",
        recommended_use="Sci-Fi, Undercover, KI.",
        camera="Digital 35mm POV", lens="Sharp Prime",
        film_stock="Ektachrome Profile", lighting="Teal and Blue Night",
        gemini_style_keywords=(
            "90s Seinen anime style, Ghost in the Shell aesthetic, teal and blue palette, sharp precise line art. "
            "STRICT EDGE-TO-EDGE: Full-bleed, zero margins."
        ),
        vision_criteria=[VisionCriterion(id="seinen_precision", description="Präzise Linienführung.", weight=30)]
    ),

    "70s Heroic Fantasy (Vallejo-Stil)": PresetConfig(
        name="Heroic Fantasy Oil",
        version="1.0.0",
        preset_intent=(
            "Simuliert den hyper-realistischen Ölmalerei-Stil der 70er/80er Jahre Fantasy-Cover. "
            "Fokus auf heroische Anatomie, eingeölte Hautoberflächen und dramatische Lichtreflexe."
        ),
        recommended_use="Barbaren, Göttinnen, Drachen, epische Krieger, High-Fantasy Cover.",
        camera="Large Format Studio Transparency",
        lens="85mm Sharp Focus",
        film_stock="Oil on Masonite Board", # Das Material, auf dem Vallejo oft malte
        lighting="Golden Hour Rim Light / High-Gloss Highlights",
        
        # Der Stealth-Prompt für Vallejo-Ästhetik
        gemini_style_keywords=(
            "Masterpiece heroic fantasy oil painting on board, 1980s book cover aesthetic. "
            "Hyper-detailed human anatomy, defined and oiled musculature, smooth skin textures. "
            "Sharp metallic reflections on chrome armor, vibrant sunset rim lighting. "
            "Rich deep colors, dramatic chiaroscuro, high-gloss finish, epic composition. "
            "STRICT BORDERLESS: Full-bleed artwork, no white space, no margins."
        ),
        
        vision_pass_score=90,
        vision_criteria=[
            VisionCriterion(
                id="anatomical_heroism", 
                description="Anatomie ist extrem definiert und wirkt wie eine klassische Ölstudie (Muskeldefinition).", 
                weight=35, failure_hint="Erhöhe die Definition der Muskulatur und Lichtreflexe auf der Haut."
            ),
            VisionCriterion(
                id="metallic_sheen", 
                description="Metalle und Rüstungen haben scharfe, spiegelnde Highlights (Chrome-Effekt).", 
                weight=25
            ),
            VisionCriterion(
                id="painterly_realism", 
                description="Kombination aus Pinselstrich-Struktur und fotorealistischen Details.", 
                weight=20
            )
        ]
    )
}