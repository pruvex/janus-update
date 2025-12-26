from typing import Optional
import logging

logger = logging.getLogger("janus_backend")

# --- GOLDSTANDARD PRESETS ---

# OPENAI (GPT Image 1.5 / Mini):
# Strategie: System-Instruktion für den Orchestrator (GPT-5.2).
# Wir verbieten "AI-Wörter" und erzwingen Kamera-Specs für echten Fotorealismus.
GPT_PRESETS = {
    "Fotorealistisch": {
        "Fotorealismus 1": (
            "ROLE: You are a Lead Prompt Engineer for OpenAI's 'gpt-image-1.5' model. "
            "GOAL: Transform the user request into a prompt that generates a RAW, UNPROCESSED PHOTOGRAPH. "
            "STRICT RULES FOR GPT-IMAGE-1.5: "
            "1. STRUCTURE: Start with the Subject, then Environment, then Lighting, then Camera Specs. "
            "2. FORBIDDEN TOKENS: Do NOT use 'photorealistic', 'hyperrealistic', '4k', '8k', or 'HDR'. These trigger a fake/CGI look. "
            "3. IMPERFECTIONS: Explicitly ask for 'natural skin texture', 'slight film grain', 'motion blur', or 'atmospheric dust'. "
            "4. CAMERA SPECS: Use 'Shot on Sony A7R V', '50mm f/1.2 GM lens', 'ISO 400', 'Global Illumination'. "
            "5. OUTPUT: Provide ONLY the rewritten prompt, nothing else. "
            "USER REQUEST: {prompt}"
        ),
        "Fotorealismus 2": (
             "ROLE: You are a Studio Lighting Expert. Write a prompt for 'gpt-image-1.5'. "
             "GOAL: A high-end Editorial/Fashion shot. "
             "SPECS: Use 'Hasselblad X2D, 90mm f/3.2', 'Profoto strobe with softbox', 'subtle rim light'. "
             "STYLE: Clean, modern, luxury aesthetic. "
             "USER REQUEST: {prompt}"
        )
    }
}

# GEMINI (Imagen 3):
# Strategie: Kurze, präzise Anweisungen mit Fokus auf technische Details.
# Keine "AI-Wörter", keine künstlerischen Stilbegriffe.
GEMINI_PRESETS = {
    "Fotorealistisch": {
        "Fotorealismus 1": (
            "Create a documentary-style photograph. "
            "Use natural lighting, subtle shadows, and realistic textures. "
            "Camera: Leica M11, 35mm Summilux, f/1.4, ISO 200. "
            "Focus on authentic details and natural imperfections. "
            "Subject: {prompt}"
        ),
        "Fotorealismus 2": (
            "Capture a moment with authentic photojournalism style. "
            "Use available light only, no artificial lighting. "
            "Camera: Canon EOS R5, 85mm, f/2.2, 1/250s, ISO 400. "
            "Slightly underexposed with rich shadows. "
            "Subject: {prompt}"
        )
    }
}

def get_preset(provider: str, style: str, variation: str, prompt: str) -> Optional[str]:
    """
    Get the processed prompt based on provider, style, and variation.
    
    Args:
        provider: The provider name (e.g., 'openai', 'gemini')
        style: The style category (e.g., 'Fotorealistisch')
        variation: The specific variation (e.g., 'Fotorealismus 1')
        prompt: The original user prompt to be enhanced
    
    Returns:
        The processed prompt string or None if not found
    """
    try:
        if provider.lower() == 'openai' and style in GPT_PRESETS and variation in GPT_PRESETS[style]:
            return GPT_PRESETS[style][variation].format(prompt=prompt)
        elif provider.lower() == 'gemini' and style in GEMINI_PRESETS and variation in GEMINI_PRESETS[style]:
            return GEMINI_PRESETS[style][variation].format(prompt=prompt)
        return None
    except Exception as e:
        logger.error(f"Error getting preset for {provider}/{style}/{variation}: {str(e)}")
        return None
