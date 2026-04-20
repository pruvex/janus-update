import logging
import json
import base64
import httpx
from typing import Dict, Any, List, Optional

logger = logging.getLogger("janus_backend")


class QualityGateService:
    async def evaluate_image(
        self,
        provider: str,
        api_key: str,
        image_bytes: bytes,
        prompt: str,
        criteria: Optional[List[Dict]] = None,
        force_json_schema: bool = True
    ) -> Dict[str, Any]:
        """
        Analysiert ein Bild mit dem angegebenen Provider (OpenAI oder Gemini)
        und gibt eine strukturierte JSON-Antwort zurück.
        """
        try:
            # 1. Input-Normalisierung: String (Base64) zu Bytes
            if isinstance(image_bytes, str):
                try:
                    image_bytes = base64.b64decode(image_bytes, validate=True)
                except Exception:
                    logger.warning("image_bytes provided as str but not valid base64; using fallback")
                    return self._fallback_result(reason="Invalid image data (string not base64).")

            # 2. Input-Normalisierung: Sicherstellen, dass es Bytes sind
            if not isinstance(image_bytes, (bytes, bytearray)):
                logger.warning("image_bytes is not bytes/bytearray; attempting conversion")
                try:
                    image_bytes = bytes(image_bytes)
                except (TypeError, ValueError) as e:
                    logger.error(f"Failed to convert image data to bytes: {e}")
                    return self._fallback_result(reason="Invalid image bytes.")

            provider = (provider or "").lower().strip()

            if provider == "openai":
                return await self._evaluate_with_openai(api_key, bytes(image_bytes), prompt, criteria, force_json_schema)
            if provider == "gemini":
                return await self._evaluate_with_gemini(api_key, bytes(image_bytes), prompt, criteria, force_json_schema)

            logger.error(f"Nicht unterstützter Provider im Quality Gate: {provider}")
            return self._fallback_result(reason=f"Unsupported provider: {provider}")

        except Exception as e:
            logger.error(f"Fehler bei der Bildauswertung mit {provider}: {e}", exc_info=True)
            return self._fallback_result(reason="Unhandled exception during evaluation.")

    async def _evaluate_with_openai(
        self,
        api_key: str,
        image_bytes: bytes,
        prompt: str,
        criteria: Optional[List[Dict]] = None,
        force_json_schema: bool = True
    ) -> Dict[str, Any]:
        """Führt die Auswertung mit OpenAI (GPT-4o) durch."""
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=api_key)

        evaluation_prompt = self._build_evaluation_prompt(prompt, criteria, force_json_schema)

        mime = self._guess_mime_type(image_bytes) or "image/jpeg"
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": evaluation_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{base64_image}"},
                    },
                ],
            }
        ]

        # Wir nutzen gpt-4o für beste Vision-Ergebnisse
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            response_format={"type": "json_object"} if force_json_schema else None,
            max_tokens=500,
        )

        content = response.choices[0].message.content
        if not content:
            logger.warning("OpenAI API returned empty content")
            return self._fallback_result(model="gpt-4o", reason="Empty response from OpenAI.")

        if not force_json_schema:
            return {
                "suggestion": content,
                "model": "gpt-4o",
                "usage": {
                    "input_tokens": getattr(response.usage, "prompt_tokens", 0),
                    "output_tokens": getattr(response.usage, "completion_tokens", 0)
                }
            }

        parsed = self._parse_and_normalize_model_json(content)
        usage = {}
        if getattr(response, "usage", None):
            usage = {
                "input_tokens": getattr(response.usage, "prompt_tokens", None),
                "output_tokens": getattr(response.usage, "completion_tokens", None),
            }

        return {**parsed, "usage": usage, "model": "gpt-4o"}

    async def _evaluate_with_gemini(
        self,
        api_key: str,
        image_bytes: bytes,
        prompt: str,
        criteria: Optional[List[Dict]] = None,
        force_json_schema: bool = True
    ) -> Dict[str, Any]:
        """Führt die Auswertung mit Gemini (gemini-3-flash-preview) durch."""
        
        # Diamond Batch 4: Flash-Preview für hohe Quota und stabile Läufe
        model_name = "gemini-3-flash-preview"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

        evaluation_prompt = self._build_evaluation_prompt(prompt, criteria, force_json_schema)
        mime = self._guess_mime_type(image_bytes) or "image/jpeg"
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        full_prompt = evaluation_prompt
        if force_json_schema:
            full_prompt = f"{evaluation_prompt}\n\nREMINDER: Return ONLY a valid JSON object matching the exact schema. No markdown."

        payload = {
            "contents": [{
                "parts": [
                    {"text": full_prompt},
                    {
                        "inline_data": {
                            "mime_type": mime,
                            "data": base64_image
                        }
                    }
                ]
            }],
            # JSON Mode nur erzwingen, wenn gewünscht
            "generationConfig": {"response_mime_type": "application/json" if force_json_schema else "text/plain"}
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                response_json = response.json()
        except Exception as e:
            logger.error(f"Gemini API Error: {e}")
            return self._fallback_result(model=model_name, reason=f"Gemini API Error: {str(e)}")

        # Extrahiere Text aus Gemini Antwort
        try:
            content = response_json["candidates"][0]["content"]["parts"][0]["text"]
            if not content:
                logger.warning("Gemini API returned empty content")
                return self._fallback_result(model=model_name, reason="Empty response from Gemini.")
                
            if not force_json_schema:
                return {
                    "suggestion": content,
                    "model": model_name,
                    "usage": {
                        "input_tokens": response_json.get("usageMetadata", {}).get("promptTokenCount", 0),
                        "output_tokens": response_json.get("usageMetadata", {}).get("candidatesTokenCount", 0)
                    }
                }
                
            parsed = self._parse_and_normalize_model_json(content)
        except (KeyError, IndexError) as e:
            logger.warning(f"Gemini API returned unexpected structure: {response_json}")
            return self._fallback_result(model=model_name, reason="Invalid response structure from Gemini.")
        
        # Usage Metriken extrahieren (falls vorhanden)
        usage = {}
        if "usageMetadata" in response_json:
             usage = {
                "input_tokens": response_json["usageMetadata"].get("promptTokenCount"),
                "output_tokens": response_json["usageMetadata"].get("candidatesTokenCount"),
            }

        return {**parsed, "usage": usage, "model": model_name}

    def _build_evaluation_prompt(self, prompt: str, criteria: Optional[List[Dict]] = None, force_json_schema: bool = True) -> str:
        if not force_json_schema:
            return prompt
            
        base_prompt = """
You are a strict Image Quality Assurance AI.
Your ONLY job is to evaluate the given image against the user's prompt and professional photographic standards.

You MUST return a JSON object with EXACTLY this structure:
{
  "score": <integer between 0 and 100>,
  "reason": "<short explanation of the score>",
  "suggestion": "<specific instruction to improve the prompt if score < 80, else null>",
  "keywords": ["list", "of", "relevant", "keywords"],
  "style": "artistic_style"
}

SCORING GUIDE:
- 100: Perfection. Photorealistic, follows prompt perfectly, no artifacts.
- 80-99: Excellent. Minor flaws only visible on close inspection.
- 60-79: Good. Follows prompt, but has visible AI artifacts or logical errors.
- <60: Fail. Does not follow prompt, bad anatomy, heavy artifacts, or looks fake.

CRITICAL:
- Do NOT describe the image content unless it is wrong.
- Focus on technical quality (sharpness, anatomy, lighting, physics).
- The "score" field is MANDATORY and must be an integer.
- Include relevant keywords and style in the response.

USER PROMPT:
{json.dumps(prompt, ensure_ascii=False)}
""".strip()

        if not criteria:
            return base_prompt

        criteria_list = "\n".join(
            [f"- {c.get('id', 'Custom')}: {c.get('description', '')}" for c in criteria]
        )

        return f"""{base_prompt}

ADDITIONAL CRITERIA TO CONSIDER:
{criteria_list}

IMPORTANT: Still return the exact JSON structure as specified above.
""".strip()

    def _parse_and_normalize_model_json(self, response_content: str) -> Dict[str, Any]:
        raw = (response_content or "").strip()
        if not raw:
            return self._fallback_result(reason="Empty model response.")

        # Remove markdown fences
        if "```" in raw:
            if "```json" in raw:
                # Versuche alles zwischen ```json und ``` zu finden
                try:
                    raw = raw.split("```json", 1)[1].split("```", 1)[0]
                except IndexError:
                    pass # Fallback auf Original
            else:
                try:
                    raw = raw.split("```", 1)[1].split("```", 1)[0]
                except IndexError:
                    pass
            raw = raw.strip()

        obj = None
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            extracted = self._extract_first_json_object(raw)
            if extracted is not None:
                try:
                    obj = json.loads(extracted)
                except json.JSONDecodeError:
                    pass
        
        if not isinstance(obj, dict):
            logger.error(f"Failed to parse JSON response. Raw: {raw}")
            return self._fallback_result(reason="Failed to parse model JSON.")

        # Normalize
        score = obj.get("score", 0)
        try:
            score = int(score)
        except:
            score = 0
        score = max(0, min(100, score))

        return {
            "score": score,
            "reason": str(obj.get("reason", "")).strip(),
            "suggestion": obj.get("suggestion"),
            "quality": score, # Alias
        }

    def _extract_first_json_object(self, text: str) -> Optional[str]:
        if not text: return None
        start = text.find("{")
        if start == -1: return None
        depth = 0
        for i in range(start, len(text)):
            ch = text[i]
            if ch == "{": depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0: return text[start : i + 1]
        return None

    def _guess_mime_type(self, data: bytes) -> Optional[str]:
        if not data or len(data) < 12: return None
        if data.startswith(b"\x89PNG\r\n\x1a\n"): return "image/png"
        if data.startswith(b"\xff\xd8\xff"): return "image/jpeg"
        if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"): return "image/gif"
        if data[0:4] == b"RIFF" and data[8:12] == b"WEBP": return "image/webp"
        return None

    def _fallback_result(self, model: str = "unknown", reason: str = "Fallback", error: Optional[str] = None) -> Dict[str, Any]:
        payload = {
            "score": 0,
            "reason": reason,
            "suggestion": "QualityGate failed.",
            "quality": 0,
            "usage": {},
            "model": model,
        }
        if error: payload["error"] = error
        return payload

# Singleton-Instanz
quality_gate_service = QualityGateService()