const MODEL_CATALOG = {
    openai: [
        { id: 'gpt-5', name: 'GPT-5', price: '$1.25 / $10.00 (Input/Output)', desc: 'Zukünftiges Flaggschiff, fähig zur Werkzeug-Nutzung.' },
        { id: 'gpt-5-mini', name: 'GPT-5 mini', price: '$0.25 / $2.00 (Input/Output)', desc: 'Zukünftiges schnelles & günstiges Modell.' },
        { id: 'gpt-4o', name: 'GPT-4o', price: '$2.50 / $10.00 (Input/Output)', desc: 'Aktuelles Flaggschiff: Schnell & intelligent.' },
        { id: 'gpt-4o-mini', name: 'GPT-4o mini', price: '$0.15 / $0.60 (Input/Output)', desc: 'Extrem schnell & günstig für Standard-Aufgaben.' },
        { id: 'dall-e-3-standard', name: 'DALL-E 3 (Standard)', price: '$0.040 / Bild', desc: 'Bilderzeugung in Standard-Qualität.' },
        { id: 'dall-e-3-hd', name: 'DALL-E 3 (HD)', price: '$0.080 / Bild', desc: 'Bilderzeugung in höchster Qualität.' }
    ],
    gemini: [ // Korrigierter Schlüssel
        { id: 'gemini-1.5-pro-latest', name: 'Gemini 1.5 Pro', price: 'ca. $3.50 / $10.50', desc: 'Googles Flaggschiff mit riesigem Kontextfenster.' },
        { id: 'gemini-1.5-flash-latest', name: 'Gemini 1.5 Flash', price: 'ca. $0.35 / $1.05', desc: 'Extrem schnell und kosteneffizient.' },
    ],
};