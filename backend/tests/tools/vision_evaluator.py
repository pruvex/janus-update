#!/usr/bin/env python3
"""E2E Vision Evaluator (Diamond Standard).

Validates full pipeline for each image and provider:
CLIP -> Cloud -> Fusion -> Orchestrator Prompt -> Final Text
"""

import argparse
import asyncio
import base64
import json
import logging
import os
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import patch

from colorama import Fore, Style, init
from dotenv import load_dotenv

# File is located in backend/tests/tools -> project root is parents[3]
PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")
sys.path.insert(0, str(PROJECT_ROOT))

from backend.data import crud, schemas
from backend.data.database import get_db_context
from backend.services.chat_orchestrator import ChatOrchestrator
from backend.services.context_manager import ContextManager
from backend.services.vision.profiles import gemini_profile, openai_profile
from backend.services.vision.utils import get_mapped_portrait_facts
from backend.services.vision_service import vision_service
from backend.utils.config_loader import load_model_catalog
from backend.utils.paths import get_app_data_dir, resource_path

logger = logging.getLogger("janus_backend")
init(autoreset=True)

PROVIDERS = ("openai", "gemini")
DEFAULT_SOURCE_REQUIRED_SLOTS = ("upper_primary", "lower_primary", "footwear", "ambiente")
KEYWORDS_TO_TRACK = {
    "Karomuster": ["karomuster", "karo", "glencheck", "kariert"],
    "Leder": ["leder"],
    "Nike": ["nike"],
}


@dataclass
class E2EResult:
    image_name: str
    provider: str
    ground_truth: Dict[str, Any]
    clip_facts: Dict[str, Any]
    cloud_result: Dict[str, Any]
    fused_facts: Dict[str, Any]
    final_text: str
    error: Optional[str] = None
    missing_details: List[str] = field(default_factory=list)
    contradiction_flags: List[str] = field(default_factory=list)
    source_of_truth: Dict[str, Any] = field(default_factory=dict)


