import logging
import html
import json
import os
import platform
import re
import shutil
import subprocess
import tempfile
import threading
import time
from datetime import datetime
from urllib.parse import urlparse
from typing import Any, Dict, List, Optional

import requests
from backend.utils.config_loader import DEFAULT_OLLAMA_BASE_URL, DEFAULT_OLLAMA_NODE, load_config_data, save_config_data

logger = logging.getLogger("janus_backend")


class OllamaManager:
    OLLAMA_BASE_URL = DEFAULT_OLLAMA_BASE_URL
    OLLAMA_INSTALL_URL = "https://ollama.com/download"
    OLLAMA_REGISTRY_BASE_URL = "https://registry.ollama.ai/v2"
    OLLAMA_GITHUB_RELEASES_URL = "https://api.github.com/repos/ollama/ollama/releases/latest"
    OLLAMA_SEARCH_URL = "https://ollama.com/search?sort=newest"

    _MODEL_MATRIX = {
        "low": [
            {
                "name": "Phi-3 Mini",
                "id": "phi3:mini",
                "size_gb": 2.3,
                "description": "Schnelles, ressourcenschonendes Modell fuer lokale Assistant-Tasks.",
                "use_case": "Fast, alltagstauglich auf schwacher Hardware",
                "tools_supported": False,
            },
            {
                "name": "TinyLlama",
                "id": "tinyllama:latest",
                "size_gb": 0.6,
                "description": "Ultraleichtes Modell fuer einfache Prompts und schnelle Tests.",
                "use_case": "Ultra-Light, minimale RAM-Last",
                "tools_supported": False,
            },
        ],
        "mid": [
            {
                "name": "Llama 3.1 (8B)",
                "id": "llama3.1:8b",
                "size_gb": 4.7,
                "description": "Moderner Allrounder mit starker Chat-Qualitaet und solidem Tool-Calling.",
                "use_case": "Bester Allrounder fuer Assistenz, Skills und Workflow-Aufgaben",
                "tools_supported": True,
            },
            {
                "name": "Mistral",
                "id": "mistral:v0.3",
                "size_gb": 4.1,
                "description": "Starkes Reasoning fuer strukturiertes Denken und Praezision.",
                "use_case": "Reasoning und analytische Aufgaben",
                "tools_supported": True,
            },
        ],
        "high": [
            {
                "name": "Mistral Nemo (12B)",
                "id": "mistral-nemo:12b",
                "size_gb": 7.1,
                "description": "Reasoning-starker Allrounder fuer Agentic-Aufgaben und stabile Tool-Ketten.",
                "use_case": "Empfohlen fuer mehrstufige Agent-Workflows",
                "tools_supported": True,
                "reasoning_capability": "high",
            },
            {
                "name": "Qwen 2.5 (14B)",
                "id": "qwen2.5:14b",
                "size_gb": 8.2,
                "description": "Sehr starkes Tool-Parsing und robustes strukturiertes Reasoning.",
                "use_case": "Exzellent fuer Tool-Calling und Parsing-intensitive Aufgaben",
                "tools_supported": True,
                "reasoning_capability": "high",
            },
            {
                "name": "Gemma 2 (27B)",
                "id": "gemma2:27b",
                "size_gb": 16.0,
                "description": "High-End Reasoning fuer komplexe Agentic Chains auf starker Hardware.",
                "use_case": "Maximale Denkstaerke bei ausreichend RAM/VRAM",
                "tools_supported": True,
                "reasoning_capability": "high",
            },
            {
                "name": "Llama 3.1 (8B)",
                "id": "llama3.1:8b",
                "size_gb": 4.7,
                "description": "Moderner Allrounder mit starker Qualitaet und zuverlaessigem Tool-Support.",
                "use_case": "Allrounder fuer Chat, Automatisierung und Janus-Skills",
                "tools_supported": True,
            },
            {
                "name": "DeepSeek Coder (Vibecoding)",
                "id": "deepseek-coder:6.7b",
                "size_gb": 4.0,
                "description": "Hocheffizientes Modell fuer Software-Entwicklung, Logik und Janus-Erweiterungen.",
                "use_case": "Perfekt fuer Vibecoding und technische Architektur-Aufgaben.",
                "tools_supported": True,
            },
            {
                "name": "Mistral (v0.3)",
                "id": "mistral:v0.3",
                "size_gb": 4.1,
                "description": "Praezises Modell fuer analytische Aufgaben und strukturierte Denkarbeit.",
                "use_case": "Analytik, Problemzerlegung und reasoning-lastige Aufgaben",
                "tools_supported": True,
            },
        ],
    }

    _TOOL_READY_BASE_MODELS = {
        "llama3.1",
        "mistral",
        "deepseek-coder",
        "mistral-nemo",
        "qwen2.5",
        "gemma2",
    }

    _CODING_MODEL_MATRIX = {
        "low": [
            {
                "name": "Qwen 2.5 Coder (3B)",
                "id": "qwen2.5-coder:3b",
                "size_gb": 2.0,
                "description": "Leichtes Coding-Modell fuer kleine Codeaenderungen, Snippets und schnelle lokale Iterationen.",
                "use_case": "Vibecoding auf schwacher Hardware",
                "tools_supported": True,
                "source": "janus_coding_profile",
                "category": "coding",
            },
            {
                "name": "CodeGemma (2B)",
                "id": "codegemma:2b",
                "size_gb": 1.4,
                "description": "Sehr kleines Coding-Modell fuer kompakte technische Aufgaben und schnelle Codevorschlaege.",
                "use_case": "Ultra-Light Coding und lokale Tests",
                "tools_supported": False,
                "source": "janus_coding_profile",
                "category": "coding",
            },
        ],
        "mid": [
            {
                "name": "Qwen 2.5 Coder (7B)",
                "id": "qwen2.5-coder:7b",
                "size_gb": 4.7,
                "description": "Coding-starker Allrounder fuer lokale Entwicklung, Refactoring und agentische Codeaufgaben.",
                "use_case": "Vibecoding, Refactoring und technische Analyse",
                "tools_supported": True,
                "source": "janus_coding_profile",
                "category": "coding",
            },
            {
                "name": "DeepSeek Coder (6.7B)",
                "id": "deepseek-coder:6.7b",
                "size_gb": 4.0,
                "description": "Effizientes Coding-Modell fuer Softwareentwicklung, Logik und Janus-Erweiterungen.",
                "use_case": "Technische Umsetzung und Code-Navigation",
                "tools_supported": True,
                "source": "janus_coding_profile",
                "category": "coding",
            },
        ],
        "high": [
            {
                "name": "Qwen 2.5 Coder (14B)",
                "id": "qwen2.5-coder:14b",
                "size_gb": 8.2,
                "description": "Staerkeres Coding-Modell fuer groessere Refactorings, Architekturfragen und mehrschrittige Codearbeit.",
                "use_case": "Vibecoding mit hoeherer Codequalitaet",
                "tools_supported": True,
                "source": "janus_coding_profile",
                "category": "coding",
            },
            {
                "name": "DeepSeek Coder (6.7B)",
                "id": "deepseek-coder:6.7b",
                "size_gb": 4.0,
                "description": "Effizientes Coding-Modell fuer Softwareentwicklung, Logik und Janus-Erweiterungen.",
                "use_case": "Technische Umsetzung und Code-Navigation",
                "tools_supported": True,
                "source": "janus_coding_profile",
                "category": "coding",
            },
        ],
    }

    def __init__(self) -> None:
        self.active_downloads: Dict[str, Dict[str, Any]] = {}
        self._download_lock = threading.Lock()
        self._status_write_lock = threading.Lock()
        self._update_lock = threading.Lock()
        self.model_update_cache: Dict[str, Dict[str, Any]] = {}
        self.binary_update_cache: Dict[str, Any] = {
            "current_version": None,
            "latest_version": None,
            "update_available": False,
            "last_checked": None,
            "error": None,
        }

    def check_ollama(self) -> Dict[str, bool]:
        running = self._is_ollama_running()
        installed = self._is_ollama_cli_available() or running
        return {"installed": installed, "running": running}

    def get_config(self) -> Dict[str, str]:
        return {"ollama_base_url": self._get_ollama_base_url()}

    def update_config(self, ollama_base_url: str) -> Dict[str, str]:
        normalized = self._normalize_ollama_base_url(ollama_base_url)
        if not normalized:
            raise ValueError("ollama_base_url is required")

        config = load_config_data()
        nodes = self._load_nodes(config)
        active_node = next((node for node in nodes if bool(node.get("active"))), nodes[0])
        active_node["url"] = normalized
        self._save_nodes_config(config, nodes)
        return {"ollama_base_url": normalized}

    def get_nodes(self) -> Dict[str, Any]:
        config = load_config_data()
        nodes = self._load_nodes(config)
        enriched_nodes = [
            {
                "id": str(node.get("id") or ""),
                "name": str(node.get("name") or ""),
                "url": str(node.get("url") or ""),
                "active": bool(node.get("active")),
                "reachable": self._is_node_reachable(str(node.get("url") or "")),
            }
            for node in nodes
        ]
        active_node = next((node for node in enriched_nodes if bool(node.get("active"))), enriched_nodes[0])
        return {
            "nodes": enriched_nodes,
            "active_node_id": str(active_node.get("id") or ""),
            "ollama_base_url": str(active_node.get("url") or self.OLLAMA_BASE_URL),
        }

    def add_node(self, name: str, url: str) -> Dict[str, Any]:
        node_name = str(name or "").strip()
        normalized_url = self._normalize_ollama_base_url(url)
        if not node_name:
            raise ValueError("name is required")
        if not normalized_url:
            raise ValueError("url is required")

        config = load_config_data()
        nodes = self._load_nodes(config)
        for existing in nodes:
            if str(existing.get("url") or "") == normalized_url:
                existing_id = str(existing.get("id") or "")
                existing_name = str(existing.get("name") or "").strip()
                if existing_name != node_name:
                    existing["name"] = node_name
                    self._save_nodes_config(config, nodes)
                    return {
                        "status": "updated",
                        "node": {
                            "id": existing_id,
                            "name": node_name,
                            "url": normalized_url,
                            "active": bool(existing.get("active")),
                            "reachable": self._is_node_reachable(normalized_url),
                        },
                    }
                return {
                    "status": "exists",
                    "node": {
                        "id": existing_id,
                        "name": existing_name or node_name,
                        "url": normalized_url,
                        "active": bool(existing.get("active")),
                        "reachable": self._is_node_reachable(normalized_url),
                    },
                }

        node_id = self._build_node_id(node_name, nodes)
        nodes.append(
            {
                "id": node_id,
                "name": node_name,
                "url": normalized_url,
                "active": False,
            }
        )
        self._save_nodes_config(config, nodes)
        return {
            "status": "created",
            "node": {
                "id": node_id,
                "name": node_name,
                "url": normalized_url,
                "active": False,
                "reachable": self._is_node_reachable(normalized_url),
            },
        }

    def delete_node(self, node_id: str) -> Dict[str, Any]:
        target_id = str(node_id or "").strip()
        if not target_id:
            raise ValueError("node_id is required")

        config = load_config_data()
        nodes = self._load_nodes(config)
        target_node = next((node for node in nodes if str(node.get("id") or "") == target_id), None)
        if target_node is None:
            raise ValueError("Node not found")
        if self._is_localhost_node(target_node):
            raise ValueError("Default localhost node cannot be deleted")

        was_active = bool(target_node.get("active"))
        localhost_node = next((node for node in nodes if self._is_localhost_node(node)), None)

        remaining_nodes = [node for node in nodes if str(node.get("id") or "") != target_id]
        if was_active and localhost_node is not None:
            localhost_id = str(localhost_node.get("id") or "")
            for node in remaining_nodes:
                node["active"] = str(node.get("id") or "") == localhost_id
        elif not any(bool(node.get("active")) for node in remaining_nodes):
            fallback_localhost = next((node for node in remaining_nodes if self._is_localhost_node(node)), None)
            if fallback_localhost is not None:
                fallback_localhost["active"] = True
            else:
                remaining_nodes[0]["active"] = True

        self._save_nodes_config(config, remaining_nodes)
        active_node = next((node for node in remaining_nodes if bool(node.get("active"))), remaining_nodes[0])
        return {
            "status": "deleted",
            "deleted_node_id": target_id,
            "active_node_id": str(active_node.get("id") or ""),
            "ollama_base_url": str(active_node.get("url") or self.OLLAMA_BASE_URL),
        }

    def activate_node(self, node_id: str) -> Dict[str, Any]:
        target_id = str(node_id or "").strip()
        if not target_id:
            raise ValueError("node_id is required")

        config = load_config_data()
        nodes = self._load_nodes(config)
        target_exists = any(str(node.get("id") or "") == target_id for node in nodes)
        if not target_exists:
            raise ValueError("Node not found")

        for node in nodes:
            node["active"] = str(node.get("id") or "") == target_id

        self._save_nodes_config(config, nodes)
        active_node = next((node for node in nodes if bool(node.get("active"))), nodes[0])
        return {
            "status": "activated",
            "active_node_id": str(active_node.get("id") or ""),
            "ollama_base_url": str(active_node.get("url") or self.OLLAMA_BASE_URL),
            "reachable": self._is_node_reachable(str(active_node.get("url") or "")),
        }

    def analyze_system(self) -> Dict[str, Any]:
        ram_gb = self._get_total_ram_gb()
        cpu_cores = os.cpu_count() or 1
        gpu_info = self._detect_gpu()
        profile = self._resolve_profile(ram_gb)
        config = load_config_data()
        nodes = self._load_nodes(config)
        active_node = next((node for node in nodes if bool(node.get("active"))), nodes[0])

        recommendations = self._get_ranked_recommendations(
            profile=profile,
            active_node=active_node,
            gpu_info=gpu_info,
        )
        return {
            "hardware": {
                "ram_gb": ram_gb,
                "cpu_cores": cpu_cores,
                "gpu": gpu_info,
                "platform": platform.platform(),
            },
            "profile": profile,
            "recommended_models": recommendations,
            "reasoning_first": self._is_reasoning_priority_node(active_node, gpu_info),
            "active_node": {
                "id": str(active_node.get("id") or ""),
                "name": str(active_node.get("name") or ""),
                "url": str(active_node.get("url") or ""),
            },
            "ollama_install_url": self.OLLAMA_INSTALL_URL,
        }

    def _get_ranked_recommendations(
        self,
        *,
        profile: str,
        active_node: Dict[str, Any],
        gpu_info: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        reasoning_priority = self._is_reasoning_priority_node(active_node, gpu_info)
        live_recommendations = self._get_live_library_recommendations(
            profile=profile,
            reasoning_priority=reasoning_priority,
        )
        if live_recommendations:
            return live_recommendations

        source_profile = "high" if reasoning_priority else profile
        base = list(self._MODEL_MATRIX.get(source_profile, self._MODEL_MATRIX["mid"]))
        if not reasoning_priority:
            return base

        def _rank(model: Dict[str, Any]) -> tuple[int, int, float]:
            model_id = str(model.get("id") or "").lower()
            size_gb = float(model.get("size_gb") or 0.0)
            reasoning_high = 1 if str(model.get("reasoning_capability") or "").lower() == "high" else 0
            strong_size = 1 if size_gb >= 7.0 else 0
            penalty_small_allrounder = -1 if model_id.startswith("llama3.1:8b") else 0
            return (reasoning_high, strong_size, size_gb + penalty_small_allrounder)

        return sorted(base, key=_rank, reverse=True)

    def _get_live_library_recommendations(self, *, profile: str, reasoning_priority: bool) -> List[Dict[str, Any]]:
        library_models = self._fetch_ollama_library_models()
        if not library_models:
            return []

        max_params = self._max_recommended_params_b(profile, reasoning_priority)
        recommendations: List[Dict[str, Any]] = []
        seen_ids: set[str] = set()

        for model in library_models:
            model_name = str(model.get("name") or "").strip()
            if not model_name:
                continue
            sizes_b = [size for size in model.get("sizes_b", []) if isinstance(size, (int, float))]
            eligible_sizes = [size for size in sizes_b if size <= max_params]
            if sizes_b and not eligible_sizes:
                continue

            selected_size = max(eligible_sizes) if eligible_sizes else None
            model_id = f"{model_name}:{self._format_size_tag(selected_size)}" if selected_size else model_name
            if model_id in seen_ids:
                continue
            seen_ids.add(model_id)

            capabilities = {str(capability).lower() for capability in model.get("capabilities", [])}
            tools_supported = "tools" in capabilities or "tool" in capabilities
            thinking = "thinking" in capabilities
            if reasoning_priority and not (tools_supported or thinking):
                continue

            recommendations.append(
                {
                    "name": self._humanize_ollama_model_name(model_name),
                    "id": model_id,
                    "size_gb": self._estimate_model_size_gb(selected_size),
                    "description": self._build_live_model_description(model_name, capabilities, selected_size),
                    "use_case": self._build_live_model_use_case(capabilities, selected_size),
                    "tools_supported": tools_supported,
                    "reasoning_capability": "high" if thinking else "standard",
                    "source": "ollama_library",
                }
            )
            if len(recommendations) >= 6:
                break

        recommendations.extend(
            self._get_coding_recommendations(
                profile=profile,
                reasoning_priority=reasoning_priority,
                seen_ids=seen_ids,
            )
        )
        return recommendations

    def _get_coding_recommendations(
        self,
        *,
        profile: str,
        reasoning_priority: bool,
        seen_ids: set[str],
    ) -> List[Dict[str, Any]]:
        source_profile = "high" if reasoning_priority else profile
        candidates = self._CODING_MODEL_MATRIX.get(source_profile, self._CODING_MODEL_MATRIX["mid"])
        selected: List[Dict[str, Any]] = []
        for candidate in candidates:
            model_id = str(candidate.get("id") or "")
            if not model_id or model_id in seen_ids:
                continue
            seen_ids.add(model_id)
            selected.append(dict(candidate))
            if len(selected) >= 2:
                break
        return selected

    def _fetch_ollama_library_models(self) -> List[Dict[str, Any]]:
        try:
            response = requests.get(self.OLLAMA_SEARCH_URL, timeout=8)
            response.raise_for_status()
        except Exception as exc:
            logger.warning("Could not fetch latest Ollama library search results: %s", exc)
            return []

        html_text = response.text or ""
        blocks = re.findall(r'<li\b[^>]*x-test-model[^>]*>(.*?)</li>', html_text, flags=re.IGNORECASE | re.DOTALL)
        parsed: List[Dict[str, Any]] = []
        for block in blocks:
            title_match = re.search(
                r'<span\b[^>]*x-test-search-response-title[^>]*>(.*?)</span>',
                block,
                flags=re.IGNORECASE | re.DOTALL,
            )
            if not title_match:
                continue
            name = self._strip_html(title_match.group(1)).strip()
            if not name:
                continue

            desc_match = re.search(r'<p\b[^>]*text-neutral-800[^>]*>(.*?)</p>', block, flags=re.IGNORECASE | re.DOTALL)
            description = self._strip_html(desc_match.group(1)).strip() if desc_match else ""
            capabilities = [
                self._strip_html(match).strip().lower()
                for match in re.findall(
                    r'<span\b[^>]*x-test-capability[^>]*>(.*?)</span>',
                    block,
                    flags=re.IGNORECASE | re.DOTALL,
                )
            ]
            size_labels = [
                self._strip_html(match).strip().lower()
                for match in re.findall(
                    r'<span\b[^>]*x-test-size[^>]*>(.*?)</span>',
                    block,
                    flags=re.IGNORECASE | re.DOTALL,
                )
            ]
            sizes_b = [size for size in (self._parse_param_size_b(label) for label in size_labels) if size is not None]
            parsed.append(
                {
                    "name": name,
                    "description": description,
                    "capabilities": capabilities,
                    "sizes_b": sizes_b,
                }
            )

        return parsed

    @staticmethod
    def _strip_html(value: str) -> str:
        text = re.sub(r"<[^>]+>", " ", value or "")
        return re.sub(r"\s+", " ", html.unescape(text)).strip()

    @staticmethod
    def _parse_param_size_b(label: str) -> Optional[float]:
        match = re.search(r"(\d+(?:\.\d+)?)\s*b\b", str(label or "").lower())
        if not match:
            return None
        return float(match.group(1))

    @staticmethod
    def _max_recommended_params_b(profile: str, reasoning_priority: bool) -> float:
        if reasoning_priority:
            return 40.0
        return {
            "low": 4.0,
            "mid": 14.0,
            "high": 32.0,
        }.get(profile, 14.0)

    @staticmethod
    def _format_size_tag(size_b: Optional[float]) -> str:
        if size_b is None:
            return "latest"
        if float(size_b).is_integer():
            return f"{int(size_b)}b"
        return f"{size_b:g}b"

    @staticmethod
    def _estimate_model_size_gb(size_b: Optional[float]) -> float:
        if size_b is None:
            return 0.0
        return round(float(size_b) * 0.65, 1)

    @staticmethod
    def _humanize_ollama_model_name(model_id: str) -> str:
        return " ".join(part.upper() if len(part) <= 3 else part.capitalize() for part in re.split(r"[-_]+", model_id))

    @staticmethod
    def _build_live_model_description(model_name: str, capabilities: set[str], size_b: Optional[float]) -> str:
        capability_parts: List[str] = []
        if "tools" in capabilities:
            capability_parts.append("Tool-Calling")
        if "thinking" in capabilities:
            capability_parts.append("Reasoning")
        if "vision" in capabilities:
            capability_parts.append("Vision")

        capability_text = ", ".join(capability_parts) if capability_parts else "allgemeine lokale Assistenz"
        if size_b:
            return f"Aktuelles Ollama-Modell fuer {capability_text}, passend im {OllamaManager._format_size_tag(size_b).upper()}-Profil."
        return f"Aktuelles Ollama-Modell fuer {capability_text}."

    @staticmethod
    def _build_live_model_use_case(capabilities: set[str], size_b: Optional[float]) -> str:
        size_label = OllamaManager._format_size_tag(size_b).upper() if size_b else ""
        has_tools = "tools" in capabilities
        has_thinking = "thinking" in capabilities
        has_vision = "vision" in capabilities

        if has_tools and has_thinking and has_vision:
            return f"Janus Skills, mehrstufige Tool-Aufgaben und Bildanalyse{f' auf {size_label}-Hardware' if size_label else ''}"
        if has_tools and has_thinking:
            return f"Agentische Janus-Workflows, Planung und strukturierte Tool-Nutzung{f' im {size_label}-Profil' if size_label else ''}"
        if has_tools and has_vision:
            return f"Lokale Assistenz mit Tool-Nutzung und visueller Analyse{f' im {size_label}-Profil' if size_label else ''}"
        if has_tools:
            return f"Zuverlaessige Janus Skills, Tool-Aufrufe und lokale Automatisierung{f' im {size_label}-Profil' if size_label else ''}"
        if has_thinking:
            return f"Komplexe Fragen, Planung und analytische Aufgaben{f' im {size_label}-Profil' if size_label else ''}"
        if has_vision:
            return f"Lokale Bildanalyse und multimodale Aufgaben{f' im {size_label}-Profil' if size_label else ''}"
        return f"Alltaegliche lokale Chat- und Assistenzaufgaben{f' im {size_label}-Profil' if size_label else ''}"

    def _is_reasoning_priority_node(self, active_node: Dict[str, Any], gpu_info: Dict[str, Any]) -> bool:
        if self._is_rolf_node(active_node):
            return True
        gpu_type = str((gpu_info or {}).get("type") or "none").lower()
        vram_gb = float((gpu_info or {}).get("vram_gb") or 0.0)
        return gpu_type not in {"none", ""} and vram_gb >= 8.0

    @staticmethod
    def _is_rolf_node(active_node: Dict[str, Any]) -> bool:
        node_id = str(active_node.get("id") or "").lower()
        node_name = str(active_node.get("name") or "").lower()
        node_url = str(active_node.get("url") or "").strip()
        parsed_host = str(urlparse(node_url).hostname or "").lower() if node_url else ""
        return any("rolf" in value for value in (node_id, node_name, parsed_host) if value)

    def list_models(self) -> List[Dict[str, Any]]:
        if not self._is_ollama_running():
            return []

        try:
            config = load_config_data()
            nodes = self._load_nodes(config)
            active_node = next((node for node in nodes if bool(node.get("active"))), nodes[0])
            models = self._fetch_node_tags(str(active_node.get("url") or ""))
        except Exception as exc:
            logger.warning("Could not fetch Ollama models: %s", exc)
            return []

        normalized: List[Dict[str, Any]] = []
        for item in models:
            model_id = str(item.get("name") or "").strip()
            if not model_id:
                continue

            size_bytes = item.get("size")
            size_gb: Optional[float] = None
            if isinstance(size_bytes, (int, float)) and size_bytes > 0:
                size_gb = round(float(size_bytes) / (1024**3), 2)

            normalized.append(
                {
                    "id": model_id,
                    "name": model_id,
                    "provider": "ollama",
                    "type": "text",
                    "size_gb": size_gb,
                    "desc": "Lokal installiertes Ollama-Modell",
                    "capabilities": ["chat", "local_inference"],
                    "tools_supported": self._supports_tools(model_id),
                    "update_available": bool(self.model_update_cache.get(model_id, {}).get("update_available", False)),
                }
            )

        return normalized

    def get_unified_model_list(self) -> List[Dict[str, Any]]:
        config = load_config_data()
        nodes = self._load_nodes(config)
        unified_models: List[Dict[str, Any]] = []
        seen_ids = set()

        for node in nodes:
            node_id = str(node.get("id") or "").strip()
            node_name = str(node.get("name") or node_id).strip() or node_id
            node_url = str(node.get("url") or "").strip()
            if not node_id or not node_url:
                continue
            if not self._is_node_reachable(node_url):
                logger.info("Unified-Model-List: Node '%s' (%s) nicht erreichbar.", node_name, node_url)
                continue

            try:
                node_models = self._fetch_node_tags(node_url)
            except Exception as exc:
                logger.info("Unified-Model-List: Node '%s' nicht erreichbar (%s)", node_name, exc)
                continue

            for item in node_models:
                base_model_id = str(item.get("name") or "").strip()
                if not base_model_id:
                    continue

                unified_model_id = f"{base_model_id}@{node_id}"
                if unified_model_id in seen_ids:
                    continue
                seen_ids.add(unified_model_id)

                size_bytes = item.get("size")
                size_gb: Optional[float] = None
                if isinstance(size_bytes, (int, float)) and size_bytes > 0:
                    size_gb = round(float(size_bytes) / (1024**3), 2)

                unified_models.append(
                    {
                        "id": unified_model_id,
                        "name": f"{base_model_id} ({node_name})",
                        "provider": "ollama",
                        "type": "text",
                        "size_gb": size_gb,
                        "desc": f"Ollama Node: {node_name}",
                        "capabilities": ["chat", "local_inference"],
                        "tools_supported": self._supports_tools(base_model_id),
                        "update_available": False,
                        "node_id": node_id,
                        "node_name": node_name,
                        "node_url": node_url,
                        "base_model_id": base_model_id,
                    }
                )

        unified_models.sort(
            key=lambda model: (
                str(model.get("node_name") or "").lower(),
                str(model.get("base_model_id") or model.get("id") or "").lower(),
            )
        )
        return unified_models

    def check_for_updates(self) -> Dict[str, Any]:
        if not self._is_ollama_running():
            snapshot = {
                "status": "skipped",
                "reason": "ollama_not_running",
                "checked_models": 0,
                "updates_available": 0,
                "last_checked": int(time.time()),
            }
            return snapshot

        installed_models = self.list_models()
        updates_available = 0
        checked_models = 0
        now = int(time.time())

        with self._update_lock:
            stale_keys = set(self.model_update_cache.keys())

        for model in installed_models:
            model_id = str(model.get("id") or "").strip()
            if not model_id:
                continue
            checked_models += 1

            local_digest = self._get_local_model_digest(model_id)
            remote_digest = self._get_remote_model_digest(model_id)
            update_available = bool(local_digest and remote_digest and local_digest != remote_digest)
            error_msg = None
            if remote_digest is None:
                error_msg = "remote_digest_unavailable"

            with self._update_lock:
                self.model_update_cache[model_id] = {
                    "model": model_id,
                    "local_digest": local_digest,
                    "remote_digest": remote_digest,
                    "update_available": update_available,
                    "last_checked": now,
                    "error": error_msg,
                }
                stale_keys.discard(model_id)

            if update_available:
                updates_available += 1

        if checked_models:
            with self._update_lock:
                for stale_key in stale_keys:
                    self.model_update_cache.pop(stale_key, None)

        return {
            "status": "ok",
            "checked_models": checked_models,
            "updates_available": updates_available,
            "last_checked": now,
        }

    def check_ollama_binary_update(self) -> Dict[str, Any]:
        now = int(time.time())
        current_version = self._get_local_ollama_version()
        latest_version = self._get_latest_ollama_version()
        update_available = self._is_version_newer(latest_version, current_version)

        payload = {
            "current_version": current_version,
            "latest_version": latest_version,
            "update_available": update_available,
            "last_checked": now,
            "error": None if current_version else "local_version_unavailable",
        }
        with self._update_lock:
            self.binary_update_cache = payload
        return payload

    def get_update_snapshot(self) -> Dict[str, Any]:
        with self._update_lock:
            return {
                "models": dict(self.model_update_cache),
                "binary": dict(self.binary_update_cache),
            }

    def queue_pull_model(self, model_id: str, *, node_id: Optional[str] = None) -> Dict[str, Any]:
        model_name = str(model_id or "").strip()
        if not model_name:
            raise ValueError("model_id is required")
        base_model, embedded_node = self._split_model_node_identifier(model_name)
        download_node = node_id or embedded_node
        download_key = self._build_download_key(base_model, download_node)

        with self._download_lock:
            current = self.active_downloads.get(download_key) or {}
            if current.get("status") in {"queued", "running"}:
                return {
                    "status": "already_running",
                    "message": f"Download fuer {download_key} laeuft bereits im Hintergrund.",
                    "model": download_key,
                }

            now = int(time.time())
            self.active_downloads[download_key] = {
                "status": "queued",
                "message": f"Download fuer {download_key} wurde gestartet.",
                "model": download_key,
                "progress": 5,
                "started_at": now,
                "updated_at": now,
                "error": None,
            }

        return {
            "status": "started",
            "message": "Download laeuft im Hintergrund",
            "model": download_key,
        }

    def pull_model(self, model_id: str, *, node_id: Optional[str] = None) -> Dict[str, Any]:
        model_name = str(model_id or "").strip()
        if not model_name:
            raise ValueError("model_id is required")

        base_model, embedded_node = self._split_model_node_identifier(model_name)
        target_node_id = node_id or embedded_node
        download_key = self._build_download_key(base_model, target_node_id)

        self._set_download_status(
            download_key,
            status="running",
            message=f"Ollama laedt {download_key} herunter...",
            progress=35,
        )

        payload: Dict[str, Any] = {}
        try:
            target_base_url = self._resolve_node_base_url(target_node_id)
            response = requests.post(
                f"{target_base_url}/api/pull",
                json={"name": base_model, "stream": False},
                timeout=None,
            )
            response.raise_for_status()

            payload = response.json() if response.content else {}
            final_status = str(payload.get("status") or "completed").lower()
            if final_status not in {"success", "completed", "done"}:
                final_status = "completed"

            self._set_download_status(
                download_key,
                status="completed",
                message=f"Modell {download_key} ist installiert.",
                progress=100,
                raw=payload,
            )
            return {"status": final_status, "model": download_key, "raw": payload}
        except Exception as exc:
            self._set_download_status(
                download_key,
                status="failed",
                message=f"Download fehlgeschlagen: {exc}",
                progress=100,
                error=str(exc),
            )
            raise

    def get_pull_status(self, model_id: str) -> Dict[str, Any]:
        model_name = str(model_id or "").strip()
        if not model_name:
            raise ValueError("model_id is required")

        base_model, embedded_node = self._split_model_node_identifier(model_id)
        target_node_id = embedded_node
        download_key = self._build_download_key(base_model, target_node_id)

        with self._download_lock:
            exact_status = self.active_downloads.get(model_name)
            if exact_status:
                return dict(exact_status)
            parsed_base, parsed_node = self._derive_base_model_and_node_from_download_key(model_name)
            if base_model == model_name and parsed_base:
                base_model = parsed_base
            if target_node_id is None:
                target_node_id = parsed_node

            if download_key in self.active_downloads:
                return dict(self.active_downloads[download_key])
            fallback_key = self._find_latest_download_key_unlocked(base_model, target_node_id)
            if fallback_key:
                return dict(self.active_downloads[fallback_key])

        installed_ids = {str(model.get("id") or "").strip() for model in self.list_models()}
        if model_name in installed_ids:
            return {
                "status": "completed",
                "message": f"Modell {model_name} ist installiert.",
                "model": model_name,
                "progress": 100,
                "error": None,
            }

        return {
            "status": "idle",
            "message": "Kein aktiver Download fuer dieses Modell.",
            "model": model_name,
            "progress": 0,
            "error": None,
        }

    def delete_model(self, model_id: str) -> Dict[str, Any]:
        model_name = str(model_id or "").strip()
        if not model_name:
            raise ValueError("model_id is required")

        base_model_name, model_node_id = self._split_model_node_identifier(model_name)
        target_base_url = self._get_ollama_base_url()
        if model_node_id:
            node_url = self._get_node_url_by_id(model_node_id)
            if node_url:
                target_base_url = node_url
            else:
                logger.warning(
                    "Delete-Model: Node '%s' aus Model-ID '%s' nicht gefunden. Verwende aktiven Node.",
                    model_node_id,
                    model_name,
                )

        try:
            response = requests.delete(
                f"{target_base_url}/api/delete",
                json={"name": base_model_name},
                timeout=20,
            )
            response.raise_for_status()
        except requests.HTTPError as exc:
            detail = exc.response.text if exc.response is not None else str(exc)
            raise RuntimeError(f"Loeschen fehlgeschlagen: {detail}") from exc
        except Exception as exc:
            raise RuntimeError(f"Loeschen fehlgeschlagen: {exc}") from exc

        self._remove_model_from_caches(base_model_name)
        return {
            "status": "deleted",
            "model": model_name,
            "message": f"Modell {model_name} wurde geloescht.",
        }

    def _set_download_status(
        self,
        model_name: str,
        *,
        status: str,
        message: str,
        progress: int,
        error: Optional[str] = None,
        raw: Optional[Dict[str, Any]] = None,
    ) -> None:
        now = int(time.time())
        with self._status_write_lock:
            with self._download_lock:
                existing = self.active_downloads.get(model_name) or {
                    "model": model_name,
                    "started_at": now,
                }
                existing.update(
                    {
                        "status": status,
                        "message": message,
                        "progress": max(0, min(100, int(progress))),
                        "updated_at": now,
                        "error": error,
                    }
                )
                if raw is not None:
                    existing["raw"] = raw
                self.active_downloads[model_name] = existing

    def _find_latest_download_key_unlocked(self, base_model: str, node_id: Optional[str]) -> Optional[str]:
        normalized_model = str(base_model or "").strip().lower()
        normalized_node = str(node_id or "active").strip().lower() or "active"
        best_key: Optional[str] = None
        best_updated_at = -1

        for key, payload in self.active_downloads.items():
            parts = str(key or "").split(":")
            if len(parts) < 3:
                continue
            key_date = parts[-1]
            key_node = parts[-2].strip().lower()
            key_model = ":".join(parts[:-2]).strip().lower()
            if key_model != normalized_model:
                continue
            if key_node != normalized_node:
                continue
            if len(key_date) != 8 or not key_date.isdigit():
                continue

            updated_at = int((payload or {}).get("updated_at") or 0)
            if updated_at >= best_updated_at:
                best_updated_at = updated_at
                best_key = key

        return best_key

    @classmethod
    def _supports_tools(cls, model_id: str) -> bool:
        normalized = str(model_id or "").strip().lower()
        if not normalized:
            return False
        base = normalized.split(":", 1)[0]
        return base in cls._TOOL_READY_BASE_MODELS

    def _remove_model_from_caches(self, model_id: str) -> None:
        normalized = str(model_id or "").strip().lower()
        base = normalized.split(":", 1)[0] if normalized else ""

        with self._download_lock:
            self.active_downloads.pop(model_id, None)
            self.active_downloads.pop(normalized, None)

        with self._update_lock:
            keys_to_remove = []
            for key in self.model_update_cache.keys():
                key_norm = str(key or "").strip().lower()
                key_base = key_norm.split(":", 1)[0] if key_norm else ""
                if key_norm == normalized or (base and key_base == base):
                    keys_to_remove.append(key)
            for key in keys_to_remove:
                self.model_update_cache.pop(key, None)

    def _get_local_model_digest(self, model_id: str) -> Optional[str]:
        normalized = str(model_id or "").strip()
        if not normalized:
            return None
        try:
            response = requests.post(
                f"{self._get_ollama_base_url()}/api/show",
                json={"name": normalized},
                timeout=6,
            )
            response.raise_for_status()
            payload = response.json() if response.content else {}
            digest = payload.get("digest")
            if digest:
                return str(digest)
            details = payload.get("details") or {}
            if isinstance(details, dict):
                digest = details.get("digest")
                if digest:
                    return str(digest)
        except Exception:
            return None
        return None

    def _get_remote_model_digest(self, model_id: str) -> Optional[str]:
        manifest_url = self._build_registry_manifest_url(model_id)
        if not manifest_url:
            return None
        try:
            response = requests.get(
                manifest_url,
                headers={
                    "Accept": (
                        "application/vnd.docker.distribution.manifest.v2+json,"
                        "application/vnd.oci.image.manifest.v1+json"
                    )
                },
                timeout=8,
            )
            if response.status_code >= 400:
                return None
            docker_digest = response.headers.get("Docker-Content-Digest")
            if docker_digest:
                return str(docker_digest)
            payload = response.json() if response.content else {}
            config = payload.get("config") if isinstance(payload, dict) else None
            if isinstance(config, dict) and config.get("digest"):
                return str(config.get("digest"))
        except Exception:
            return None
        return None

    def _build_registry_manifest_url(self, model_id: str) -> Optional[str]:
        normalized = str(model_id or "").strip().lower()
        if not normalized:
            return None
        repository_part, tag = self._split_model_id(normalized)
        if not repository_part:
            return None
        if "/" not in repository_part:
            repository_part = f"library/{repository_part}"
        return f"{self.OLLAMA_REGISTRY_BASE_URL}/{repository_part}/manifests/{tag}"

    @staticmethod
    def _split_model_id(model_id: str) -> tuple[str, str]:
        normalized = str(model_id or "").strip().lower()
        if not normalized:
            return "", "latest"
        if ":" in normalized:
            repository, tag = normalized.rsplit(":", 1)
            return repository, tag or "latest"
        return normalized, "latest"

    def _get_local_ollama_version(self) -> Optional[str]:
        try:
            response = requests.get(f"{self._get_ollama_base_url()}/api/version", timeout=4)
            response.raise_for_status()
            payload = response.json() if response.content else {}
            version = payload.get("version")
            if version:
                return str(version)
        except Exception:
            return None
        return None

    def _get_latest_ollama_version(self) -> Optional[str]:
        try:
            response = requests.get(self.OLLAMA_GITHUB_RELEASES_URL, timeout=5)
            response.raise_for_status()
            payload = response.json() if response.content else {}
            tag_name = payload.get("tag_name")
            if tag_name:
                return str(tag_name).lstrip("v")
        except Exception:
            return None
        return None

    @staticmethod
    def _is_version_newer(latest_version: Optional[str], current_version: Optional[str]) -> bool:
        if not latest_version or not current_version:
            return False
        latest_parts = OllamaManager._parse_version_parts(latest_version)
        current_parts = OllamaManager._parse_version_parts(current_version)
        if not latest_parts or not current_parts:
            return False
        return latest_parts > current_parts

    @staticmethod
    def _parse_version_parts(version: str) -> tuple[int, ...]:
        if not version:
            return tuple()
        cleaned = str(version).strip().lower().lstrip("v")
        numbers = [int(part) for part in re.findall(r"\d+", cleaned)]
        return tuple(numbers)

    def _is_ollama_running(self) -> bool:
        try:
            response = requests.get(f"{self._get_ollama_base_url()}/api/version", timeout=2)
            return response.ok
        except Exception:
            return False

    def _get_ollama_base_url(self) -> str:
        config = load_config_data()
        nodes = self._load_nodes(config)
        active_node = next((node for node in nodes if bool(node.get("active"))), nodes[0])
        normalized = self._normalize_ollama_base_url(active_node.get("url"))
        return normalized or self.OLLAMA_BASE_URL

    def _get_node_url_by_id(self, node_id: str) -> Optional[str]:
        target_id = str(node_id or "").strip()
        if not target_id:
            return None
        config = load_config_data()
        nodes = self._load_nodes(config)
        for node in nodes:
            if str(node.get("id") or "") == target_id:
                normalized = self._normalize_ollama_base_url(node.get("url"))
                if normalized:
                    return normalized
        return None

    def _resolve_node_base_url(self, node_id: Optional[str]) -> str:
        target_id = str(node_id or "").strip()
        if target_id:
            node_url = self._get_node_url_by_id(target_id)
            if node_url:
                return node_url
            logger.warning("Pull-Model: Node '%s' nicht gefunden. Verwende aktiven Node.", target_id)
        return self._get_ollama_base_url()

    def _fetch_node_tags(self, base_url: str) -> List[Dict[str, Any]]:
        normalized_url = self._normalize_ollama_base_url(base_url)
        if not normalized_url:
            return []
        response = requests.get(f"{normalized_url}/api/tags", timeout=5)
        response.raise_for_status()
        payload = response.json() if response.content else {}
        models = payload.get("models")
        return models if isinstance(models, list) else []

    @staticmethod
    def _split_model_node_identifier(model_id: str) -> tuple[str, Optional[str]]:
        raw = str(model_id or "").strip()
        if not raw:
            return "", None
        if "@" not in raw:
            return raw, None
        base_model, node_id = raw.rsplit("@", 1)
        cleaned_model = str(base_model or "").strip() or raw
        cleaned_node_id = str(node_id or "").strip() or None
        return cleaned_model, cleaned_node_id

    @staticmethod
    def _derive_base_model_and_node_from_download_key(value: str) -> tuple[str, Optional[str]]:
        raw = str(value or "").strip()
        if not raw:
            return "", None
        parts = raw.split(":")
        if len(parts) < 3:
            return raw, None
        candidate_date = parts[-1]
        if len(candidate_date) == 8 and candidate_date.isdigit():
            node_part = parts[-2].strip()
            base_part = ":".join(parts[:-2]).strip()
            node_id = node_part if node_part else None
            return base_part or raw, node_id
        return raw, None

    def _build_download_key(self, model_name: str, node_id: Optional[str]) -> str:
        clean_model = str(model_name or "").strip()
        clean_node = str(node_id or "active").strip() or "active"
        return f"{clean_model}:{clean_node}:{datetime.now().strftime('%Y%m%d')}"

    @classmethod
    def _load_nodes(cls, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        nodes_raw = config.get("ollama_nodes") if isinstance(config, dict) else None
        nodes: List[Dict[str, Any]] = []
        if isinstance(nodes_raw, list):
            for node in nodes_raw:
                if not isinstance(node, dict):
                    continue
                node_url = cls._normalize_ollama_base_url(node.get("url"))
                if not node_url:
                    continue
                nodes.append(
                    {
                        "id": str(node.get("id") or "").strip() or f"node_{len(nodes) + 1}",
                        "name": str(node.get("name") or "").strip() or "Node",
                        "url": node_url,
                        "active": bool(node.get("active")),
                    }
                )

        if not nodes:
            nodes = [dict(DEFAULT_OLLAMA_NODE)]
        localhost_id = str(DEFAULT_OLLAMA_NODE.get("id") or "localhost")
        if not any(str(node.get("id") or "") == localhost_id for node in nodes):
            nodes.insert(0, dict(DEFAULT_OLLAMA_NODE))
        if not any(bool(node.get("active")) for node in nodes):
            nodes[0]["active"] = True
        first_active_id = next((str(node.get("id") or "") for node in nodes if bool(node.get("active"))), str(nodes[0].get("id") or ""))
        for node in nodes:
            node["active"] = str(node.get("id") or "") == first_active_id
        return nodes

    @classmethod
    def _is_localhost_node(cls, node: Dict[str, Any]) -> bool:
        node_id = str(node.get("id") or "").strip().lower()
        node_url = cls._normalize_ollama_base_url(node.get("url"))
        return node_id == str(DEFAULT_OLLAMA_NODE.get("id") or "localhost") or node_url == DEFAULT_OLLAMA_BASE_URL

    @classmethod
    def _save_nodes_config(cls, config: Dict[str, Any], nodes: List[Dict[str, Any]]) -> None:
        normalized_nodes = cls._load_nodes({"ollama_nodes": nodes})
        active_node = next((node for node in normalized_nodes if bool(node.get("active"))), normalized_nodes[0])
        config["ollama_nodes"] = normalized_nodes
        config["ollama_base_url"] = str(active_node.get("url") or cls.OLLAMA_BASE_URL)
        save_config_data(config)

    @staticmethod
    def _build_node_id(name: str, existing_nodes: List[Dict[str, Any]]) -> str:
        base = re.sub(r"[^a-z0-9]+", "-", str(name or "").strip().lower()).strip("-") or "ollama-node"
        existing_ids = {str(node.get("id") or "") for node in existing_nodes}
        candidate = base
        counter = 2
        while candidate in existing_ids:
            candidate = f"{base}-{counter}"
            counter += 1
        return candidate

    @staticmethod
    def _is_node_reachable(base_url: str) -> bool:
        normalized = OllamaManager._normalize_ollama_base_url(base_url)
        if not normalized:
            return False
        try:
            response = requests.get(f"{normalized}/api/version", timeout=2)
            return bool(response.ok)
        except Exception:
            return False

    @staticmethod
    def _normalize_ollama_base_url(value: Any) -> Optional[str]:
        raw = str(value or "").strip()
        if not raw:
            return None
        if not raw.startswith("http://") and not raw.startswith("https://"):
            raw = f"http://{raw}"
        return raw.rstrip("/")

    @staticmethod
    def _is_ollama_cli_available() -> bool:
        return shutil.which("ollama") is not None

    @staticmethod
    def _get_total_ram_gb() -> float:
        if platform.system().lower() == "windows":
            wmic_ram = OllamaManager._get_windows_total_ram_gb_wmic()
            psutil_ram = OllamaManager._get_psutil_total_ram_gb()
            if wmic_ram is not None and psutil_ram is not None:
                # In VMs kann psutil unterreporten, daher den groesseren plausiblen Wert nutzen.
                return round(max(wmic_ram, psutil_ram), 1)
            if wmic_ram is not None:
                return round(wmic_ram, 1)
            if psutil_ram is not None:
                return round(psutil_ram, 1)

        psutil_ram = OllamaManager._get_psutil_total_ram_gb()
        if psutil_ram is not None:
            return round(psutil_ram, 1)

        unix_ram = OllamaManager._get_unix_total_ram_gb()
        if unix_ram is not None:
            return round(unix_ram, 1)

        return 8.0

    @staticmethod
    def _get_psutil_total_ram_gb() -> Optional[float]:
        try:
            import psutil

            return float(psutil.virtual_memory().total) / (1024**3)
        except Exception:
            return None

    @staticmethod
    def _get_unix_total_ram_gb() -> Optional[float]:
        if not hasattr(os, "sysconf"):
            return None
        if "SC_PAGE_SIZE" not in os.sysconf_names or "SC_PHYS_PAGES" not in os.sysconf_names:
            return None

        try:
            page_size = os.sysconf("SC_PAGE_SIZE")
            pages = os.sysconf("SC_PHYS_PAGES")
            return float(page_size * pages) / (1024**3)
        except Exception:
            return None

    @staticmethod
    def _get_windows_total_ram_gb_wmic() -> Optional[float]:
        try:
            result = subprocess.run(
                ["wmic", "computersystem", "get", "totalphysicalmemory", "/value"],
                capture_output=True,
                text=True,
                timeout=4,
                check=True,
            )
            for raw_line in (result.stdout or "").splitlines():
                line = raw_line.strip()
                if not line.lower().startswith("totalphysicalmemory"):
                    continue
                _, raw_value = line.split("=", 1)
                value = raw_value.strip()
                if value.isdigit():
                    return float(int(value)) / (1024**3)
        except Exception:
            return None
        return None

    @staticmethod
    def _resolve_profile(ram_gb: float) -> str:
        if ram_gb < 8:
            return "low"
        if ram_gb <= 16:
            return "mid"
        return "high"

    def _detect_gpu(self) -> Dict[str, Any]:
        nvidia = self._detect_nvidia_gpu()
        if nvidia:
            return nvidia

        apple = self._detect_apple_silicon()
        if apple:
            return apple

        generic = self._detect_generic_gpu()
        if generic:
            return generic

        return {
            "type": "none",
            "name": "Keine dedizierte GPU erkannt",
            "vram_gb": None,
            "detection_source": "none",
            "vram_source": "none",
            "vram_confidence": "none",
        }

    @staticmethod
    def _detect_nvidia_gpu() -> Optional[Dict[str, Any]]:
        nvidia_smi = shutil.which("nvidia-smi")
        if not nvidia_smi:
            return None

        try:
            result = subprocess.run(
                [
                    nvidia_smi,
                    "--query-gpu=name,memory.total",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=3,
                check=True,
            )
            first_line = (result.stdout or "").splitlines()[0]
            name, memory_mb = [part.strip() for part in first_line.split(",", maxsplit=1)]
            memory_gb = round(float(memory_mb) / 1024.0, 1)
            return {
                "type": "nvidia",
                "name": name,
                "vram_gb": memory_gb,
                "detection_source": "nvidia-smi",
                "vram_source": "nvidia-smi",
                "vram_confidence": "high",
            }
        except Exception:
            return None

    @staticmethod
    def _detect_apple_silicon() -> Optional[Dict[str, Any]]:
        if platform.system().lower() != "darwin":
            return None

        try:
            cpu_brand = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True,
                timeout=2,
                check=True,
            ).stdout.strip()
            if "apple" not in cpu_brand.lower() and "m1" not in cpu_brand.lower() and "m2" not in cpu_brand.lower() and "m3" not in cpu_brand.lower():
                return None

            mem_bytes = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True,
                text=True,
                timeout=2,
                check=True,
            ).stdout.strip()
            unified_gb = round(float(mem_bytes) / (1024**3), 1)
            return {
                "type": "apple_silicon",
                "name": cpu_brand,
                "vram_gb": unified_gb,
                "note": "Unified Memory (geteilt zwischen CPU/GPU)",
                "detection_source": "sysctl",
                "vram_source": "unified_memory",
                "vram_confidence": "medium",
            }
        except Exception:
            return None

    @staticmethod
    def _detect_generic_gpu() -> Optional[Dict[str, Any]]:
        system_name = platform.system().lower()
        if system_name != "windows":
            return None

        try:
            controllers = OllamaManager._read_windows_video_controllers()
            if not controllers:
                return None
            controllers = [
                controller
                for controller in controllers
                if OllamaManager._is_preferred_windows_gpu_name(str(controller.get("name") or ""))
            ]
            if not controllers:
                return None

            def gpu_score(item: Dict[str, Any]) -> tuple[int, float]:
                name = str(item.get("name") or "").lower()
                vram = float(item.get("vram_gb") or 0.0)
                preferred = 1 if OllamaManager._is_preferred_windows_gpu_name(name) else 0
                vendor_bonus = 1 if any(v in name for v in ["amd", "radeon", "nvidia", "geforce", "intel arc"]) else 0
                return (preferred + vendor_bonus, vram)

            best = max(controllers, key=gpu_score)
            best_name = str(best.get("name") or "Unbekannt")
            best_vram = best.get("vram_gb")
            detection_source = str(best.get("detection_source") or "windows")
            vram_source = str(best.get("vram_source") or ("windows_adapter_ram" if best_vram else "none"))
            vram_confidence = str(best.get("vram_confidence") or ("medium" if best_vram else "none"))
            inferred_vram = OllamaManager._infer_vram_from_gpu_name(best_name)
            if inferred_vram is not None and (best_vram is None or float(best_vram or 0.0) < inferred_vram):
                best_vram = inferred_vram
                vram_source = "gpu_name_heuristic"
                vram_confidence = "medium"

            gpu_type = "generic"
            best_name_l = best_name.lower()
            if "amd" in best_name_l or "radeon" in best_name_l:
                gpu_type = "amd"
            elif "nvidia" in best_name_l or "geforce" in best_name_l:
                gpu_type = "nvidia"
            elif "intel" in best_name_l:
                gpu_type = "intel"

            return {
                "type": gpu_type,
                "name": best_name,
                "vram_gb": best_vram,
                "detection_source": detection_source,
                "vram_source": vram_source,
                "vram_confidence": vram_confidence,
            }
        except Exception:
            return None

        return None

    @staticmethod
    def _read_windows_video_controllers() -> List[Dict[str, Any]]:
        controllers: List[Dict[str, Any]] = []

        try:
            ps_result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    "Get-CimInstance Win32_VideoController | "
                    "Select-Object Name,AdapterRAM,PNPDeviceID | ConvertTo-Json -Compress",
                ],
                capture_output=True,
                text=True,
                timeout=5,
                check=True,
            )
            raw = (ps_result.stdout or "").strip()
            if raw:
                payload = json.loads(raw)
                entries = payload if isinstance(payload, list) else [payload]
                for entry in entries:
                    if not isinstance(entry, dict):
                        continue
                    name = str(entry.get("Name") or "").strip()
                    if not name:
                        continue
                    adapter_ram = entry.get("AdapterRAM")
                    controllers.append(
                        {
                            "name": name,
                            "vram_gb": OllamaManager._parse_windows_adapter_ram_gb(adapter_ram),
                            "pnp_device_id": str(entry.get("PNPDeviceID") or "").strip() or None,
                            "detection_source": "cim",
                            "vram_source": "cim_adapter_ram" if adapter_ram else "none",
                            "vram_confidence": "medium" if adapter_ram else "none",
                        }
                    )
        except Exception:
            pass

        if OllamaManager._has_preferred_windows_gpu(controllers):
            return controllers
        controllers = []

        # Erforderliche Kompatibilitaet: Name-Abfrage ueber WMIC (auch fuer AMD).
        try:
            csv_result = subprocess.run(
                [
                    "wmic",
                    "path",
                    "win32_VideoController",
                    "get",
                    "name,AdapterRAM",
                    "/format:csv",
                ],
                capture_output=True,
                text=True,
                timeout=4,
                check=True,
            )
            lines = [line.strip() for line in (csv_result.stdout or "").splitlines() if line.strip()]
            headers: List[str] = []
            for line in lines:
                parts = [part.strip() for part in line.split(",")]
                if not headers:
                    headers = [part.lower() for part in parts]
                    continue
                row = {headers[idx]: value for idx, value in enumerate(parts) if idx < len(headers)}
                name = str(row.get("name") or "").strip()
                if not name:
                    continue

                controllers.append(
                    {
                        "name": name,
                        "vram_gb": OllamaManager._parse_windows_adapter_ram_gb(row.get("adapterram")),
                        "detection_source": "wmic",
                        "vram_source": "wmic_adapter_ram" if row.get("adapterram") else "none",
                        "vram_confidence": "medium" if row.get("adapterram") else "none",
                    }
                )
        except Exception:
            pass

        if OllamaManager._has_preferred_windows_gpu(controllers):
            return controllers
        controllers = []

        # Fallback nur Name, falls AdapterRAM nicht geliefert wird.
        try:
            name_result = subprocess.run(
                ["wmic", "path", "win32_VideoController", "get", "name"],
                capture_output=True,
                text=True,
                timeout=4,
                check=True,
            )
            for raw_line in (name_result.stdout or "").splitlines():
                name = raw_line.strip()
                if not name or name.lower() == "name":
                    continue
                controllers.append(
                    {
                        "name": name,
                        "vram_gb": None,
                        "detection_source": "wmic_name",
                        "vram_source": "none",
                        "vram_confidence": "none",
                    }
                )
        except Exception:
            pass

        if OllamaManager._has_preferred_windows_gpu(controllers):
            return controllers
        controllers = []

        controllers = OllamaManager._read_windows_video_controllers_from_registry()
        if OllamaManager._has_preferred_windows_gpu(controllers):
            return controllers

        return OllamaManager._read_windows_video_controllers_from_dxdiag()

    @staticmethod
    def _has_preferred_windows_gpu(controllers: List[Dict[str, Any]]) -> bool:
        return any(OllamaManager._is_preferred_windows_gpu_name(str(item.get("name") or "")) for item in controllers)

    @staticmethod
    def _read_windows_video_controllers_from_registry() -> List[Dict[str, Any]]:
        try:
            registry_result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    "Get-ItemProperty 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Video\\*\\0000' "
                    "-ErrorAction SilentlyContinue | "
                    "Where-Object { $_.'HardwareInformation.AdapterString' } | "
                    "Select-Object @{Name='Name';Expression={[Text.Encoding]::Unicode.GetString($_.'HardwareInformation.AdapterString').Trim([char]0)}},"
                    "@{Name='MemorySize';Expression={$_.'HardwareInformation.MemorySize'}} | ConvertTo-Json -Compress",
                ],
                capture_output=True,
                text=True,
                timeout=5,
                check=True,
            )
            raw = (registry_result.stdout or "").strip()
            if not raw:
                return []
            payload = json.loads(raw)
            entries = payload if isinstance(payload, list) else [payload]
            controllers: List[Dict[str, Any]] = []
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                name = str(entry.get("Name") or "").strip()
                if not name:
                    continue
                memory_size = entry.get("MemorySize")
                controllers.append(
                    {
                        "name": name,
                        "vram_gb": OllamaManager._parse_windows_adapter_ram_gb(memory_size),
                        "detection_source": "registry",
                        "vram_source": "registry_memory_size" if memory_size else "none",
                        "vram_confidence": "medium" if memory_size else "none",
                    }
                )
            return controllers
        except Exception:
            return []

    @staticmethod
    def _read_windows_video_controllers_from_dxdiag() -> List[Dict[str, Any]]:
        dxdiag = shutil.which("dxdiag") or "dxdiag"

        report_path = ""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as report:
                report_path = report.name
            subprocess.run(
                [dxdiag, "/whql:off", "/t", report_path],
                capture_output=True,
                text=True,
                timeout=20,
                check=True,
            )
            with open(report_path, "r", encoding="utf-16", errors="ignore") as handle:
                text = handle.read()
            if not text.strip():
                with open(report_path, "r", encoding="utf-8", errors="ignore") as handle:
                    text = handle.read()
            return OllamaManager._parse_dxdiag_video_controllers(text)
        except Exception:
            return []
        finally:
            if report_path:
                try:
                    os.unlink(report_path)
                except Exception:
                    pass

    @staticmethod
    def _parse_dxdiag_video_controllers(text: str) -> List[Dict[str, Any]]:
        controllers: List[Dict[str, Any]] = []
        blocks = re.split(r"\r?\n\s*-{5,}\s*\r?\n", text or "")
        for block in blocks:
            if "Card name:" not in block and "Chip type:" not in block:
                continue
            name_match = re.search(r"Card name:\s*(.+)", block)
            if not name_match:
                continue
            name = name_match.group(1).strip()
            if not name:
                continue
            memory_match = re.search(r"(?:Display Memory|Dedicated Memory):\s*([0-9]+)\s*MB", block, flags=re.IGNORECASE)
            vram_gb = None
            if memory_match:
                vram_gb = round(float(memory_match.group(1)) / 1024.0, 1)
            controllers.append(
                {
                    "name": name,
                    "vram_gb": vram_gb,
                    "detection_source": "dxdiag",
                    "vram_source": "dxdiag_memory" if vram_gb else "none",
                    "vram_confidence": "medium" if vram_gb else "none",
                }
            )
        return controllers

    @staticmethod
    def _parse_windows_adapter_ram_gb(raw_value: Any) -> Optional[float]:
        try:
            if raw_value is None:
                return None
            value = int(str(raw_value).strip())
            if value <= 0:
                return None
            return round(float(value) / (1024**3), 1)
        except Exception:
            return None

    @staticmethod
    def _infer_vram_from_gpu_name(name: str) -> Optional[float]:
        normalized = re.sub(r"[^a-z0-9]+", " ", str(name or "").lower())
        normalized = re.sub(r"\b(?:r|tm)\b", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        known_cards = [
            (r"\brx 7900 xtx\b", 24.0),
            (r"\brx 7900 xt\b", 20.0),
            (r"\brx 7900 gre\b", 16.0),
            (r"\brx 7800 xt\b", 16.0),
            (r"\brx 7700 xt\b", 12.0),
            (r"\brx 7600 xt\b", 16.0),
            (r"\brx 7600\b", 8.0),
            (r"\brx 6950 xt\b", 16.0),
            (r"\brx 6900 xt\b", 16.0),
            (r"\brx 6800 xt\b", 16.0),
            (r"\brx 6800\b", 16.0),
            (r"\brx 6750 xt\b", 12.0),
            (r"\brx 6700 xt\b", 12.0),
            (r"\brx 6700\b", 10.0),
            (r"\brx 6650 xt\b", 8.0),
            (r"\brx 6600 xt\b", 8.0),
            (r"\brx 6600\b", 8.0),
            (r"\brx 5700 xt\b", 8.0),
            (r"\brx 5700\b", 8.0),
            (r"\brx 580\b", 8.0),
            (r"\brtx 4090\b", 24.0),
            (r"\brtx 4080 super\b", 16.0),
            (r"\brtx 4080\b", 16.0),
            (r"\brtx 5070 ti\b", 16.0),
            (r"\brtx 5070\b", 12.0),
            (r"\brtx 5060 ti\b", 16.0),
            (r"\brtx 5060\b", 8.0),
            (r"\brtx 4070 ti super\b", 16.0),
            (r"\brtx 4070 ti\b", 12.0),
            (r"\brtx 4070 super\b", 12.0),
            (r"\brtx 4070\b", 12.0),
            (r"\brtx 3090 ti\b", 24.0),
            (r"\brtx 3090\b", 24.0),
            (r"\brtx 3080 ti\b", 12.0),
            (r"\brtx 3080\b", 10.0),
            (r"\brtx 3070 ti\b", 8.0),
            (r"\brtx 3070\b", 8.0),
            (r"\brtx 3060 ti\b", 8.0),
            (r"\brtx 3060\b", 12.0),
            (r"\brtx 4060 ti\b", 8.0),
            (r"\brtx 4060\b", 8.0),
            (r"\bintel arc a770\b", 16.0),
            (r"\bintel arc a750\b", 8.0),
            (r"\bintel arc a580\b", 8.0),
            (r"\bintel arc a380\b", 6.0),
        ]
        for pattern, vram_gb in known_cards:
            if re.search(pattern, normalized):
                return vram_gb
        return None

    @staticmethod
    def _is_preferred_windows_gpu_name(name: str) -> bool:
        lower_name = str(name or "").lower()
        if not lower_name:
            return False
        noisy_adapters = [
            "microsoft basic",
            "remote display",
            "virtual display",
            "hyper-v",
            "vmware",
            "virtualbox",
            "parallels",
        ]
        return not any(token in lower_name for token in noisy_adapters)


ollama_manager = OllamaManager()
