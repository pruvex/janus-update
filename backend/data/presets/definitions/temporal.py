from ..models import PresetConfig, VisionCriterion, SocialTier
from ..temporal_library import inject_temporal_guardrails

# Basis-Definitionen (werden unten durch Injection veredelt)
base_presets = {
    # 1. 1890 (SANIERT)
    "1890_Glass_Plate": PresetConfig(
        name="1890 – Historische Glasplatten-Fotografie",
        version="1.3.0",
        preset_intent="Simulates a pristine, high-quality wet plate collodion photograph from 1890. Focus on the optical characteristics of the era: orthochromatic tonal response (blue eyes look white, red lips look black), extreme depth of field falloff (large format look), and subtle chemical edges. The image should look like a well-preserved museum masterpiece, NOT a damaged or scratched finding.",
        recommended_use="Historische Porträts, Stillleben, Szenen der viktorianischen Ära.",
        
        camera="Großformat-Plattenkamera (8x10)",
        lens="Petzval-Objektiv (Wirbel-Bokeh)",
        film_stock="Orthochromatische Kollodium-Platte (Frisch)",
        lighting="Nordfenster-Licht (Weich) oder pralles Sonnenlicht",
        
        imperfections=[
            "Sanfte Randabdunklung (Vignette)",
            "Orthochromatische Tonwerte (Dunkle Rottöne)",
            "Geringe Schärfentiefe (Fokus nur auf Augen)",
            "Subtile chemische Ränder (nur am Rahmen)",
            "Lange Belichtung (weiche Bewegungen)"
        ],
        forbidden=["Kratzer im Gesicht", "Starke Beschädigung", "Risse", "Schimmel", "Lächeln"],
        
        social_tiers=[
            SocialTier(
                tier_id="worker",
                keywords=["worker", "laborer", "factory", "dock", "Hafenarbeiter", "Fabrik", "Arbeiter"],
                description="Working class individuals in functional, worn attire.",
                textiles=["rough wool", "canvas", "heavy cotton", "worn leather"],
                colors=["drab brown", "grey", "dark blue", "off-white"],
                headwear=["flat cap", "bowler hat", "headscarf"],
                footwear=["heavy leather boots"],
                props=["tools", "handcart", "crates", "coal shovel"],
                locations=["docks", "factory floor", "cobblestone alley", "tenement"],
                forbidden=["silk", "lace", "jewelry", "clean hands", "manicured look"]
            ),
            SocialTier(
                tier_id="bourgeoisie",
                keywords=["scholar", "inventor", "merchant", "doctor", "Gelehrter", "Erfinderin", "Arzt"],
                description="Middle to upper class individuals in formal, structured attire.",
                textiles=["fine wool", "tweed", "starched cotton", "velvet", "subtle lace"],
                colors=["black", "dark grey", "burgundy", "forest green"],
                headwear=["top hat", "bonnet", "formal indoor caps"],
                footwear=["polished leather shoes", "button-up boots"],
                props=["books", "scientific instruments (brass, wood)", "inkwell", "pocket watch"],
                locations=["library", "study", "parlor", "laboratory", "office (Kontor)"],
                forbidden=["rough work clothes", "dirt", "manual labor tools"]
            )
        ],
        default_tier="worker",
        
        gemini_style_keywords="high resolution museum scan of a wet plate collodion photograph from 1890. Sharp focus on eyes, shallow depth of field (Petzval swirl bokeh). Orthochromatic black and white (reds appear black). Subtle chemical imperfections only at the very edges. Pristine condition, high contrast, silver gelatin tones.",
        
        vision_pass_score=92,
        vision_criteria=[
            VisionCriterion(id="orthochromatic_response", description="Orthochromatic behavior visible (dark reds, light blues).", weight=20, is_critical=True, failure_hint="Adjust tonal response."),
            VisionCriterion(id="clean_subject", description="Subject's face is free of scratches or heavy damage artifacts.", weight=20, is_critical=True, failure_hint="Remove noise/scratches from face.")
        ]
    ),
    
    # 2. 1930
    "1930_Documentary": PresetConfig(
        name="1930 – Reportage-Stil (Zwischenkriegszeit)",
        version="1.1.0",
        preset_intent="Der körnige, ungestellte Realismus des Fotojournalismus der 30er Jahre. Unvergütete Optik (Lens Flare), organisches Filmkorn und harte Realität.",
        recommended_use="Straßenfotografie, Reportagen, authentische Momente, 'Street Photography'.",
        
        camera="35mm Messsucherkamera (Leica II Stil)",
        lens="50mm f/3.5 unvergütetes Objektiv",
        film_stock="Panchromatischer S/W-Nitratfilm",
        lighting="Verfügbares natürliches Licht (Kontrast szenenabhängig)",
        
        imperfections=[
            "Organisches Filmkorn",
            "Leichte Bewegungsunschärfe",
            "Randunschärfe des Objektivs",
            "Lichtschleier (Veiling Flare)"
        ],
        forbidden=["Studiobeleuchtung", "Lächeln für die Kamera"],
        
        gemini_style_keywords="CRITICAL OVERRIDE: This is a monochrome black and white photograph. IGNORE any color associations from the prompt. Emulate the look of high-speed panchromatic nitrate film stock: visible organic grain, sharp focus, high contrast, deep blacks. Uncoated lens characteristics (subtle veiling flare). Authentic 1930s documentary 'street photography' style.",
        
        vision_pass_score=90,
        vision_criteria=[
            VisionCriterion(id="uncoated_flare", description="Uncoated optics behavior: mild veiling flare, not digital bloom.", weight=20, is_critical=True, failure_hint="Add veiling flare."),
            VisionCriterion(id="candid_feel", description="Image feels unposed and documentary.", weight=20, failure_hint="Remove posed elements.")
        ]
    ),

    # 3. 1955
    "1955_Mid_Century": PresetConfig(
        name="1955 – Mid-Century Farbfoto (Früher Farbfilm)",
        version="1.0.0",
        preset_intent="Farbfotografie der Nachkriegszeit. Blitzlichtbirnen (Flashbulbs), früher Farbfilm-Charakter und die Ästhetik alter Familienalben.",
        recommended_use="Retro-Lifestyle, Americana, Familienszenen der 50er Jahre.",
        
        camera="1950er Messsucher- oder Klappkamera",
        lens="50mm f/2.8 einfach vergütet",
        film_stock="Früher Farbnegativfilm (Kodacolor Stil)",
        lighting="Tageslicht + Blitzlichtbirne (Harter Frontalblitz)",
        
        imperfections=[
            "Warme Farbverschiebung",
            "Harte Blitzschatten",
            "Leichte Eckenunschärfe",
            "Sichtbares feines Korn"
        ],
        forbidden=["Moderne LED", "Moderne Verpackungen", "Perfekte digitale Schärfe", "Modernes Styling"],
        
        gemini_style_keywords="authentic 1950s color snapshot, flashbulb lighting, early color film, warm tones, uncoated lens character, family album realism",
        
        vision_pass_score=88,
        vision_criteria=[
            VisionCriterion(id="flashbulb_look", description="Hard flash shadows and speculars (if flash used).", weight=25, is_critical=True, failure_hint="Use flashbulb lighting cues."),
            VisionCriterion(id="midcentury_colors", description="Warm, early color film palette (not modern neon).", weight=25, is_critical=True, failure_hint="Shift to warm/pastel palette.")
        ]
    ),
    
    # 4. 1970
    "1970_Analog_Color": PresetConfig(
        name="1970 – Analoger Farbrealismus (Kodachrome Ära)",
        version="1.2.0",
        preset_intent="Die warme, erdige Ästhetik von 1970er Kodachrome-Diafilm. Hohe Schärfe, aber organische Farben und analoger Charme.",
        recommended_use="Nostalgie, Roadtrips, authentische Porträts.",
        
        camera="35mm Spiegelreflex (SLR, z.B. Canon AE-1)",
        lens="50mm f/1.8 Vintage-Vergütung",
        film_stock="Kodachrome 64 Diafilm",
        lighting="Natürliches warmes Licht oder Wolfram (Kein LED)",
        
        imperfections=[
            "Feines organisches Korn",
            "Warmer Farbstich (Gelb/Orange)",
            "Kodachrome Rot/Blau Signatur"
        ],
        forbidden=["Teal and Orange Grading", "Moderner LED-Look", "Synthwave"],
        
        gemini_style_keywords="1970s color photography, kodachrome film look, vintage slr, earth tones, warm analog colors",
        
        vision_pass_score=92,
        vision_criteria=[
            VisionCriterion(id="kodachrome_colors", description="Kodachrome signature: warm skin, strong reds, pleasing blues.", weight=25, is_critical=True, failure_hint="Shift palette to Kodachrome."),
            VisionCriterion(id="temporal_fashion", description="Clothing strictly 1970s.", weight=25, is_critical=True, failure_hint="Fix fashion.")
        ]
    ),
    
    # 5. 1980
    "1980_High_Gloss": PresetConfig(
        name="1980 – Hochglanz-Ästhetik (Vibrant High Gloss)", # KORRIGIERT: 1980 statt 1980er
        version="1.2.0",
        preset_intent="Hochkontrastige Werbefotografie der 80er Jahre. Direkter Blitz, gesättigte Farben und 'Glossy'-Look.",
        recommended_use="Mode, Lifestyle, ausgefallene Porträts ('Flashy').",
        
        camera="Nikon F3 (35mm SLR)",
        lens="35-70mm Zoom-Objektiv",
        film_stock="Fujicolor Super HR 100",
        lighting="Direkter Blitz + Städtisches Umgebungslicht (Natriumdampf)",
        
        imperfections=[
            "Lichthöfe (Halation) / Diffusions-Glow",
            "Hohe Farbsättigung",
            "Harte Blitzschatten"
        ],
        forbidden=["Modernes HD", "Gedämpfte Farben", "Digitales Rauschen"],
        
        gemini_style_keywords="1980s fashion photography, direct flash, fujicolor look, vibrant colors, soft focus highlights, sodium vapor ambient",
        
        vision_pass_score=90,
        vision_criteria=[
            VisionCriterion(id="ambient_light_color", description="Ambient light feels 1980s (Sodium Vapor), no white LED.", weight=20, is_critical=True, failure_hint="Warm up ambient light."),
            VisionCriterion(id="flash_look", description="Direct flash character visible.", weight=20, is_critical=True, failure_hint="Add flash shadows.")
        ]
    )
}

# --- INJECTION DER DIAMANT-STANDARD REGELN ---
# Hier wenden wir die Bibliothek auf die Basis-Presets an.
presets = {
    "1890 – Historische Glasplatten-Fotografie": inject_temporal_guardrails(base_presets["1890_Glass_Plate"], "1890"),
    "1930 – Reportage-Stil (Zwischenkriegszeit)": inject_temporal_guardrails(base_presets["1930_Documentary"], "1930"),
    "1955 – Mid-Century Farbfoto": inject_temporal_guardrails(base_presets["1955_Mid_Century"], "1950"), 
    "1970 – Analoger Farbrealismus": inject_temporal_guardrails(base_presets["1970_Analog_Color"], "1970"),
    "1980 – Hochglanz-Ästhetik": inject_temporal_guardrails(base_presets["1980_High_Gloss"], "1980") # KORRIGIERT
}