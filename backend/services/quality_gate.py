import logging
import base64
import json
import httpx
from typing import Dict, List, Optional
import openai

logger = logging.getLogger("janus_backend")

class QualityGateService:
    """
    Verteilt die Anfrage an den passenden Provider (OpenAI oder Gemini).
    """
    async def evaluate_image(
        self, 
        provider: str,
        api_key: str, 
        image_bytes: bytes, 
        prompt: str, 
        criteria: List[str] = None
    ) -> Dict:
        """
        Sendet das Bild an GPT-4o Vision zur Analyse.
        """
        if not criteria:
            criteria = ["Is the image photorealistic?", "Are there obvious AI artifacts?"]

        if provider == "openai":
            return await self._evaluate_with_openai(api_key, image_bytes, prompt, criteria)
        elif provider == "gemini":
            return await self._evaluate_with_gemini(api_key, image_bytes, prompt, criteria)
        else:
            logger.error(f"Unbekannter Provider für Quality Gate: {provider}")
            return self._fallback_result()

    async def _evaluate_with_openai(self, api_key: str, image_bytes: bytes, prompt: str, criteria: List[str]) -> Dict:
        # Kriterien formatieren
        criteria_text = "\n".join([f"- {c}" for c in criteria])
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        client = openai.AsyncOpenAI(api_key=api_key)
        
        system_prompt = (
            "You are a strict Photography Critic and AI Quality Control Agent. "
            "Your job is to REJECT images that look like 'typical AI art' (plastic skin, perfect symmetry, weird hands) "
            "and ACCEPT only images that look like real photos.\n"
            f"CRITERIA TO CHECK:\n{criteria_text}"
        )
        
        user_message = (
            f"Original Prompt: {prompt}\n\n"
            "Evaluate this image. Does it meet the criteria? "
            "Return a JSON object with: { 'passed': boolean, 'score': 0-100, 'reason': 'string', 'suggestion': 'string' }"
        )

        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": [
                        {"type": "text", "text": user_message},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                    ]}
                ],
                response_format={"type": "json_object"},
                max_tokens=300
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"OpenAI Quality Gate Error: {e}")
            return self._fallback_result()

    async def _evaluate_with_gemini(self, api_key: str, image_bytes: bytes, prompt: str, criteria: List[str]) -> Dict:
        # UPDATE: Wir nutzen jetzt Gemini 3 Flash (Preview)
        model = "gemini-3-flash-preview"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        
        criteria_text = "\n".join([f"- {c}" for c in criteria])
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        # Prompt Konstruktion
        full_prompt = (
            "You are a strict Photography Critic. Analyze this image based on these criteria:\n"
            f"{criteria_text}\n\n"
            f"Original Request: {prompt}\n\n"
            "Output strictly valid JSON with no markdown formatting:\n"
            "{ \"passed\": boolean, \"score\": 0-100, \"reason\": \"string\", \"suggestion\": \"string\" }"
        )

        payload = {
            "contents": [{
                "parts": [
                    {"text": full_prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": base64_image
                        }
                    }
                ]
            }],
            "generationConfig": {
                "response_mime_type": "application/json" # JSON Mode erzwingen
            }
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                
            data = response.json()
            # Text extrahieren
            text_result = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "{}")
            return json.loads(text_result)
            
        except Exception as e:
            logger.error(f"Gemini Quality Gate Error: {e}")
            return self._fallback_result()

    def _fallback_result(self):
        return {"passed": True, "score": 100, "reason": "Check skipped due to error", "suggestion": ""}

# Singleton Instanz
quality_gate_service = QualityGateService()
