"""Build or validate ``modal_request`` for chat API responses (MCL / video player)."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from backend.data.schemas import ModalRequest

logger = logging.getLogger("janus_backend")

_YOUTUBE_MATCHERS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "watch",
        re.compile(
            r"(?P<url>(?:https?://)?(?:www\.|m\.)?youtube\.com/watch\?[^\s#<>)\]]*\bv=(?P<id>[a-zA-Z0-9_-]{11})\b"
            r"(?:[^\s#<>)\]]*)?)",
            re.IGNORECASE,
        ),
    ),
    (
        "youtu.be",
        re.compile(
            r"(?P<url>(?:https?://)?youtu\.be/(?P<id>[a-zA-Z0-9_-]{11})(?:[^\s#<>)\]]*)?)",
            re.IGNORECASE,
        ),
    ),
    (
        "embed",
        re.compile(
            r"(?P<url>(?:https?://)?(?:www\.)?youtube\.com/embed/(?P<id>[a-zA-Z0-9_-]{11})(?:[^\s#<>)\]]*)?)",
            re.IGNORECASE,
        ),
    ),
    (
        "nocookie_embed",
        re.compile(
            r"(?P<url>(?:https?://)?(?:www\.)?youtube-nocookie\.com/embed/(?P<id>[a-zA-Z0-9_-]{11})(?:[^\s#<>)\]]*)?)",
            re.IGNORECASE,
        ),
    ),
    (
        "shorts",
        re.compile(
            r"(?P<url>(?:https?://)?(?:www\.|m\.)?youtube\.com/shorts/(?P<id>[a-zA-Z0-9_-]{11})(?:[^\s#<>)\]]*)?)",
            re.IGNORECASE,
        ),
    ),
)
_VIMEO_RE = re.compile(
    r"(?P<url>(?:https?://)?(?:www\.)?vimeo\.com/(?:video/)?(?P<id>\d+)(?:[?&][^\s]*)?)",
    re.IGNORECASE,
)

# Bekannte oder offensichtlich ungültige Muster (Halluzinationen / Test-IDs). Erweiterbar.
_SUSPICIOUS_YOUTUBE_IDS: frozenset[str] = frozenset(
    {
        "00000000000",
        "11111111111",
        "aaaaaaaaaaa",
        "xxxxxxxxxxx",
    }
)


def _youtube_id_structurally_suspicious(video_id: str) -> bool:
    if len(video_id) != 11:
        return True
    if video_id in _SUSPICIOUS_YOUTUBE_IDS:
        return True
    if len(set(video_id)) == 1:
        return True
    return False


def _youtube_url_passes_modal_validation(video_id: str, raw_url: str) -> bool:
    """Lehnt zu kurze URLs und typische Halluzinations-IDs ab (Embed öffnet sonst „nicht verfügbar“)."""
    if _youtube_id_structurally_suspicious(video_id):
        return False
    u = (raw_url or "").strip()
    if len(u) < 28:
        return False
    low = u.lower()
    if "youtube.com/watch" in low and len(u) < 42:
        return False
    if "youtube.com/embed" in low and len(u) < 40:
        return False
    return True


def _vimeo_url_passes_modal_validation(vimeo_id: str, raw_url: str) -> bool:
    if not vimeo_id.isdigit() or len(vimeo_id) < 6:
        return False
    u = (raw_url or "").strip()
    if len(u) < 24:
        return False
    return True


def _should_reject_video_modal_request(mr: ModalRequest) -> bool:
    if (mr.type or "").strip().lower() != "video":
        return False
    pl = dict(mr.payload or {})
    src = str(pl.get("source") or "").strip().lower()
    blob = f"{pl.get('url') or ''} {pl.get('embed_url') or ''}"
    if src == "vimeo" or "vimeo.com" in blob.lower():
        vm = _VIMEO_RE.search(blob)
        if not vm:
            return True
        vid = vm.group("id")
        raw = _ensure_http(vm.group("url"))
        return not _vimeo_url_passes_modal_validation(vid, raw)
    m = _first_youtube_match(blob)
    if not m:
        return True
    vid = m.group("id")
    raw = _ensure_http(m.group("url"))
    return not _youtube_url_passes_modal_validation(vid, raw)


def _ensure_http(url: str) -> str:
    u = (url or "").strip()
    if not u:
        return u
    if u.startswith("//"):
        return "https:" + u
    if not re.match(r"^https?://", u, re.IGNORECASE):
        return "https://" + u.lstrip("/")
    return u


def _youtube_embed(video_id: str) -> str:
    return f"https://www.youtube.com/embed/{video_id}?rel=0"


def _vimeo_embed(video_id: str) -> str:
    return f"https://player.vimeo.com/video/{video_id}"


def _url_has_embed_path(m: re.Match[str]) -> bool:
    u = (m.group("url") or "").lower()
    return "/embed/" in u or "youtube-nocookie.com/embed" in u


def _match_quality_score(label: str, m: re.Match[str]) -> int:
    """Höher = besser für Embed: Shorts runter, /embed/ hoch."""
    s = 0
    if label != "shorts":
        s += 100
    if _url_has_embed_path(m):
        s += 50
    return s


def _ordered_youtube_candidates(blob: str) -> List[Tuple[re.Match[str], str]]:
    """Pro Video-ID ein Treffer: bei mehreren URLs zur gleichen ID die embed-tauglichere Variante behalten."""
    if not (blob or "").strip():
        return []
    hits: List[Tuple[int, re.Match[str], str]] = []
    for label, rx in _YOUTUBE_MATCHERS:
        for m in rx.finditer(blob):
            hits.append((m.start(), m, label))
    hits.sort(key=lambda x: x[0])
    best_by_id: Dict[str, Tuple[int, int, re.Match[str], str]] = {}
    for start, m, label in hits:
        vid = m.group("id")
        sc = _match_quality_score(label, m)
        if vid not in best_by_id:
            best_by_id[vid] = (sc, start, m, label)
        else:
            old_sc, old_start, _om, _olb = best_by_id[vid]
            if sc > old_sc or (sc == old_sc and start < old_start):
                best_by_id[vid] = (sc, start, m, label)
    ordered = sorted(best_by_id.values(), key=lambda x: x[1])
    return [(m, lb) for _sc, _st, m, lb in ordered]


def _pick_best_youtube_candidate(candidates: List[Tuple[re.Match[str], str]]) -> Optional[Tuple[re.Match[str], str]]:
    """Mehrere verschiedene Videos: Shorts vermeiden wenn möglich; unter den Rest /embed/-URLs zuerst."""
    if not candidates:
        return None

    def is_shorts(label: str) -> bool:
        return label == "shorts"

    if len(candidates) > 1:
        non_short = [(m, lb) for m, lb in candidates if not is_shorts(lb)]
        pool: List[Tuple[re.Match[str], str]] = non_short if non_short else list(candidates)
    else:
        pool = list(candidates)

    with_embed = [(m, lb) for m, lb in pool if _url_has_embed_path(m)]
    if with_embed:
        return with_embed[0]
    return pool[0]


def _first_youtube_match(blob: str) -> Optional[re.Match[str]]:
    """Ein Treffer nach derselben Heuristik (Einzel-URL / Payload)."""
    cands = _ordered_youtube_candidates(blob)
    picked = _pick_best_youtube_candidate(cands)
    return picked[0] if picked else None


# BACKLOG-011 FIX: detect_video_modal_request_dict() entfernt
# URL-Detection Fallback wurde deaktiviert, modal_request wird ausschließlich aus video.search tool_results abgeleitet
# Diese Funktion ist nicht mehr benötigt und wurde entfernt um falsch-positive Video-Links zu verhindern


def merge_skill_modal_request_into_workflow(wf: Any) -> None:
    """If the skill placed ``modal_request`` on ``wf.response``, copy it to ``wf.modal_request``."""
    if getattr(wf, "modal_request", None) is not None:
        return
    resp = getattr(wf, "response", None)
    if isinstance(resp, dict):
        raw = resp.get("modal_request")
        if raw is not None:
            wf.modal_request = raw


def _ensure_video_embed_in_payload(mr: ModalRequest) -> ModalRequest:
    """Fill ``payload.embed_url`` for type ``video`` when only ``url`` is present."""
    if (mr.type or "").strip().lower() != "video":
        return mr
    pl = dict(mr.payload or {})
    is_embeddable = bool(pl.get("is_embeddable", True))
    if not is_embeddable:
        pl["external_only"] = True
        pl.setdefault("external_hint", "Nur direkt auf YouTube verfügbar.")
        pl["embed_url"] = ""
        return ModalRequest(type=mr.type, payload=pl, options=mr.options)
    if pl.get("embed_url"):
        return mr
    url = str(pl.get("url") or "").strip()
    if not url:
        return mr
    m = _first_youtube_match(url)
    if m:
        pl["embed_url"] = _youtube_embed(m.group("id"))
        pl.setdefault("source", "youtube")
        return ModalRequest(type=mr.type, payload=pl, options=mr.options)
    m = _VIMEO_RE.search(url)
    if m:
        pl["embed_url"] = _vimeo_embed(m.group("id"))
        pl.setdefault("source", "vimeo")
        return ModalRequest(type=mr.type, payload=pl, options=mr.options)
    return mr


def resolve_modal_request_for_execution(wf: Any) -> Optional[ModalRequest]:
    """Validated ``ModalRequest`` from workflow or skill response. URL detection fallback disabled (BACKLOG-011)."""
    merge_skill_modal_request_into_workflow(wf)
    raw = getattr(wf, "modal_request", None)
    if raw is not None:
        try:
            mr = raw if isinstance(raw, ModalRequest) else ModalRequest.model_validate(raw)
            mr = _ensure_video_embed_in_payload(mr)
            if _should_reject_video_modal_request(mr):
                logger.warning(
                    "modal_request video rejected by URL validation; no fallback to URL detection (BACKLOG-011)",
                )
            else:
                return mr
        except Exception:
            logger.warning("modal_request on workflow invalid; no fallback to URL detection (BACKLOG-011)", exc_info=True)
    # BACKLOG-011 FIX: URL-Detection Fallback deaktiviert
    # modal_request wird ausschließlich aus video.search tool_results abgeleitet (in response_finalizer.py)
    # Falsch-positive Video-Links bei nicht-video-bezogenen Antworten werden verhindert
    return None
