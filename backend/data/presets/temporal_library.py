from .models import VisionCriterion, PresetConfig

# --- GLOBAL TEMPORAL QUALITY GATE (v1.3.0) ---
# Added: 1950s Support (Mid-Century)

# 1. TECHNOLOGY & PROCESS CRITERIA (Wie der Film aussieht)
TEMPORAL_TECH_CRITERIA = {
    "1890": [
        VisionCriterion(
            id="tech_accuracy_1890_process",
            description="Kameratechnik/Prozess wirkt wie 1890: Großformat/Glasplatte, orthochromatische Tonwerte (Rot ist dunkel, Himmel hell), lange Belichtungslogik.",
            weight=35, is_critical=True,
            failure_hint="Erzwinge Glasplatten-Ästhetik (orthochromatisch, weicher Look, chemische Plattenfehler), entferne moderne Lichtsignale."
        )
    ],
    "1930": [
        VisionCriterion(
            id="tech_accuracy_1930_35mm",
            description="Kameratechnik/Optik wirkt wie frühe 35mm-Reportage (uncoated lens behavior, organisches Filmkorn, keine digitale Schärfe).",
            weight=30, is_critical=True,
            failure_hint="Füge organisches Korn und uncoated veiling flare hinzu; reduziere digitale Mikroschärfe."
        )
    ],
    "1950": [
        VisionCriterion(
            id="tech_accuracy_1950_early_color",
            description="Frühe Farbfotografie (Kodacolor/Ektachrome E-1): Warme Hauttöne, leichte Farbverschiebungen, Flashbulbs.",
            weight=30, is_critical=True,
            failure_hint="Nutze Flashbulb-Licht (harte Schatten), reduziere moderne Sättigung, shift to warm/pastel."
        )
    ],
    "1970": [
        VisionCriterion(
            id="tech_accuracy_1970_color_film",
            description="Farbfilm-Charakter wirkt 1970er-typisch (Kodachrome/Ektachrome-Ästhetik ohne modernes Teal/Orange Grading).",
            weight=30, is_critical=True,
            failure_hint="Vermeide modernes Color-Grading; nutze filmtypische Tonkurven, feines Korn."
        )
    ],
    "1980": [
        VisionCriterion(
            id="tech_accuracy_1980_flash_colorneg",
            description="80er-Commercial-Foto wirkt technisch plausibel: Direct flash + Color negative look, plausible Halation ohne digitalen Synthwave-Look.",
            weight=30, is_critical=True,
            failure_hint="Licht als echten Blitz integrieren (harte Schatten, Speculars), Filmlook statt digitaler Neon-Ästhetik."
        )
    ],
}

# 2. GLOBAL BLACKLISTS (Was es damals NICHT gab - Weltweit gültig)
TEMPORAL_GLOBAL_BLACKLIST = {
    "1890": [
        "Smartphone", "Laptop", "Headphones", "LED light", "Neon sign", 
        "Modern plastic", "PVC", "Aluminum can", "Modern packaging (barcodes)",
        "Zipper", "Velcro", "Modern sneakers", "Baseball cap", "Modern eyeglasses",
        "Color photography", "Digital noise", "HDR glow"
    ],
    "1930": [
        "Smartphone", "Laptop", "LED light", "Modern plastic", "Spandex/Nylon",
        "Modern Zipper", "Velcro", "Modern sneakers", "Modern sportswear",
        "Barcodes", "QR codes", "Modern UI", "Color photography", "Digital sharpness"
    ],
    "1950": [
        "Smartphone", "Laptop", "LED light", "Modern Flat Screen", 
        "Modern Sneakers (Nike/Adidas style)", "Barcodes", "QR codes", 
        "Modern Acrylics", "Digital noise"
    ],
    "1970": [
        "Smartphone", "Laptop", "Modern LED lighting", "Flat screens",
        "Modern athletic sneakers", "Modern streetwear", "QR codes",
        "Modern car design (post-2000)", "Teal-and-orange grade", "HDR glow"
    ],
    "1980": [
        "Smartphone", "Laptop", "Modern LED signage", "Flat screens",
        "Modern sneakers (post-2000)", "QR codes", "Modern UI",
        "Retrowave/Synthwave neon grid (digital art)", "HDR glow"
    ],
}

