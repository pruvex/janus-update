from ..models import PresetConfig, SocialTier, VisionCriterion

presets = {
    "Golden Age (Vintage 1940s)": PresetConfig(
        name="Golden Age Comic",
        version="1.0.0",
        preset_intent="Simuliert den klassischen US-Comic-Druck der 40er Jahre. Fokus auf Ben-Day-Dots, begrenzte Farbpalette und leicht versetzten Farbdruck auf grobem Papier.",
        recommended_use="Superhelden-Nostalgie, Vintage-Poster, Retro-Illustration.",
        camera="Process Camera (Analog)",
        lens="Fixed Focal Length (Flat Field)",
        film_stock="Newsprint (Zeitungspapier, leicht vergilgt)",
        lighting="Flat High-Contrast Inking",
        gemini_style_keywords="1940s comic book art, Ben-Day dots, CMYK offset printing, ink bleed, thick black outlines, pulp aesthetic, retro color palette",
        social_tiers=[
            SocialTier(
                tier_id="hero",
                keywords=["hero", "superhero", "protagonist"],
                description="Klassische heroische Proportionen, dynamische Pose.",
                textiles=["Spandex-Prototyp", "Heavy Cotton", "Leather"],
                colors=["Primary Colors", "Blue", "Red", "Yellow"],
                headwear=["Cowl", "Mask"],
                footwear=["Leather Boots"],
                props=["Shield", "Utility Belt"],
                locations=["Metropolis", "Art Deco Cityscape"],
                forbidden=["Digital gradients", "Modern neon"]
            )
        ],
        vision_criteria=[
            VisionCriterion(id="ink_outlines", description="Klare schwarze Outlines vorhanden, keine zittrigen Linien.", weight=30, is_critical=True),
            VisionCriterion(id="paper_texture", description="Sichtbare Papierfaser und Druckpunkte (Dots) im Hintergrund.", weight=20)
        ]
    ),

    "Noir Graphic Novel (Tusche)": PresetConfig(
        name="Modern Noir Ink",
        version="1.0.0",
        preset_intent="Extremer Schwarz-Weiß-Kontrast (Chiaroscuro). Inspiriert von Frank Miller. Fokus auf Schatten als narratives Element.",
        recommended_use="Crime Stories, düstere Thriller, dramatische Porträts.",
        camera="High Contrast Monochrome Transfer",
        lens="Deep Shadows / Wide Angle",
        film_stock="High-Gloss Ink on Bristol Board",
        lighting="Hard Rim Light / Stark Chiaroscuro",
        gemini_style_keywords="graphic novel noir style, heavy ink, stark black and white, chiaroscuro, rain streaks, gritty texture, minimal accent color",
        vision_criteria=[
            VisionCriterion(id="stark_contrast", description="Echte Schwarzbereiche ohne Graustufen-Rauschen.", weight=40, is_critical=True),
            VisionCriterion(id="no_midtones", description="Minimierung von Zwischentönen für harten Comic-Look.", weight=20)
        ]
    ),

    "Ligne Claire (Klarer Stil)": PresetConfig(
        name="Ligne Claire (Moebius Style)",
        version="1.0.0",
        preset_intent="Präzise, gleichmäßig dicke Linien, flache Farben, keine Schraffur. Fokus auf Klarheit und Eleganz.",
        recommended_use="Sci-Fi, Architektur-Visualisierung, europäische Graphic Novels.",
        camera="Technical Pen (0.5mm)",
        lens="Infinite Depth of Field",
        film_stock="Matte Heavyweight Paper",
        lighting="Uniform Ambient Light (No Shadows)",
        gemini_style_keywords="Ligne claire style, Moebius aesthetic, clean lines, flat colors, no hatching, elegant compositions, Hergé influence",
        vision_criteria=[
            VisionCriterion(id="line_purity", description="Konstante Linienstärke ohne Druck-Variationen.", weight=35, is_critical=True),
            VisionCriterion(id="flat_shading", description="Vollständig flache Farbflächen ohne Verläufe.", weight=25, is_critical=True)
        ]
    ),

    "90s Cyber-Extreme": PresetConfig(
        name="90s Gritty Comic",
        version="1.0.0",
        preset_intent="Aggressives Cross-Hatching, übersteigerte Anatomie, Neon-Akzente auf schmutzigen Texturen. Inspiriert von Image Comics.",
        recommended_use="Cyberpunk, Action, Dark Fantasy.",
        camera="Multi-Layer Digital Inking",
        lens="Fisheye / Dynamic Action Angle",
        film_stock="Glossy Coated Paper",
        lighting="Multi-Directional Neon Fill",
        gemini_style_keywords="90s comic style, extreme cross-hatching, gritty textures, vibrant but dirty colors, dynamic perspective, heavy muscle detail",
        vision_criteria=[
            VisionCriterion(id="cross_hatching", description="Detaillierte Kreuzschraffur für Schattenbereiche.", weight=30),
            VisionCriterion(id="dynamic_pose", description="Extreme perspektivische Verkürzung (Fore-shortening).", weight=20)
        ]
    ),

    "Painterly Graphic Novel": PresetConfig(
        name="Digital Painterly",
        version="1.0.0",
        preset_intent="Moderner Graphic-Novel-Stil mit malerischen digitalen Texturen. Kombiniert weiche Malerei mit harten Fokus-Linien.",
        recommended_use="Fantasy, Storytelling, emotionale Charakter-Szenen.",
        camera="Digital Cintiq Rendering",
        lens="Focus Blur (Digital)",
        film_stock="Digital Canvas",
        lighting="Volumetric / Cinematic Lighting",
        gemini_style_keywords="painterly graphic novel, digital art, soft brushstrokes, sharp focus lines, volumetric lighting, rich color depth, concept art aesthetic",
        vision_criteria=[
            VisionCriterion(id="brushstroke_texture", description="Sichtbare Pinselstriche in den Farbflächen.", weight=25),
            VisionCriterion(id="focal_lines", description="Kombination aus weichen Hintergründen und scharfen Linien am Subjekt.", weight=25)
        ]
    )
}