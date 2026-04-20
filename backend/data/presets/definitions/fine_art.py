# backend/data/presets/definitions/fine_art.py

from ..models import PresetConfig, VisionCriterion

# v1.0.0 — Fine Art Diamond Standard
# Diese Presets simulieren physikalische Maltechniken und Pigment-Verhalten.

presets = {
    "Surrealismus (Dali-Stil)": PresetConfig(
        name="Surrealist Dream",
        version="1.0.0",
        preset_intent=(
            "Simuliert den präzisen, traumartigen Stil von Salvador Dalí. "
            "Fokus auf extreme Tiefenschärfe, scharfe Schatten und unmögliche physikalische Objekte."
        ),
        recommended_use="Träume, Metamorphosen, Wüstenlandschaften, Symbolik.",
        camera="Hyper-focused Perception",
        lens="Infinite Depth of Field",
        film_stock="Smooth Oil on Fine Linen",
        lighting="Harsh Desert Sun / Long Shadows",
        gemini_style_keywords=(
            "Salvador Dali surrealism style, dream logic, hyper-realistic precision, "
            "desert landscapes, melting objects, sharp hard shadows, bizarre symbolism. "
            "STRICT BORDERLESS: Full-bleed artwork, no white space, no margins."
        ),
        vision_criteria=[
            VisionCriterion(id="dream_logic", description="Motiv enthält surrealistische oder physikalisch unmögliche Elemente.", weight=30)
        ]
    ),

    "Renaissance (Da Vinci Stil)": PresetConfig(
        name="High Renaissance Master",
        version="1.0.0",
        preset_intent=(
            "Simuliert die Meisterschaft von Leonardo da Vinci. Fokus auf Sfumato "
            "(rauchige Übergänge), anatomische Perfektion und erdige Pigmente."
        ),
        recommended_use="Klassische Porträts, anatomische Studien, historische Szenen.",
        camera="Humanist Vision",
        lens="Observational Detail",
        film_stock="Oil on Poplar Wood Panel",
        lighting="Soft Diffused North Light",
        gemini_style_keywords=(
            "Leonardo da Vinci painting style, High Renaissance, sfumato technique, "
            "smoky transitions, earthy tones (umber, ochre), anatomical precision, "
            "subtle golden glow. STRICT BORDERLESS: No frames, no paper borders."
        ),
        vision_criteria=[
            VisionCriterion(id="sfumato_check", description="Weiche, rauchige Übergänge ohne harte Kanten im Gesicht.", weight=35, is_critical=True)
        ]
    ),

    "Impressionismus (Van Gogh Stil)": PresetConfig(
        name="Expressive Impasto",
        version="1.0.0",
        preset_intent=(
            "Simuliert den emotionalen Stil von Vincent van Gogh. Fokus auf dicken Farbauftrag "
            "(Impasto), wirbelnde Pinselstriche und komplementäre Farbkontraste."
        ),
        recommended_use="Landschaften, Blumen, emotionale Porträts, Nachtszenen.",
        camera="Emotional Lens",
        lens="Dynamic Movement",
        film_stock="Thick Oil on Coarse Burlap",
        lighting="Vibrant Starry Night / Swirling Sun",
        gemini_style_keywords=(
            "Vincent van Gogh style, Post-Impressionism, thick impasto brushstrokes, "
            "swirling paint patterns, vibrant complementary colors, heavy texture, "
            "visible brush movement. STRICTLY BORDERLESS: The paint covers every pixel."
        ),
        vision_criteria=[
            VisionCriterion(id="impasto_texture", description="Sichtbare, dicke Farbschichten und Pinselstriche.", weight=40, is_critical=True)
        ]
    ),

    "Barock (Rembrandt Stil)": PresetConfig(
        name="Baroque Chiaroscuro",
        version="1.0.0",
        preset_intent=(
            "Simuliert den dramatischen Stil von Rembrandt. Fokus auf Chiaroscuro "
            "(starker Hell-Dunkel-Kontrast) und ein warmes, goldenes Licht."
        ),
        recommended_use="Dramatische Porträts, Charakterstudien, Szenen mit Kerzenlicht.",
        camera="Dramatic Observer",
        lens="Deep Shadow Focus",
        film_stock="Oil on Dark Primed Canvas",
        lighting="Dramatic Chiaroscuro / Golden Key Light",
        gemini_style_keywords=(
            "Rembrandt painting style, Baroque, chiaroscuro lighting, "
            "deep dark backgrounds, dramatic golden spotlights, thick impasto in highlights, "
            "emotional depth. STRICT BORDERLESS: Edge-to-edge dark oil painting."
        ),
        vision_criteria=[
            VisionCriterion(id="chiaroscuro_check", description="Starke Trennung zwischen Licht und Schatten (Schlagschatten im Gesicht).", weight=35, is_critical=True)
        ]
    ),

    "Pop Art (Warhol Stil)": PresetConfig(
        name="Pop Art Screenprint",
        version="1.0.0",
        preset_intent=(
            "Simuliert den Siebdruck-Stil von Andy Warhol. Fokus auf flache Farbflächen, "
            "hohe Sättigung und mechanische Reproduktions-Fehler."
        ),
        recommended_use="Moderne Ikonen, Porträts, Konsumkultur.",
        camera="Mechanical Reproduction",
        lens="Flat Field",
        film_stock="Silk Screen Ink on Fabric",
        lighting="Flat Commercial Studio",
        gemini_style_keywords=(
            "Andy Warhol Pop Art style, silk screen print texture, halftone dots, "
            "high saturation, flat vibrant colors, misaligned registration, "
            "high contrast. STRICT BORDERLESS: Image extends to all four edges."
        ),
        vision_criteria=[
            VisionCriterion(id="screen_print_look", description="Flache Farben und sichtbare Druckraster.", weight=30)
        ]
    )
}