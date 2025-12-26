import logging
import base64
import json
import httpx
from typing import Dict, List, Optional, Any
import openai
from backend.data.presets import VisionCriterion  # WICHTIG: Die neue Klasse importieren

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
        criteria: List[VisionCriterion] = None
    ) -> Dict:
        """
        Verteilt die Anfrage an den passenden Provider.
        """
        # Fallback auf generische Kriterien, wenn keine spezifischen übergeben werden
        if not criteria:
            criteria = [
                VisionCriterion(id="photorealism", description="Is the image photorealistic?", weight=100)
            ]

        if provider == "openai":
            return await self._evaluate_with_openai(api_key, image_bytes, prompt, criteria)
        elif provider == "gemini":
            return await self._evaluate_with_gemini(api_key, image_bytes, prompt, criteria)
        else:
            logger.error(f"Unbekannter Provider für Quality Gate: {provider}")
            return self._fallback_result()

    async def _evaluate_with_openai(self, api_key: str, image_bytes: bytes, prompt: str, criteria: List[VisionCriterion]) -> Dict:
        # Kriterien in eine Scorecard für den Vision Prompt umwandeln
        scorecard_text = ""
        for c in criteria:
            scorecard_text += f"- {c.description} (id: {c.id})\n"
        
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        client = openai.AsyncOpenAI(api_key=api_key)
        
        system_prompt = (
            "You are a strict Photography Critic. "
            "Evaluate the image against the provided scorecard. "
            "For each criterion, provide a score from 0 to 100. "
            "Return ONLY a valid JSON object with a list of scores and nothing else."
        )
        
        user_message = (
            f"Original Prompt: {prompt}\n\n"
            f"SCORECARD:\n{scorecard_text}\n"
            "JSON format: { \"scores\": [{\"id\": \"criterion_id\", \"score\": 0-100, \"reason\": \"short string\"}] }"
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
                max_tokens=500 # Mehr Platz für detailliertere Scores
            )
            # Hier berechnen wir den finalen Score
            return self._calculate_final_score(json.loads(response.choices[0].message.content), criteria)
        except Exception as e:
            logger.error(f"OpenAI Quality Gate Error: {e}")
            return self._fallback_result()

    async def _evaluate_with_gemini(self, api_key: str, image_bytes: bytes, prompt: str, criteria: List[VisionCriterion]) -> Dict:
        model = "gemini-3-flash-preview"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        
        # Scorecard für den Prompt erstellen
        scorecard_text = ""
        for c in criteria:
            scorecard_text += f"- {c.description} (id: {c.id})\n"
            
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        full_prompt = (
            "You are a strict Photography Critic. Evaluate the image against this scorecard. "
            "For each criterion, provide a score from 0 to 100.\n"
            f"SCORECARD:\n{scorecard_text}\n"
            "Output strictly valid JSON with no markdown:\n"
            "{ \"scores\": [{\"id\": \"criterion_id\", \"score\": 0-100, \"reason\": \"short string\"}] }"
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
                "response_mime_type": "application/json"
            }
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                
            data = response.json()
            # Text extrahieren
            text_result = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "{}")
            return self._calculate_final_score(json.loads(text_result), criteria)
            
        except Exception as e:
            logger.error(f"Gemini Quality Gate Error: {e}")
            return self._fallback_result()

    def _calculate_final_score(self, evaluation_json: Dict, criteria: List[VisionCriterion]) -> Dict:
        """Berechnet den gewichteten Score und findet den schlechtesten Punkt für die Degradation."""
        total_score = 0
        total_weight = 0
        lowest_score = 101
        degradation_suggestion = "make it look more realistic"
        
        scores_map = {item['id']: item for item in evaluation_json.get('scores', [])}
        
        for c in criteria:
            total_weight += c.weight
            score_item = scores_map.get(c.id)
            if score_item:
                score = score_item.get('score', 0)
                total_score += score * c.weight
                
                # Finde das Kriterium mit dem niedrigsten Score für die Korrektur
                if score < lowest_score:
                    lowest_score = score
                    if c.failure_hint:
                        degradation_suggestion = c.failure_hint

        final_score = int(total_score / total_weight) if total_weight > 0 else 0
        
        return {
            "score": final_score,
            "suggestion": degradation_suggestion
        }

    def _fallback_result(self):
        return {"score": 100, "suggestion": ""}

# Singleton Instanz
quality_gate_service = QualityGateService()
