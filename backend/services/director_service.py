import logging
from typing import Dict
import openai

logger = logging.getLogger("janus_backend")

# --- ATMOSPHERE BOOSTER (Für Route A: Kein Preset) ---
# Das war früher hardcodiert in openai_image_generation.py
ATMOSPHERE_BOOSTER = (
    "Style: atmospheric, candid moment, captured on 35mm film, "
    "subtle film grain, cinematic lighting, highly detailed."
)

class DirectorService:
    """
    Der Director ist das GEHIRN der Prompt-Erstellung.
    Er entscheidet basierend auf dem Preset-Kontext, wie der finale Prompt aussieht.
    """

    @staticmethod
    async def create_narrative_prompt(
        context: Dict,
        director_model: str,
        client: openai.AsyncOpenAI
    ) -> str:
        user_prompt = context.get("user_prompt", "")
        # Erkennung für Combine-Modus (mehrere URLs)
        is_combine = context.get("reference_image_urls") is not None and len(context.get("reference_image_urls", [])) > 0

        # --- ROUTE D: COMBINE MODE ---
        if is_combine:
            logger.info(f"Director: Route D (Combine Mode) - Merging {len(context['reference_image_urls'])} images.")
            return await DirectorService._generate_combine_instruction(user_prompt, context, director_model, client)
        
        has_preset = context.get("has_preset", False)
        # NEU: Erkennung, ob es ein Refinement/Edit ist
        is_modifying_image = (
            context.get("mode") in ["refine", "edit"] or
            context.get("previous_response_id") is not None or
            context.get("reference_image_url") is not None
        )

        # --- ROUTE C: REFINE/EDIT MODE (Veredelung/Bearbeitung) ---
        if is_modifying_image:
            logger.info("Director: Route C (Modify Mode) - Generating Delta-Instruction.")
            return await DirectorService._generate_refinement_instruction(user_prompt, context, director_model, client)

        # --- ROUTE A: FREE MODE (Kein Preset) ---
        if not has_preset:
            logger.info("Director: Route A (Free Mode) - Enhancing creativity.")
            return await DirectorService._generate_creative_expansion(user_prompt, director_model, client)

        # --- ROUTE B: PRESET MODE (Diamantstandard) ---
        else:
            logger.info(f"Director: Route B (Preset Mode) - Enforcing style: {context.get('film_stock', 'Unknown')}")
            return await DirectorService._generate_preset_compliant_prompt(user_prompt, context, director_model, client)

    @staticmethod
    async def _generate_creative_expansion(user_prompt: str, model: str, client: openai.AsyncOpenAI) -> str:
        """
        Erweitert kurze Prompts kreativ, fügt aber den generischen Atmosphere-Booster hinzu.
        """
        system_prompt = (
            "You are an expert Photographer and Art Director.\n"
            "TASK: Expand the user's short input into a detailed visual description for an image generator (DALL-E 3).\n"
            "GUIDELINES:\n"
            "- Describe lighting, texture, and composition.\n"
            "- Keep it concise but vivid (max 2-3 sentences).\n"
            "- Do NOT add technical camera parameters yet (they are added via suffix).\n"
            "- Output ONLY the prompt text, nothing else."
        )

        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7
            )
            narrative = response.choices[0].message.content.strip()
            
            # Hier fügen wir den Booster hinzu -> Zentralisiert!
            return f"{narrative}. {ATMOSPHERE_BOOSTER}"
            
        except Exception as e:
            logger.error(f"Director Error (Creative): {e}")
            # Fallback: Einfach User-Input + Booster
            return f"{user_prompt}. {ATMOSPHERE_BOOSTER}"

    @staticmethod
    async def _generate_preset_compliant_prompt(user_prompt: str, context: Dict, model: str, client: openai.AsyncOpenAI) -> str:
        """
        Erstellt einen Prompt für ein NEUES BILD, das den Preset-Regeln folgt.
        Der Style-Transfer wird jetzt im Router gehandhabt.
        """
        # --- 1. Regeln und Kontext extrahieren ---
        rules = context.get("rules", {})
        camera = context.get("camera", "Standard Camera")
        film = context.get("film_stock", "Standard Film")
        lens = context.get("lens", "Standard Lens")
        lighting = context.get("lighting", "Natural Light")
        tech_keywords = context.get("gemini_style_keywords", "")
        
        def safe_join(key):
            items = rules.get(key, [])
            if not items: return "None specific"
            return ", ".join(items)

        # --- 2. System-Prompt für neue Bilder ---
        system_prompt = (
            f"You are a strict Technical Director for a high-end AI Image Generator.\n\n"
            f"YOUR GOAL: Create a prompt for a NEW IMAGE based on the user's request, perfectly matching the style.\n\n"
            f"--- TECHNICAL SPECIFICATIONS (MUST ADHERE) ---\n"
            f"STYLE: {context.get('name', 'N/A')}\n"
            f"INTENT: {rules.get('era_intent', 'Photorealism')}\n"
            f"CAMERA: {camera}\n"
            f"FILM/SENSOR: {film}\n"
            f"LENS: {lens}\n"
            f"LIGHTING: {lighting}\n"
            f"IMPERFECTIONS TO ADD: {safe_join('imperfections')}\n"
            f"FORBIDDEN ITEMS: {safe_join('forbidden_items')}\n"
            f"SOCIAL CONTEXT: The subject must fit the description of a '{rules.get('tier_description', 'person')}'.\n\n"
            f"--- INSTRUCTIONS ---\n"
            f"1. Create a detailed visual description based on: '{user_prompt}'.\n"
            f"2. Ensure the description matches all technical specifications above.\n"
            f"3. Include appropriate lighting, composition, and imperfections.\n"
            f"4. Output ONLY the final prompt text, nothing else."
        )

        # --- 3. User-Prompt für den Director ---
        director_user_prompt = f"Create a new image based on: '{user_prompt}'. Append these keywords: {tech_keywords}"

        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": director_user_prompt}
                ],
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Director Error (New Image): {e}")
            # Fallback: User-Input + Keywords
            return f"{user_prompt} {tech_keywords}"

    @staticmethod
    async def _generate_refinement_instruction(user_prompt: str, context: Dict, model: str, client: openai.AsyncOpenAI) -> str:
        system_prompt = (
            "You are a world-class Digital Artist and Cinematographer.\n"
            "TASK: Create a instruction to TRANSFORM an image.\n"
            "GUIDELINES:\n"
            "- IDENTITY: Keep the person's face recognizable.\n"
            "- ENVIRONMENT: If the background changes, describe the LIGHTING and ATMOSPHERE it casts ON the person.\n"
            "- PRESETS: If a historical or cinematic preset is used, specify the appropriate WARDROBE (e.g., fur for Stone Age, silk for Arri Alexa).\n"
            "- INTEGRATION: Ensure no sharp edges between subject and background. Use lighting as a 'glue'.\n"
            "- LIGHTING INTERACTION: Describe how the environment's light affects the subject's surfaces (skin, hair, clothing). Avoid generic descriptions; be specific about the interaction.\n"
            "- AMBIENT OCCLUSION: Always specify how the subject interacts with the new lighting. Use terms like 'Rim Light', 'Color Spill', and 'Atmospheric Blending' to force the AI to merge the layers.\n"
            "- MATERIAL LOGIC: If clothing changes, describe how the fabric (leather, fur, silk) should cast shadows on the person's body and how the environment light hits that specific material.\n"
            "- Output ONLY the final instruction."
        )
        
        style_hint = f" Style to maintain: {context.get('film_stock', 'Photorealistic')}, {context.get('lighting', '')}."
        
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"User Request: '{user_prompt}'. Context: {style_hint}"}
                ],
                temperature=0.5 # Leicht erhöht für bessere visuelle Logik
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Director Error (Refine): {e}")
            return user_prompt

    @staticmethod
    async def _generate_combine_instruction(user_prompt: str, context: Dict, model: str, client: openai.AsyncOpenAI) -> str:
        system_prompt = (
            "You are a master Image Compositor.\n"
            "TASK: Create a blueprint to merge multiple images into one seamless scene.\n"
            "GUIDELINES:\n"
            "- IMAGE ROLES: Identify which image contains the SUBJECT and which contains the BACKGROUND based on the user request.\n"
            "- SEAMLESS BLENDING: Command the AI to extract the subject perfectly and place it into the new environment.\n"
            "- LIGHTING HARMONY: Insist that the environment's light and shadows MUST be applied to the subject.\n"
            "- No 'collage' or 'sticker' look. Output ONLY the technical merging instruction."
        )
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"User Request: '{user_prompt}'. Styles to consider: {context.get('film_stock', 'Realistic')}."}
                ],
                temperature=0.4
            )
            return response.choices[0].message.content.strip()
        except Exception: return user_prompt

# Singleton Instanz für einfachen Import
director_service = DirectorService()
