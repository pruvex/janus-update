from ..models import PresetConfig, VisionCriterion
from ..library import COMMON_FAILURES_LIST

# v2.4.0 — Enterprise Diamond Standard (German Localization)
# - Alle Preset-Namen und Beschreibungen auf Deutsch
# - Keys im Dictionary angepasst (für das Dropdown)
# - Behält alle technischen Diamant-Standard-Regeln bei

presets = {
    # 1) Doku / RAW
    "Authentische RAW-Realität": PresetConfig(
        name="Ungestellte Realität (Sony Alpha)",
        version="2.4.0",
        preset_intent=(
            "Simuliert ungestellte, reale Fotografie mit dokumentarischem RAW-Charakter. "
            "Priorisiert physikalische Plausibilität, glaubwürdige Imperfektion und echte Materialien "
            "über ästhetische Perfektion."
        ),
        recommended_use="Street Photography, Reportagen, 'Grit', authentische Momente.",
        benchmark_composition_locked=False,
        
        camera="Sony A7R V",
        lens="35mm f/1.8",
        film_stock="Unverarbeitetes RAW (Neutrales Profil)",
        lighting="Verfügbares Licht (Nur natürliche/praktische Quellen)",
        
        imperfections=[
            "Subtile optische Unvollkommenheiten (Randabfall)",
            "Leichte Bewegungsunschärfe (Shutter Drag)",
            "Sichtbares ISO-Rauschen (800-1600)",
            "Natürliche Hauttextur (nicht geglättet)"
        ],
        forbidden=[
            "Studio-Beleuchtung", "Beauty-Retusche", "Teal & Orange Grading",
            "Perfekte Symmetrie", "CGI Render-Look", "Hero Lighting"
        ],
        common_failure_modes=COMMON_FAILURES_LIST + ["Too clean/perfect", "Dramatic studio light"],
        
        gemini_style_keywords=(
            "documentary photograph, RAW style, available light, natural colors, "
            "realistic skin texture, visible grain, authentic imperfections"
        ),
        
        vision_pass_score=88,
        vision_criteria=[
            VisionCriterion(
                id="raw_lighting",
                description="Beleuchtung wirkt wie echtes Available Light (eine Hauptrichtung, logischer Falloff), kein Studio-Setup.",
                weight=25, failure_hint="Entferne Fill-Lights, mache Schatten härter/natürlicher.", is_critical=True
            ),
            VisionCriterion(
                id="texture_authenticity",
                description="Kein 'Digital Art' Look. Haut/Stoffe haben organische Unregelmäßigkeiten.",
                weight=20, failure_hint="Füge Noise/Grain hinzu, reduziere Glättung."
            )
        ]
    ),

    # 2) Porträt
    "Menschliche Porträt-Treue": PresetConfig(
        name="Hochauflösendes Porträt (Canon RF)",
        version="2.4.0",
        preset_intent=(
            "Erfasst menschliche Subjekte mit dermatologischer Genauigkeit und glaubwürdiger Präsenz. "
            "Natürliche Asymmetrie, realistische Augen (Lichtreflexe), keine KI-Perfektion."
        ),
        recommended_use="Headshots, Charakterstudien, High-End Editorial.",
        benchmark_composition_locked=True,
        
        camera="Canon EOS R5",
        lens="85mm f/1.2L",
        film_stock="Neutrales Porträt-Profil",
        lighting="Weiches Fensterlicht oder große Octabox (Eine Hauptquelle)",
        
        imperfections=[
            "Poren, feine Linien, kleine Unreinheiten",
            "Leichte Asymmetrie im Gesicht",
            "Abstehende Haare (Flyaways), natürliche Haarstruktur"
        ],
        forbidden=[
            "Airbrush-Haut", "Puppengesicht", "Glasige Augen",
            "Übertrieben weiße Zähne", "HDR-Glow", "Überschärfte Halos"
        ],
        common_failure_modes=COMMON_FAILURES_LIST + ["Doll-like face", "Glassy eyes"],
        
        gemini_style_keywords=(
            "professional portrait photograph, highly detailed skin texture, pores, "
            "natural asymmetry, sharp eyes, believable catchlights, soft lighting"
        ),
        
        vision_pass_score=92,
        vision_criteria=[
            VisionCriterion(
                id="skin_realism",
                description="Haut muss Poren, Fältchen und Textur zeigen. KEIN Wachs/Plastik-Look.",
                weight=35, failure_hint="Entferne Beauty-Filter, erhöhe Struktur.", is_critical=True
            ),
            VisionCriterion(
                id="eye_depth",
                description="Augen haben Tiefe, Struktur in der Iris und logische Reflexionen (Catchlights).",
                weight=25, failure_hint="Füge Catchlights hinzu, detailliere Iris.", is_critical=True
            )
        ]
    ),

    # 3) Produkt (Werbung)
    "Kommerzieller Produkt-Realismus": PresetConfig(
        name="Fühlbare Produktaufnahme (Fuji GFX)",
        version="2.4.0",
        preset_intent=(
            "Kommerziell nutzbare Produktfotografie mit glaubwürdiger physischer Präsenz und Haptik. "
            "Kontaktfläche, plausible Schattenlogik, kontrollierte Reflexe."
        ),
        recommended_use="High-End Produktfotos, Werbung, Mockups mit Materialfokus.",
        benchmark_composition_locked=True,
        
        camera="Fujifilm GFX 100S",
        lens="120mm f/4 Macro",
        film_stock="Mittelformat Digital (Hoher Dynamikumfang)",
        lighting="Kontrolliertes Studio (Kantenlicht, Flags, weiches Fülllicht)",
        
        imperfections=[
            "Glaubwürdiger Kontaktschatten (Grounding)",
            "Subtile Material-Unperfektheit (Staubkorn, Mikrokratzer)",
            "Physikalisch korrekte Reflexionen (Fresnel)"
        ],
        forbidden=[
            "Schwebende Objekte", "Keine Schatten", "Perfekter CGI-Spiegel", 
            "Low-Poly Kurven", "Treppchenbildung (Aliasing)"
        ],
        common_failure_modes=COMMON_FAILURES_LIST + ["Floating object", "Bad reflection mapping"],
        
        gemini_style_keywords=(
            "commercial product photograph, medium format quality, macro details, "
            "tangible materials, contact shadow, studio lighting, 8k"
        ),
        
        vision_pass_score=90,
        vision_criteria=[
            VisionCriterion(
                id="grounding_physics",
                description="Objekt ist fest verankert (Kontaktschatten + Ambient Occlusion). Es schwebt nicht.",
                weight=35, failure_hint="Füge Schatten am Bodenkontakt hinzu.", is_critical=True
            ),
            VisionCriterion(
                id="material_response",
                description="Materialien reagieren korrekt auf Licht (Metall glänzt, Stoff matt, Glas bricht).",
                weight=30, failure_hint="Korrigiere Roughness/Glossiness Maps.", is_critical=True
            )
        ]
    ),

    # 4) Kino-Look
    "Kino-Erzählstil (Filmstill)": PresetConfig(
        name="Kino-Look (ARRI Alexa)",
        version="1.0.0",
        preset_intent=(
            "Fotorealistische Szene mit Filmstill-Qualität: kontrolliertes, motiviertes Licht, "
            "glaubwürdige Atmosphäre, echte Optik ohne CGI-Look."
        ),
        recommended_use="Key Visuals, Trailer-Stills, Storytelling.",
        benchmark_composition_locked=False,
        
        camera="ARRI Alexa 35",
        lens="50mm Anamorph (Subtil)",
        film_stock="Film-Emulation (Kodak Vision3 Stil)",
        lighting="Motiviertes Licht (Key) + Praktische Leuchten + Atmosphäre",
        
        imperfections=[
            "Subtiles Filmkorn",
            "Sanfte Lichthöfe (Halation)",
            "Atmosphärischer Dunst (Haze)",
            "Natürlicher Lichter-Abfall (Roll-off)"
        ],
        forbidden=[
            "Übertriebenes Teal-Orange", "Starkes Bloom", "CGI-Glanz",
            "Überschärfte Ränder", "Digitales Rauschen"
        ],
        common_failure_modes=COMMON_FAILURES_LIST + ["Video game look", "Over-processed"],
        
        gemini_style_keywords=(
            "cinematic film still, motivated lighting, practical lights, subtle haze, "
            "gentle film grain, natural highlight roll-off, realistic lenses, arri alexa"
        ),
        
        vision_pass_score=89,
        vision_criteria=[
            VisionCriterion(
                id="motivated_lighting",
                description="Licht ist motiviert und physikalisch plausibel (Practical-Quelle erkennbar/implizit).",
                weight=35, failure_hint="Setze Practical Lights; korrigiere Schattenlogik.", is_critical=True
            ),
            VisionCriterion(
                id="cinema_not_cgi",
                description="Filmlook ohne CGI-Signale (keine perfekten Spiegelungen, kein Plastikglanz).",
                weight=35, failure_hint="Reflexe unperfekter; Materialroughness variieren.", is_critical=True
            )
        ]
    ),

    # 5) E-Commerce
    "Sauberer E-Commerce Packshot": PresetConfig(
        name="Sauberer Packshot (High-Key Studio)",
        version="1.0.0",
        preset_intent=(
            "Extrem saubere, fotorealistische E-Commerce-Packshots: High-Key Hintergrund, "
            "kontrollierte weiche Schatten, neutrale Farben, perfekte Kantenlesbarkeit."
        ),
        recommended_use="Shop/Marketplace, Katalog, Freisteller.",
        benchmark_composition_locked=True,
        
        camera="Phase One XF IQ4",
        lens="100mm Makro (Geringe Verzerrung)",
        film_stock="Neutrales Werbe-Profil",
        lighting="High-Key Studio (Softbox, Weißer Hintergrund)",
        
        imperfections=[
            "Minimaler realer Schlagschatten (nicht schwebend)",
            "Keine chromatische Aberration"
        ],
        forbidden=[
            "Schmutziges Weiß", "Farbstich", "Harte Schatten", 
            "HDR-Glow", "Vignette", "Hintergrund-Unruhe"
        ],
        common_failure_modes=COMMON_FAILURES_LIST + ["Gray background", "Hard shadow"],
        
        gemini_style_keywords=(
            "photorealistic high-key packshot, clean white background, soft controlled shadow, "
            "accurate color, crisp edges, commercial e-commerce photography"
        ),
        
        vision_pass_score=91,
        vision_criteria=[
            VisionCriterion(
                id="white_balance",
                description="Weißpunkt neutral, Hintergrund sauber High-Key ohne Grauschleier.",
                weight=35, failure_hint="Weißabgleich neutralisieren; Hintergrund aufhellen.", is_critical=True
            ),
            VisionCriterion(
                id="edge_clarity",
                description="Kanten klar und sauber ohne Halos oder Fransen (Freisteller-Qualität).",
                weight=35, failure_hint="Kanten schärfen aber ohne Halos.", is_critical=True
            ),
            VisionCriterion(
                id="soft_shadow",
                description="Weicher, plausibler Produktschatten am Boden (nicht fehlend, nicht hart).",
                weight=30, failure_hint="Weichen Kontaktschatten hinzufügen.", is_critical=True
            )
        ]
    )
}