class VisionEvaluator:
    @staticmethod
    def _detect_contradictions(fused_facts: Dict[str, Any]) -> List[str]:
        flags: List[str] = []
        fused_facts = fused_facts or {}

        lower_text = " ".join(
            [
                str(fused_facts.get("LEGWEAR", "") or ""),
                str(fused_facts.get("LEGWEAR_SATZ", "") or ""),
                str(fused_facts.get("OUTFIT_UNTEN", "") or ""),
            ]
        ).lower()
        has_jeans = any(token in lower_text for token in ["jeans", "denim"])
        has_chino = "chino" in lower_text
        has_trousers = any(token in lower_text for token in ["trousers", "pants"])
        if "hose" in lower_text and not any(token in lower_text for token in ["jeans", "denim"]):
            has_trousers = True
        has_skirt = any(token in lower_text for token in ["rock", "skirt"])
        lower_classes = int(has_jeans) + int(has_chino or has_trousers) + int(has_skirt)
        if lower_classes > 1:
            flags.append("lower_slot_conflict")

        upper_text = " ".join(
            [
                str(fused_facts.get("KLEIDUNG", "") or ""),
                str(fused_facts.get("OUTERWEAR", "") or ""),
                str(fused_facts.get("INNER_LAYER", "") or ""),
                str(fused_facts.get("OUTFIT_OBEN", "") or ""),
            ]
        ).lower()
        has_tshirt = any(token in upper_text for token in ["t-shirt", "crew neck", "shirt"])
        has_turtleneck = any(token in upper_text for token in ["rollkragen", "turtleneck", "roll neck", "mock neck", "high neck"])
        has_cardigan = any(token in upper_text for token in ["cardigan", "strickjacke", "knit cardigan"])
        if has_tshirt and has_turtleneck and has_cardigan:
            flags.append("upper_triple_conflict")

        validation_flags = fused_facts.get("VALIDATION_FLAGS", [])
        if isinstance(validation_flags, list):
            for raw_flag in validation_flags:
                flag_text = str(raw_flag or "").strip().lower()
                if not flag_text:
                    continue
                if flag_text.startswith("missing_source_slot:"):
                    continue
                flags.append(f"validator_{flag_text}")

        # de-duplicate, preserve order
        deduped: List[str] = []
        seen = set()
        for item in flags:
            if item in seen:
                continue
            seen.add(item)
            deduped.append(item)
        return deduped

    @staticmethod
    def _normalize_text(value: str) -> str:
        text = str(value or "").strip().lower()
        if not text:
            return ""

        text = unicodedata.normalize("NFKD", text)
        text = "".join(ch for ch in text if not unicodedata.combining(ch))
        text = text.replace("ß", "ss")
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        return " ".join(text.split())

    @staticmethod
    def _compact_text(value: str) -> str:
        return VisionEvaluator._normalize_text(value).replace(" ", "")

    @staticmethod
    def _tokenize(value: str) -> List[str]:
        text = VisionEvaluator._normalize_text(value)
        return [token for token in text.split(" ") if token]

    @staticmethod
    def _token_soft_equal(expected: str, candidate: str) -> bool:
        if expected == candidate:
            return True
        if len(expected) >= 5 and expected in candidate:
            return True
        if len(candidate) >= 5 and candidate in expected:
            return True
        if len(expected) >= 4 and len(candidate) >= 4 and expected[:4] == candidate[:4]:
            return True
        if abs(len(expected) - len(candidate)) <= 1 and len(expected) >= 4 and len(candidate) >= 4 and expected[:3] == candidate[:3]:
            return True
        return False

    @staticmethod
    def _rough_phrase_match(expected_phrase: str, haystack_text: str) -> bool:
        expected_norm = VisionEvaluator._normalize_text(expected_phrase)
        haystack_norm = VisionEvaluator._normalize_text(haystack_text)
        expected_compact = VisionEvaluator._compact_text(expected_phrase)
        haystack_compact = VisionEvaluator._compact_text(haystack_text)

        if not expected_norm:
            return True
        if expected_norm in haystack_norm:
            return True
        if expected_compact and expected_compact in haystack_compact:
            return True

        expected_tokens = [t for t in VisionEvaluator._tokenize(expected_norm) if len(t) >= 3]
        haystack_tokens = VisionEvaluator._tokenize(haystack_norm)
        if not expected_tokens or not haystack_tokens:
            return False

        matched = 0
        for exp in expected_tokens:
            if any(VisionEvaluator._token_soft_equal(exp, got) for got in haystack_tokens):
                matched += 1

        required_ratio = 0.67 if len(expected_tokens) <= 3 else 0.75
        return (matched / len(expected_tokens)) >= required_ratio

    @staticmethod
    def _expand_expected_phrases(expected: Any) -> List[str]:
        if expected is None:
            return []
        if isinstance(expected, list):
            phrases: List[str] = []
            for item in expected:
                phrases.extend(VisionEvaluator._expand_expected_phrases(item))
            # dedupe, preserve order
            seen_list = set()
            unique_phrases: List[str] = []
            for phrase in phrases:
                key = phrase.lower()
                if key in seen_list:
                    continue
                seen_list.add(key)
                unique_phrases.append(phrase)
            return unique_phrases
        if not isinstance(expected, str):
            expected = str(expected)

        raw = expected.strip()
        if not raw:
            return []

        parts = [raw]
        for sep in [",", " und ", " / "]:
            next_parts: List[str] = []
            for p in parts:
                if sep in p:
                    next_parts.extend([token.strip() for token in p.split(sep) if token.strip()])
                else:
                    next_parts.append(p.strip())
            parts = next_parts

        # dedupe, preserve order
        seen = set()
        final_parts: List[str] = []
        for p in parts:
            key = p.lower()
            if key not in seen:
                seen.add(key)
                final_parts.append(p)
        return final_parts

    def _find_missing_gt_details(
        self,
        ground_truth: Dict[str, Any],
        final_text: str,
        fused_facts: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        missing: List[str] = []
        normalized_final = self._normalize_text(final_text)
        fused_facts = fused_facts or {}

        def _contains_exclusion_phrase(haystack: str, phrase: str) -> bool:
            haystack = str(haystack or "")
            phrase = str(phrase or "")
            if not phrase:
                return False

            # Token-aware matching to avoid false positives like "hose" in "strumpfhose".
            normalized_chars = [ch if (ch.isalnum() or ch.isspace()) else " " for ch in haystack]
            tokenized_haystack = " ".join("".join(normalized_chars).split())
            hay_tokens = tokenized_haystack.split(" ") if tokenized_haystack else []
            phrase_tokens = phrase.split(" ")

            if len(phrase_tokens) == 1:
                return phrase_tokens[0] in hay_tokens

            return phrase in tokenized_haystack

        for category, expected in (ground_truth or {}).items():
            if category == "NOTIZ":
                note_raw = str(expected or "").strip()
                if note_raw:
                    note_variants = [note_raw]
                    note_variants.extend(part.strip() for part in note_raw.split(";") if part.strip())
                    fused_value = fused_facts.get(category)
                    fused_text = ""
                    if isinstance(fused_value, list):
                        fused_text = " ".join(str(v) for v in fused_value)
                    elif fused_value is not None:
                        fused_text = str(fused_value)
                    combined_haystack = f"{final_text} {fused_text}"
                    if not any(self._rough_phrase_match(variant, combined_haystack) for variant in note_variants):
                        missing.append(f"{category}: {note_raw}")
                continue

            phrases = self._expand_expected_phrases(expected)

            # Ausschlussliste bedeutet: diese Begriffe dürfen NICHT im Endtext stehen.
            if category == "AUSSCHLUSS_PFLICHT":
                for phrase in phrases:
                    normalized_phrase = self._normalize_text(phrase)
                    if normalized_phrase and _contains_exclusion_phrase(normalized_final, normalized_phrase):
                        missing.append(f"{category} verletzt: {phrase}")
                continue

            fused_value = fused_facts.get(category)
            fused_text = ""
            if isinstance(fused_value, list):
                fused_text = " ".join(str(v) for v in fused_value)
            elif fused_value is not None:
                fused_text = str(fused_value)

            combined_haystack = f"{final_text} {fused_text}"
            for phrase in phrases:
                if not self._rough_phrase_match(phrase, combined_haystack):
                    missing.append(f"{category}: {phrase}")
        return missing

    @staticmethod
    def _fingerprint_key(value: Optional[str]) -> str:
        if not value:
            return "<missing>"
        if len(value) <= 10:
            return f"{value[:2]}...{value[-2:]}"
        return f"{value[:5]}...{value[-5:]}"

    def __init__(
        self,
        matrix_dir: Path,
        cluster: Optional[str] = None,
        image_name: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        providers: Optional[List[str]] = None,
        raw_mode: bool = False,
        live_mode: bool = False,
    ):
        resolved_matrix_dir = Path(str(matrix_dir).replace("/", os.sep)).expanduser()
        if cluster:
            resolved_matrix_dir = PROJECT_ROOT / "backend" / "tests" / "vision_matrix" / cluster

        self.matrix_dir = resolved_matrix_dir.resolve()
        self.image_name_filter = (image_name or "").strip()
        self.logger = logging.getLogger(__name__)

        self.api_keys = {
            "openai": openai_api_key or os.getenv("OPENAI_API_KEY"),
            "gemini": gemini_api_key or os.getenv("GEMINI_API_KEY"),
        }

        selected = [str(p or "").strip().lower() for p in (providers or list(PROVIDERS))]
        selected = [p for p in selected if p in PROVIDERS]
        self.providers = tuple(selected) if selected else PROVIDERS
        self.raw_mode = bool(raw_mode)
        self.live_mode = bool(live_mode)

        # Harte Injektion in ENV für alle nachgelagerten Provider-Libraries.
        if self.api_keys.get("openai"):
            os.environ["OPENAI_API_KEY"] = self.api_keys["openai"]
        if self.api_keys.get("gemini"):
            os.environ["GEMINI_API_KEY"] = self.api_keys["gemini"]
            os.environ["GOOGLE_API_KEY"] = self.api_keys["gemini"]

        print(
            f"Using OpenAI Key: {self._fingerprint_key(self.api_keys.get('openai'))} | "
            f"Gemini Key: {self._fingerprint_key(self.api_keys.get('gemini'))}"
        )

        self.model_catalog = load_model_catalog() or {}
        context_models = list(self.model_catalog.values())
        if not context_models:
            context_models = [{"id": "gpt-5.4-nano", "context_window": 8000}]

        self.context_manager = ContextManager(context_models)

        app_data = Path(get_app_data_dir())
        self.config_file_path = app_data / "config.json"
        self.personalities_file_path = app_data / "personalities.json"
        self.template_config_file_path = Path(resource_path("backend/config/config.json"))
        self.template_personalities_file_path = Path(resource_path("backend/config/personalities.json"))

    def _normalize_expected_data(self, ground_truth: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(ground_truth, dict):
            nested_expected = ground_truth.get("expected")
            if isinstance(nested_expected, dict):
                return nested_expected
        return ground_truth if isinstance(ground_truth, dict) else {}

    def _resolve_ground_truth_file(self, image_file: Path) -> Path:
        simple_json = image_file.with_suffix(".json")
        if simple_json.exists():
            return simple_json

        suffix_json = image_file.with_suffix(f"{image_file.suffix}.json")
        if suffix_json.exists():
            return suffix_json

        default_json = image_file.with_suffix(".jpg.json")
        if default_json.exists():
            return default_json

        stem = image_file.stem
        numeric = "".join(ch for ch in stem if ch.isdigit())
        if numeric:
            fallback = image_file.with_name(f"{int(numeric)}.jpg.json")
            if fallback.exists():
                return fallback

        return default_json

    def load_ground_truth(self, json_path: Path) -> Dict[str, Any]:
        try:
            normalized = Path(str(json_path).replace("/", os.sep))
            return json.loads(normalized.read_text(encoding="utf-8-sig"))
        except Exception as exc:
            self.logger.error("Fehler beim Laden von %s: %s", json_path, exc)
            return {}

    @staticmethod
    def _to_data_url(image_path: Path) -> str:
        ext = image_path.suffix.lower()
        mime = "image/jpeg" if ext in {".jpg", ".jpeg"} else "image/png"
        payload = base64.b64encode(image_path.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{payload}"

    def _build_orchestrator(self, db_session) -> ChatOrchestrator:
        return ChatOrchestrator(
            db=db_session,
            context_manager=self.context_manager,
            model_catalog=self.model_catalog,
            config_file_path=str(self.config_file_path),
            template_config_file_path=str(self.template_config_file_path),
            personalities_file_path=str(self.personalities_file_path),
            template_personalities_file_path=str(self.template_personalities_file_path),
        )

    def _run_local_clip(self, image_bytes: bytes, db_session, provider: str, image_name: str) -> Dict[str, Any]:
        profile = openai_profile if provider == "openai" else gemini_profile
        local_result = vision_service.process_image(
            image_bytes,
            db_session,
            profile=profile,
            image_name=image_name,
        )
        return get_mapped_portrait_facts(
            local_result.get("feature_report", {}),
            local_result.get("context", {}),
            vision_mode="eval",
        )

    async def _run_provider_e2e(
        self,
        image_path: Path,
        provider: str,
        api_key: Optional[str],
        db,
    ) -> E2EResult:
        captured: Dict[str, Any] = {}
        ground_truth_file = self._resolve_ground_truth_file(image_path)
        ground_truth: Dict[str, Any] = {}
        if ground_truth_file.exists():
            ground_truth = self._normalize_expected_data(self.load_ground_truth(ground_truth_file))

        print(f"Using {provider} key: {self._fingerprint_key(api_key)}")

        try:
            image_bytes = image_path.read_bytes()
            clip_facts = self._run_local_clip(image_bytes, db, provider, image_path.name)

            orchestrator = self._build_orchestrator(db)
            matrix_hint = self.matrix_dir.name
            if self.raw_mode:
                chat_title = f"LIVEPARITY {matrix_hint}/{image_path.name} [{provider}]"
            else:
                chat_title = f"E2E {matrix_hint}/{image_path.name} [{provider}]"
            chat = crud.create_chat(db, title=chat_title)

            request = schemas.ChatRequest(
                prompt="Bitte beschreibe die Person auf dem Bild präzise und faktenbasiert.",
                content=[
                    schemas.ContentPart(type="text", text="Bitte analysiere dieses Bild vollständig."),
                    schemas.ContentPart(type="image_url", image_url=self._to_data_url(image_path)),
                ],
                provider=provider,
                model=orchestrator.MODEL_HIERARCHY[provider]["speed"],
                api_key=api_key,
                chat_id=chat.id,
            )

            import backend.services.chat_orchestrator as chat_orchestrator_module
            import backend.services.vision.utils as vision_utils_module

            original_fuse = chat_orchestrator_module.fuse_vision_results

            def _fuse_wrapper(local_result: Dict[str, Any], cloud_result: Dict[str, Any], **kwargs) -> Dict[str, Any]:
                fused = original_fuse(local_result, cloud_result, **kwargs)
                captured["cloud_result"] = cloud_result
                captured["fused_facts"] = fused
                return fused

            def _key_lookup(_service_name: str, provider_name: str) -> Optional[str]:
                if provider_name == provider:
                    return api_key
                return self.api_keys.get(provider_name)

            previous_eval_calibration = os.environ.get("JANUS_ENABLE_EVAL_CALIBRATION")
            previous_literal_backfill = os.environ.get("JANUS_ENABLE_STRICT_LITERAL_BACKFILL")
            previous_eval_calibration_flag = getattr(vision_utils_module, "_ENABLE_EVAL_CALIBRATION", True)
            previous_literal_backfill_flag = getattr(chat_orchestrator_module, "_ENABLE_STRICT_LITERAL_BACKFILL", True)
            try:
                os.environ["JANUS_ENABLE_EVAL_CALIBRATION"] = "0" if self.raw_mode else "1"
                os.environ["JANUS_ENABLE_STRICT_LITERAL_BACKFILL"] = "0" if self.raw_mode else "1"
                vision_utils_module._ENABLE_EVAL_CALIBRATION = not self.raw_mode
                chat_orchestrator_module._ENABLE_STRICT_LITERAL_BACKFILL = not self.raw_mode
                with patch.object(chat_orchestrator_module, "fuse_vision_results", side_effect=_fuse_wrapper):
                    with patch.object(chat_orchestrator_module.keyring, "get_password", side_effect=_key_lookup):
                        response = await orchestrator.handle_chat_request(request)
            finally:
                vision_utils_module._ENABLE_EVAL_CALIBRATION = previous_eval_calibration_flag
                chat_orchestrator_module._ENABLE_STRICT_LITERAL_BACKFILL = previous_literal_backfill_flag
                if previous_eval_calibration is None:
                    os.environ.pop("JANUS_ENABLE_EVAL_CALIBRATION", None)
                else:
                    os.environ["JANUS_ENABLE_EVAL_CALIBRATION"] = previous_eval_calibration
                if previous_literal_backfill is None:
                    os.environ.pop("JANUS_ENABLE_STRICT_LITERAL_BACKFILL", None)
                else:
                    os.environ["JANUS_ENABLE_STRICT_LITERAL_BACKFILL"] = previous_literal_backfill

            return E2EResult(
                image_name=image_path.name,
                provider=provider,
                ground_truth=ground_truth,
                clip_facts=clip_facts,
                cloud_result=captured.get("cloud_result", {}),
                fused_facts=captured.get("fused_facts", {}),
                final_text=response.get("text", ""),
                contradiction_flags=self._detect_contradictions(captured.get("fused_facts", {})),
                source_of_truth=captured.get("fused_facts", {}).get("SOURCE_OF_TRUTH", {}),
                missing_details=self._find_missing_gt_details(
                    ground_truth,
                    response.get("text", ""),
                    captured.get("fused_facts", {}),
                ),
            )
        except Exception as exc:
            return E2EResult(
                image_name=image_path.name,
                provider=provider,
                ground_truth=ground_truth,
                clip_facts={},
                cloud_result={},
                fused_facts={},
                final_text="",
                error=str(exc),
                contradiction_flags=["runtime_error"],
                source_of_truth={},
            )

    @staticmethod
    def _json_block(title: str, payload: Any):
        print(f"\n{Style.BRIGHT}{title}{Style.RESET_ALL}")
        if isinstance(payload, (dict, list)):
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(str(payload))

    @staticmethod
    def _contains_pattern(cloud_result: Dict[str, Any]) -> bool:
        text = json.dumps(cloud_result or {}, ensure_ascii=False).lower()
        return any(token in text for token in ["karo", "karomuster", "glencheck", "checkered", "plaid", "tartan", "kariert"])

    def _print_keyword_checks(self, ground_truth: Dict[str, Any], final_text: str):
        final_lower = (final_text or "").lower()
        gt_lower = json.dumps(ground_truth or {}, ensure_ascii=False).lower()

        print(f"\n{Style.BRIGHT}KEYWORD-CHECK{Style.RESET_ALL}")
        for label, tokens in KEYWORDS_TO_TRACK.items():
            expected = any(token in gt_lower for token in tokens)
            if not expected:
                print(f"  - {label}: {Fore.CYAN}N/A{Style.RESET_ALL} (nicht im GT erwartet)")
                continue
            found = any(token in final_lower for token in tokens)
            status = f"{Fore.GREEN}FOUND{Style.RESET_ALL}" if found else f"{Fore.RED}MISSING{Style.RESET_ALL}"
            print(f"  - {label}: {status}")

    def _print_provider_result(self, title: str, result: E2EResult):
        print(f"\n{Style.BRIGHT}{title}{Style.RESET_ALL}")
        if result.error:
            print(f"{Fore.RED}ERROR: {result.error}{Style.RESET_ALL}")
            return

        self._json_block("CLIP", result.clip_facts)
        self._json_block("CLOUD", result.cloud_result)
        pattern_status = f"{Fore.GREEN}YES{Style.RESET_ALL}" if self._contains_pattern(result.cloud_result) else f"{Fore.YELLOW}NO{Style.RESET_ALL}"
        print(f"\nCloud Pattern erkannt (Karo/Glencheck): {pattern_status}")
        self._json_block("FUSED_FACTS", result.fused_facts)
        self._json_block("FINAL", result.final_text)
        self._print_keyword_checks(result.ground_truth, result.final_text)
        if result.missing_details:
            print(f"\n{Fore.RED}STRICT-V3 MISSING DETAILS ({len(result.missing_details)}):{Style.RESET_ALL}")
            for missing in result.missing_details:
                print(f"  - {missing}")
        else:
            print(f"\n{Fore.GREEN}STRICT-V3: Alle Ground-Truth-Details im Finaltext enthalten.{Style.RESET_ALL}")

    @staticmethod
    def _extract_image_number(image_file: Path) -> Optional[int]:
        stem = image_file.stem
        digits = "".join(ch for ch in stem if ch.isdigit())
        if not digits:
            return None
        return int(digits)

    @staticmethod
    def _parse_range(range_value: Optional[str]) -> Optional[tuple[int, int]]:
        if not range_value:
            return None
        value = range_value.strip()
        if "-" not in value:
            return None
        left, right = value.split("-", 1)
        if not left.strip().isdigit() or not right.strip().isdigit():
            return None
        start = int(left.strip())
        end = int(right.strip())
        if start > end:
            start, end = end, start
        return (start, end)

    def _print_e2e_comparison(self, image_name: str, expected: Dict[str, Any], by_provider: Dict[str, E2EResult]):
        print(f"\n{'=' * 120}")
        print(f"{Style.BRIGHT}{image_name}{Style.RESET_ALL}")
        print(f"{'=' * 120}")
        if self.live_mode and not expected:
            print(f"{Style.BRIGHT}EXPECTED (GT){Style.RESET_ALL}\n<live-mode: no ground-truth required>")
        else:
            self._json_block("EXPECTED (GT)", expected)

        openai_result = by_provider.get("openai")
        if openai_result:
            self._print_provider_result("RESULT (OPENAI): gpt-4o + gpt-5.2", openai_result)

        gemini_result = by_provider.get("gemini")
        if gemini_result:
            self._print_provider_result("RESULT (GEMINI): gemini-3-flash-preview", gemini_result)

    async def test_orchestrator_e2e(self, image_path: Path, db=None) -> List[E2EResult]:
        runs: List[E2EResult] = []
        for provider in self.providers:
            api_key = self.api_keys.get(provider)
            if not api_key:
                print(f"{Fore.YELLOW}WARN: Kein API-Key für {provider}. Versuch läuft trotzdem (erwarteter Fehler möglich).{Style.RESET_ALL}")
            if db is not None:
                result = await self._run_provider_e2e(image_path, provider, api_key, db)
            else:
                with get_db_context() as provider_db:
                    result = await self._run_provider_e2e(image_path, provider, api_key, provider_db)
            runs.append(result)
        return runs

    async def run_e2e(self, db, image_range: Optional[str] = None) -> int:
        if not self.matrix_dir.exists():
            print(f"{Fore.RED}Matrix-Verzeichnis nicht gefunden: {self.matrix_dir}{Style.RESET_ALL}")
            return 2

        image_files = sorted(
            list(Path(self.matrix_dir).glob("*.jpg")) + list(Path(self.matrix_dir).glob("*.jpeg"))
        )
        if self.image_name_filter:
            image_files = [img for img in image_files if img.name.lower() == self.image_name_filter.lower()]

        parsed_range = self._parse_range(image_range)
        if image_range and not parsed_range:
            print(f"{Fore.RED}Ungültiges --range Format: {image_range}. Erwartet z.B. 41-60{Style.RESET_ALL}")
            return 2
        if parsed_range:
            start, end = parsed_range
            image_files = [
                img
                for img in image_files
                if (num := self._extract_image_number(img)) is not None and start <= num <= end
            ]

        if not image_files:
            print(f"{Fore.RED}Keine .jpg Dateien gefunden in: {self.matrix_dir}{Style.RESET_ALL}")
            return 2

        total_runs = 0
        failed_runs = 0
        strict_failed_runs = 0
        contradiction_runs = 0
        source_map_runs = 0
        cloud_verifier_hits = 0
        resolver_veto_hits = 0
        slot_counter = 0
        required_slot_hits = 0
        required_slot_total = 0
        semantic_validation_issue_runs = 0
        required_slots = tuple(getattr(self, "source_required_slots", DEFAULT_SOURCE_REQUIRED_SLOTS))

        for image_file in image_files:
            gt_file = self._resolve_ground_truth_file(image_file)
            if not gt_file.exists() and not self.live_mode:
                print(f"{Fore.YELLOW}SKIP (keine GT-Datei): {image_file.name}{Style.RESET_ALL}")
                continue

            print(f"\n{Style.BRIGHT}Verarbeite Bild: {image_file}{Style.RESET_ALL}")
            results = await self.test_orchestrator_e2e(image_file, db)
            by_provider = {result.provider: result for result in results}
            expected = results[0].ground_truth if results else {}
            self._print_e2e_comparison(image_file.name, expected, by_provider)
            for result in results:
                total_runs += 1
                if result.error:
                    failed_runs += 1
                elif (not self.live_mode) and result.missing_details:
                    strict_failed_runs += 1
                if result.contradiction_flags:
                    contradiction_runs += 1
                if isinstance(result.source_of_truth, dict) and result.source_of_truth:
                    source_map_runs += 1
                    for _, src in result.source_of_truth.items():
                        slot_counter += 1
                        src_text = str(src or "").lower()
                        if "cloud_verifier" in src_text:
                            cloud_verifier_hits += 1
                        if "resolver_cloud_veto" in src_text:
                            resolver_veto_hits += 1

                if required_slots:
                    required_slot_total += len(required_slots)
                    if isinstance(result.source_of_truth, dict) and result.source_of_truth:
                        for slot in required_slots:
                            if str(result.source_of_truth.get(slot, "") or "").strip():
                                required_slot_hits += 1

                validation_flags = result.fused_facts.get("VALIDATION_FLAGS", []) if isinstance(result.fused_facts, dict) else []
                if isinstance(validation_flags, list) and any(str(flag or "").strip() for flag in validation_flags):
                    semantic_validation_issue_runs += 1

            # Kleine asynchrone Pause als Puffer zwischen Bildern.
            await asyncio.sleep(0.1)

        ok_runs = total_runs - failed_runs
        print(f"\n{'=' * 120}")
        print(f"E2E SUMMARY: {ok_runs}/{total_runs} erfolgreiche Provider-Runs")
        if not self.live_mode:
            print(f"STRICT-V3 SUMMARY: {total_runs - strict_failed_runs}/{total_runs} Runs ohne fehlende Detail-Fakten")
        else:
            print("LIVE-MODE SUMMARY: GT-Strict-Checks deaktiviert (unseen/private image evaluation).")
        contradiction_rate = (contradiction_runs / total_runs) if total_runs else 0.0
        source_map_coverage = (source_map_runs / total_runs) if total_runs else 0.0
        cloud_verifier_share = (cloud_verifier_hits / slot_counter) if slot_counter else 0.0
        resolver_veto_share = (resolver_veto_hits / slot_counter) if slot_counter else 0.0
        slot_source_coverage = (required_slot_hits / required_slot_total) if required_slot_total else 0.0
        semantic_validation_rate = 1.0 - ((semantic_validation_issue_runs / total_runs) if total_runs else 0.0)
        print(f"KPI SUMMARY: contradiction_rate={contradiction_rate:.3f}, source_map_coverage={source_map_coverage:.3f}, slot_source_coverage={slot_source_coverage:.3f}, semantic_validation_rate={semantic_validation_rate:.3f}, cloud_verifier_share={cloud_verifier_share:.3f}, resolver_veto_share={resolver_veto_share:.3f}")
        if failed_runs:
            print(f"{Fore.RED}{failed_runs} Runs mit Fehlern{Style.RESET_ALL}")
            return 1
        if strict_failed_runs and not self.live_mode:
            print(f"{Fore.RED}{strict_failed_runs} Runs mit fehlenden GT-Details im Finaltext{Style.RESET_ALL}")
            return 1
        if getattr(self, "kpi_gate", False):
            if contradiction_rate > self.max_contradiction_rate:
                print(
                    f"{Fore.RED}KPI-GATE FAIL: contradiction_rate {contradiction_rate:.3f} > {self.max_contradiction_rate:.3f}{Style.RESET_ALL}"
                )
                return 1
            if source_map_coverage < self.min_source_map_coverage:
                print(
                    f"{Fore.RED}KPI-GATE FAIL: source_map_coverage {source_map_coverage:.3f} < {self.min_source_map_coverage:.3f}{Style.RESET_ALL}"
                )
                return 1
            if slot_source_coverage < self.min_slot_source_coverage:
                print(
                    f"{Fore.RED}KPI-GATE FAIL: slot_source_coverage {slot_source_coverage:.3f} < {self.min_slot_source_coverage:.3f}{Style.RESET_ALL}"
                )
                return 1
            if semantic_validation_rate < self.min_semantic_validation_rate:
                print(
                    f"{Fore.RED}KPI-GATE FAIL: semantic_validation_rate {semantic_validation_rate:.3f} < {self.min_semantic_validation_rate:.3f}{Style.RESET_ALL}"
                )
                return 1
        print(f"{Fore.GREEN}Alle E2E-Runs abgeschlossen.{Style.RESET_ALL}")
        return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="E2E Diamond-Standard Vision Evaluator")
    parser.add_argument("--e2e", action="store_true", help="Führt den vollständigen Orchestrator-E2E-Test aus")
    parser.add_argument("--raw", action="store_true", help="Deaktiviert Eval-Kalibrierung und Literal-Backfill für realitätsnahen E2E-Run")
    parser.add_argument("--live-mode", action="store_true", help="Live-Parity-Modus: raw/live-nahe Ausführung ohne GT-Pflicht (für unseen/private Bilder)")
    parser.add_argument("--cluster", type=str, default=None, help="Optional: Cluster-Name, z.B. cluster_1")
    parser.add_argument(
        "--matrix-dir",
        type=str,
        default=str(PROJECT_ROOT / "backend" / "tests" / "vision_matrix" / "Supercluster"),
        help="Pfad zum Matrix-Ordner mit Bildern + Ground Truth",
    )
    parser.add_argument("--image", type=str, default=None, help="Optional: genau ein Bildname, z.B. Cluster1-1.jpg")
    parser.add_argument("--range", type=str, default=None, help="Optional: numerischer Bildbereich, z.B. 41-60")
    parser.add_argument("--openai-api-key", type=str, default=None, help="Optionaler OpenAI API Key")
    parser.add_argument("--gemini-api-key", type=str, default=None, help="Optionaler Gemini API Key")
    parser.add_argument("--providers", type=str, default="openai,gemini", help="Kommagetrennte Providerliste, z.B. gemini oder openai,gemini")
    parser.add_argument("--kpi-gate", action="store_true", help="Aktiviert KPI-Gate fuer contradiction/source-map")
    parser.add_argument("--max-contradiction-rate", type=float, default=0.0, help="Maximal erlaubte Widerspruchsrate")
    parser.add_argument("--min-source-map-coverage", type=float, default=0.95, help="Mindestanteil Runs mit SOURCE_OF_TRUTH")
    parser.add_argument("--min-slot-source-coverage", type=float, default=0.80, help="Mindestabdeckung der Pflicht-Slots in SOURCE_OF_TRUTH")
    parser.add_argument("--min-semantic-validation-rate", type=float, default=0.85, help="Mindestrate validator-cleaner Runs")
    return parser.parse_args()


async def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    args = parse_args()
    if not args.e2e:
        print("Dieser Evaluator läuft im E2E-Modus mit --e2e")
        return 0

    evaluator = VisionEvaluator(
        matrix_dir=Path(args.matrix_dir),
        cluster=args.cluster,
        image_name=args.image,
        openai_api_key=args.openai_api_key,
        gemini_api_key=args.gemini_api_key,
        providers=[item.strip() for item in str(args.providers or "").split(",") if item.strip()],
        raw_mode=bool(args.raw or args.live_mode),
        live_mode=bool(args.live_mode),
    )
    evaluator.kpi_gate = bool(args.kpi_gate)
    evaluator.max_contradiction_rate = float(args.max_contradiction_rate)
    evaluator.min_source_map_coverage = float(args.min_source_map_coverage)
    evaluator.min_slot_source_coverage = float(args.min_slot_source_coverage)
    evaluator.min_semantic_validation_rate = float(args.min_semantic_validation_rate)
    evaluator.source_required_slots = DEFAULT_SOURCE_REQUIRED_SLOTS
    with get_db_context() as db:
        return await evaluator.run_e2e(db=db, image_range=args.range)


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