# 3. TYPOGRAPHY CHEAT SHEET (Wenn Text im Bild ist, muss er so aussehen)
TEMPORAL_TYPOGRAPHY = {
    "1890": "Visible text allowed only if era-correct (1890). Printed matter: letterpress-like ink on matte paper. Typography: Serif-dominant, hand-painted signage. FORBIDDEN: QR codes, Barcodes, Modern UI, Sans-serif branding.",
    "1930": "Visible text allowed only if era-correct (1930). Newspapers: letterpress/early offset, slightly imperfect registration. Typography: Serif headlines, painted shop signs. FORBIDDEN: Clean geometric sans, Modern icons.",
    "1950": "Visible text allowed only if era-correct (1950). Mid-Century Modern Typography. Hand-painted signs or early phototypesetting. NO Digital fonts/Barcodes.",
    "1970": "Visible text allowed only if era-correct (1970). Print: offset printing, visible halftone dots allowed. Typography: Bold headlines, period ad layouts. FORBIDDEN: Modern app UI, Minimalist branding.",
    "1980": "Visible text allowed only if era-correct (1980). Print: glossy magazine style, offset. Typography: Bold commercial headlines. FORBIDDEN: Digital displays, LED screen text, URL addresses."
}

# 4. GLOBAL GATE CRITERIA (Sicherheitsnetz)
GLOBAL_TEMPORAL_CRITERIA = [
    VisionCriterion(
        id="no_modern_cues_global",
        description="Keine modernen Cues: Smartphones, LED-Look, moderne Verpackungen/Barcodes, moderne Kunststoffe.",
        weight=16, is_critical=True,
        failure_hint="Entferne moderne Geräte und Materialien."
    ),
    VisionCriterion(
        id="light_source_plausibility",
        description="Lichtquellen zeitplausibel (kein LED, kein unmotiviertes Studio-Licht).",
        weight=14, is_critical=True,
        failure_hint="Passe Licht an Epoche an (Tageslicht, Tungsten, Blitz)."
    ),
    VisionCriterion(
        id="text_era_correct",
        description="Schrift/Print ist erlaubt, aber muss zur Epoche passen (Material, Drucktechnik, Typo). Keine QR/Barcodes.",
        weight=10, is_critical=True,
        failure_hint="Nutze periodtypische Drucktechnik (Letterpress/Offset), entferne moderne Logos/Codes."
    )
]

# 5. INJECTION HELPER
def inject_temporal_guardrails(preset: PresetConfig, decade_key: str) -> PresetConfig:
    """
    Kombiniert alle Regeln zu einem Diamant-Standard Preset.
    """
    # 1. Blacklist hinzufügen
    blacklist = TEMPORAL_GLOBAL_BLACKLIST.get(decade_key, [])
    preset.forbidden = list(dict.fromkeys(list(preset.forbidden) + blacklist))
    
    # 2. Tech Criteria (Prozess)
    tech_crit = TEMPORAL_TECH_CRITERIA.get(decade_key, [])
    
    # 3. Global Gate (Anachronismen & Text)
    preset.vision_criteria = list(preset.vision_criteria) + tech_crit + GLOBAL_TEMPORAL_CRITERIA
    
    # 4. Typo-Regeln in den Prompt injizieren (wichtig für DALL-E/Gemini)
    typo_hint = TEMPORAL_TYPOGRAPHY.get(decade_key, "")
    if typo_hint:
        preset.gemini_style_keywords += f", {typo_hint}"
        
    return preset
