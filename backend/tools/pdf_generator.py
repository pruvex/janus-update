# backend/tools/pdf_generator.py

import logging
import os
import tempfile
import time
import base64
import re
import textwrap
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse
from typing import Dict, Optional, Tuple

try:
    from PIL import Image  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    Image = None

from fpdf import FPDF
from pydantic import BaseModel, Field

from backend.data.schemas_tools import ToolErrorDetails, ToolResultV1
from backend.services import rag_manager
from backend.utils.paths import get_images_dir
from backend.utils.config_loader import load_config_data
from backend.utils.paths import get_app_data_dir, resource_path
from sqlalchemy.orm import Session

logger = logging.getLogger("janus_backend")

FONT_PATH = resource_path("backend/assets/fonts/DejaVuSans.ttf")
_AGENT_SIGNATURE_RE = re.compile(r"^\s*Erstellt\s+vom\s+.+?Spezial-Agenten\.?\s*$", re.IGNORECASE)
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_MARKDOWN_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")

_DEFAULT_LAYOUT_PROFILE = "bericht"
@dataclass(frozen=True)
class LayoutProfile:
    base_font_size: int
    heading_scales: Dict[str, float]
    paragraph_spacing: int
    heading_spacing: int
    image_spacing: int
    line_height: float
    title_page: bool = False
    chapter_page_break: bool = False
    image_max_width: int = 160
    image_alignment: str = "left"
    heading_alignment: str = "L"
    text_alignment: str = "L"
    heading_color: Tuple[int, int, int] = (0, 0, 0)
    text_color: Tuple[int, int, int] = (40, 40, 40)


@dataclass
class StoryChapterBlock:
    chapter_title: str
    text_above: str
    image_paths: list[str]
    text_below: str


@dataclass
class StorybookPagePlan:
    chapter_title: str
    text_above: str
    image_path: Optional[str]
    text_below: str
    title_on_page: bool = True
    image_width: Optional[float] = None
    vertical_offset: float = 0.0
    scene_class: str = "standard"
    page_style: str = "standard"


_LAYOUT_PROFILES = {
    "bericht": LayoutProfile(
        base_font_size=11,
        heading_scales={"h1": 1.55, "h2": 1.32, "h3": 1.15},
        paragraph_spacing=2,
        heading_spacing=2,
        image_spacing=4,
        line_height=5,
        image_max_width=160,
        image_alignment="left",
        heading_alignment="L",
        text_alignment="L",
        heading_color=(0, 0, 0),
        text_color=(40, 40, 40),
    ),
    "bilderbuch": LayoutProfile(
        base_font_size=15,
        heading_scales={"h1": 2.5, "h2": 1.8, "h3": 1.4},
        paragraph_spacing=6,
        heading_spacing=12,
        image_spacing=10,
        line_height=7.5,
        title_page=True,
        chapter_page_break=True,
        image_max_width=160,
        image_alignment="center",
        heading_alignment="C",
        text_alignment="L",
        heading_color=(200, 70, 40),
        text_color=(30, 30, 30),
    ),
    "praesentation": LayoutProfile(
        base_font_size=12,
        heading_scales={"h1": 1.8, "h2": 1.45, "h3": 1.2},
        paragraph_spacing=3,
        heading_spacing=3,
        image_spacing=5,
        line_height=6,
        image_max_width=140,
        image_alignment="center",
        heading_alignment="C",
        text_alignment="L",
    ),
    "magazin": LayoutProfile(
        base_font_size=12,
        heading_scales={"h1": 1.7, "h2": 1.4, "h3": 1.16},
        paragraph_spacing=3,
        heading_spacing=2,
        image_spacing=5,
        line_height=6,
        image_max_width=150,
        image_alignment="left",
        heading_alignment="L",
        text_alignment="L",
    ),
}


def _normalize_layout_profile(value: str) -> str:
    candidate = str(value or "").strip().lower()
    aliases = {
        "auto": "auto",
        "default": "auto",
        "report": "bericht",
        "bericht": "bericht",
        "storybook": "bilderbuch",
        "children": "bilderbuch",
        "bilderbuch": "bilderbuch",
        "kinderbuch": "bilderbuch",
        "presentation": "praesentation",
        "praesentation": "praesentation",
        "präsentation": "praesentation",
        "magazine": "magazin",
        "magazin": "magazin",
        "blog": "magazin",
    }
    return aliases.get(candidate, candidate)


def _estimate_image_height(image_path: str, width: float) -> float:
    if width <= 0:
        return 0.0

    aspect_ratio = 1.0
    if Image:
        try:
            with Image.open(image_path) as img:  # type: ignore[attr-defined]
                if img.width > 0:
                    aspect_ratio = img.height / img.width
        except Exception:
            aspect_ratio = 1.0
    return max(width * aspect_ratio, width * 0.6)


def _estimate_future_text_height(lines: list[str], start_index: int, style: LayoutProfile) -> float:
    total = 0.0
    line_height = float(style.line_height)
    paragraph_spacing = max(2, int(style.paragraph_spacing))

    for fragment in lines[start_index:]:
        stripped = fragment.strip()
        if stripped.startswith("## ") or stripped.startswith("# ") or _MARKDOWN_IMAGE_RE.search(stripped):
            break  # Stop beim nächsten Kapitel oder Bild

        if not stripped:
            total += paragraph_spacing
            continue

        chars_per_line = _get_storybook_chars_per_line(style)
        estimated_lines = max(1, len(stripped) // chars_per_line + 1)
        total += (estimated_lines * line_height) + paragraph_spacing

    return total


def _estimate_wrapped_text_height(text: str, style: LayoutProfile, chars_per_line: int) -> float:
    normalized = str(text or "").strip()
    if not normalized:
        return 0.0
    line_height = float(style.line_height)
    paragraph_spacing = max(2, int(style.paragraph_spacing))
    total = 0.0
    for paragraph in normalized.split("\n"):
        stripped = paragraph.strip()
        if not stripped:
            total += paragraph_spacing
            continue
        estimated_lines = max(1, len(stripped) // max(1, chars_per_line) + 1)
        total += (estimated_lines * line_height) + paragraph_spacing
    return total


def _split_storybook_sentences(text: str) -> list[str]:
    return [part.strip() for part in _split_sentences_preserving_abbreviations(text) if part.strip()]


def _build_storybook_text_parts(raw_above: str, raw_below: str) -> tuple[str, str]:
    sentences = _split_storybook_sentences(f"{str(raw_above or '').strip()} {str(raw_below or '').strip()}".strip())
    if not sentences:
        return str(raw_above or "").strip(), str(raw_below or "").strip()
    split_index = 2 if len(sentences) >= 4 else 1 if len(sentences) >= 2 else len(sentences)
    text_above = " ".join(sentences[:split_index]).strip()
    text_below = " ".join(sentences[split_index:]).strip()
    return text_above, text_below


def _get_storybook_chars_per_line(style: LayoutProfile) -> int:
    if style.base_font_size >= 15:
        return 68
    return 90


def _estimate_last_wrapped_line_length(text: str, chars_per_line: int) -> int:
    normalized = str(text or "").strip()
    if not normalized:
        return 0

    last_line_length = 0
    for paragraph in normalized.split("\n"):
        stripped = paragraph.strip()
        if not stripped:
            continue
        wrapped = textwrap.wrap(
            stripped,
            width=max(1, chars_per_line),
            break_long_words=False,
            break_on_hyphens=False,
        )
        if wrapped:
            last_line_length = len(wrapped[-1].strip())
    return last_line_length


def _has_too_short_last_line(text: str, chars_per_line: int) -> bool:
    last_line_length = _estimate_last_wrapped_line_length(text, chars_per_line)
    if last_line_length <= 0:
        return False
    return last_line_length < max(12, int(chars_per_line * 0.22))


def _classify_storybook_scene(block: StoryChapterBlock) -> str:
    combined = f"{block.chapter_title} {block.text_above} {block.text_below}".lower()
    hero_markers = [
        "plötzlich",
        "auf einmal",
        "endlich",
        "geheim",
        "wunder",
        "strahl",
        "leuchten",
        "funkel",
        "fest",
        "schloss",
        "mond",
        "stern",
        "regenbogen",
    ]
    calm_markers = [
        "leise",
        "sanft",
        "ruhig",
        "kuschel",
        "schlief",
        "abend",
        "nacht",
        "flüster",
    ]
    action_markers = [
        "lief",
        "rannten",
        "sprang",
        "flog",
        "suchten",
        "entdeckten",
        "retteten",
        "folgten",
    ]
    if any(marker in combined for marker in hero_markers):
        return "hero"
    if any(marker in combined for marker in action_markers):
        return "adventure"
    if any(marker in combined for marker in calm_markers):
        return "calm"
    return "standard"


def _determine_storybook_page_style(
    scene_class: str,
    has_image: bool,
    title_on_page: bool,
    is_continuation: bool,
) -> str:
    if is_continuation:
        return "continuation-soft" if scene_class == "calm" else "continuation"
    if has_image and scene_class == "hero":
        return "hero"
    if has_image and title_on_page:
        return "chapter-opening"
    if has_image:
        return "image-focus"
    return "text-balanced"


def _rebalance_storybook_block_for_height(
    block: StoryChapterBlock,
    style: LayoutProfile,
    font_size: int,
    image_width: float,
    available_height: float,
) -> StoryChapterBlock:
    combined_text = f"{str(block.text_above or '').strip()} {str(block.text_below or '').strip()}".strip()
    sentences = _split_storybook_sentences(combined_text)
    if len(sentences) < 2:
        return block

    min_below_sentences = 2 if len(sentences) >= 4 else 1
    target_split = min(2 if len(sentences) >= 4 else 1, max(1, len(sentences) - min_below_sentences))
    best_fit: Optional[tuple[int, float, StoryChapterBlock]] = None
    best_overflow: Optional[tuple[float, int, StoryChapterBlock]] = None

    for split_index in range(1, len(sentences)):
        below_count = len(sentences) - split_index
        below_penalty = max(0, min_below_sentences - below_count)
        candidate = StoryChapterBlock(
            chapter_title=block.chapter_title,
            text_above=" ".join(sentences[:split_index]).strip(),
            image_paths=list(block.image_paths),
            text_below=" ".join(sentences[split_index:]).strip(),
        )
        candidate_height = _estimate_storybook_block_height(candidate, style, font_size, image_width)
        split_distance = abs(split_index - target_split) + (below_penalty * 3)

        if candidate_height <= available_height:
            if best_fit is None or split_distance < best_fit[0] or (
                split_distance == best_fit[0] and candidate_height > best_fit[1]
            ):
                best_fit = (split_distance, candidate_height, candidate)
            continue

        overflow = candidate_height - available_height
        overflow_score = overflow + (below_penalty * float(style.line_height) * 1.5)
        if best_overflow is None or overflow_score < best_overflow[0] or (
            overflow_score == best_overflow[0] and split_distance < best_overflow[1]
        ):
            best_overflow = (overflow_score, split_distance, candidate)

    if best_fit is not None:
        return best_fit[2]
    if best_overflow is not None:
        return best_overflow[2]
    return block


def _split_storybook_text_to_fit_height(
    text: str,
    style: LayoutProfile,
    available_height: float,
    min_sentences_top: int = 2,
) -> tuple[str, str]:
    sentences = _split_storybook_sentences(text)
    if not sentences:
        return "", ""

    if available_height <= 0:
        return "", " ".join(sentences).strip()

    chars_per_line = _get_storybook_chars_per_line(style)
    fitting_count = 0
    for idx in range(1, len(sentences) + 1):
        candidate = " ".join(sentences[:idx]).strip()
        candidate_height = _estimate_wrapped_text_height(candidate, style, chars_per_line)
        if candidate_height <= available_height:
            fitting_count = idx
        else:
            break

    if fitting_count <= 0:
        return "", " ".join(sentences).strip()

    remainder_count = len(sentences) - fitting_count
    if remainder_count == 1 and fitting_count > min_sentences_top:
        fitting_count -= 1
    elif fitting_count < len(sentences):
        candidate_top = " ".join(sentences[:fitting_count]).strip()
        if fitting_count > min_sentences_top and _has_too_short_last_line(candidate_top, chars_per_line):
            fitting_count -= 1

    fitting_count = max(1, fitting_count)
    top_text = " ".join(sentences[:fitting_count]).strip()
    remaining_text = " ".join(sentences[fitting_count:]).strip()
    return top_text, remaining_text


def _storybook_image_page_text_safety_margin(style: LayoutProfile) -> float:
    return max(float(style.line_height) * 1.15, float(style.paragraph_spacing) + 2.0)


def _select_storybook_image_width(
    image_path: Optional[str],
    requested_width: float,
    style: LayoutProfile,
    page_height: float,
    reserved_text_height: float,
    scene_class: str = "standard",
    page_style: str = "standard",
) -> Optional[float]:
    if not image_path or requested_width <= 0:
        return None

    min_width = 60.0
    max_width = max(min_width, requested_width)
    candidate_width = max_width
    available_for_image = max(42.0, page_height - reserved_text_height - int(style.image_spacing))
    target_ratio = _resolve_storybook_image_target_ratio(scene_class, page_style)
    target_image_height = min(max(available_for_image * 0.82, 52.0), page_height * target_ratio)

    estimated_height = _estimate_image_height(image_path, candidate_width)
    if estimated_height > available_for_image:
        shrink_ratio = available_for_image / max(estimated_height, 1e-6)
        candidate_width = max(min_width, candidate_width * shrink_ratio)
        estimated_height = _estimate_image_height(image_path, candidate_width)

    if estimated_height > target_image_height:
        shrink_ratio = target_image_height / max(estimated_height, 1e-6)
        candidate_width = max(min_width, candidate_width * shrink_ratio)

    return min(max_width, candidate_width)


def _compute_storybook_vertical_offset(plan_height: float, page_height: float, has_image: bool) -> float:
    if plan_height <= 0 or plan_height >= page_height:
        return 0.0

    leftover = page_height - plan_height
    if leftover <= 16:
        return 0.0

    ratio = 0.24 if has_image else 0.33
    return min(26.0, leftover * ratio)


def _resolve_storybook_image_target_ratio(scene_class: str, page_style: str) -> float:
    if page_style == "hero":
        return 0.68
    if scene_class == "hero":
        return 0.62
    if scene_class == "adventure":
        return 0.58
    if scene_class == "calm":
        return 0.48
    return 0.54


def _ensure_storybook_text_below_room(
    image_path: Optional[str],
    image_width: Optional[float],
    text_below: str,
    style: LayoutProfile,
    page_height: float,
    reserved_height: float,
) -> Optional[float]:
    if not image_path or not image_width or not text_below:
        return image_width

    sentences = _split_storybook_sentences(text_below)
    if not sentences:
        return image_width

    chars_per_line = _get_storybook_chars_per_line(style)
    current_width = image_width
    current_image_height = _estimate_image_height(image_path, current_width)
    safety_margin = _storybook_image_page_text_safety_margin(style)

    for target_sentence_count in (2, 1):
        if len(sentences) < target_sentence_count:
            continue
        target_text = " ".join(sentences[:target_sentence_count]).strip()
        target_text_height = _estimate_wrapped_text_height(target_text, style, chars_per_line)
        required_image_height = max(16.0, page_height - reserved_height - target_text_height - safety_margin)
        if current_image_height <= required_image_height:
            return current_width
        shrink_ratio = required_image_height / max(current_image_height, 1e-6)
        candidate_width = max(48.0, current_width * shrink_ratio)
        candidate_height = _estimate_image_height(image_path, candidate_width)
        if candidate_height <= required_image_height:
            return candidate_width

    return max(48.0, current_width)


def _fit_storybook_first_page_for_text(
    first_plan: StorybookPagePlan,
    text_below: str,
    style: LayoutProfile,
    font_size: int,
    page_height: float,
) -> bool:
    safety_target = page_height - (_storybook_image_page_text_safety_margin(style) if first_plan.image_path else 0.0)
    if not first_plan.image_path:
        candidate_height = _estimate_storybook_page_plan_height(
            StorybookPagePlan(
                chapter_title=first_plan.chapter_title,
                text_above=first_plan.text_above,
                image_path=None,
                text_below=text_below,
                title_on_page=first_plan.title_on_page,
                image_width=None,
                vertical_offset=0.0,
                scene_class=first_plan.scene_class,
                page_style=first_plan.page_style,
            ),
            style,
            font_size,
        )
        if candidate_height <= safety_target:
            first_plan.text_below = text_below
            return True
        return False

    if not first_plan.image_width:
        return False

    candidate_width = first_plan.image_width
    for _ in range(7):
        candidate_height = _estimate_storybook_page_plan_height(
            StorybookPagePlan(
                chapter_title=first_plan.chapter_title,
                text_above=first_plan.text_above,
                image_path=first_plan.image_path,
                text_below=text_below,
                title_on_page=first_plan.title_on_page,
                image_width=candidate_width,
                vertical_offset=0.0,
                scene_class=first_plan.scene_class,
                page_style=first_plan.page_style,
            ),
            style,
            font_size,
        )
        if candidate_height <= safety_target:
            first_plan.image_width = candidate_width
            first_plan.text_below = text_below
            return True

        image_height = _estimate_image_height(first_plan.image_path, candidate_width)
        excess_height = candidate_height - safety_target
        target_image_height = max(16.0, image_height - excess_height - float(style.image_spacing))
        shrink_ratio = target_image_height / max(image_height, 1e-6)
        next_width = max(48.0, candidate_width * shrink_ratio)
        if next_width >= candidate_width - 0.5:
            next_width = max(48.0, candidate_width - 8.0)
        if next_width >= candidate_width - 0.2:
            break
        candidate_width = next_width

    return False


def _is_short_storybook_remainder(text: str, style: LayoutProfile, page_height: float) -> bool:
    sentences = _split_storybook_sentences(text)
    if not sentences:
        return False
    chars_per_line = _get_storybook_chars_per_line(style)
    remainder_height = _estimate_wrapped_text_height(text, style, chars_per_line)
    min_comfort_height = max(page_height * 0.28, float(style.line_height) * 3.2)
    if len(sentences) <= 2:
        return True
    return remainder_height <= min_comfort_height or _has_too_short_last_line(text, chars_per_line)


def _stabilize_storybook_first_page_split(
    first_plan: StorybookPagePlan,
    remaining_text: str,
    style: LayoutProfile,
    font_size: int,
    page_height: float,
) -> tuple[str, str]:
    if not first_plan.text_below or not remaining_text:
        return first_plan.text_below, remaining_text
    if not _is_short_storybook_remainder(remaining_text, style, page_height):
        return first_plan.text_below, remaining_text

    original_width = first_plan.image_width
    original_first_text = first_plan.text_below
    merged_text = f"{str(first_plan.text_below or '').strip()} {str(remaining_text or '').strip()}".strip()
    if merged_text and _fit_storybook_first_page_for_text(first_plan, merged_text, style, font_size, page_height):
        return first_plan.text_below, ""

    first_plan.image_width = original_width
    first_plan.text_below = original_first_text

    first_sentences = _split_storybook_sentences(original_first_text)
    remaining_sentences = _split_storybook_sentences(remaining_text)
    while len(first_sentences) > 1 and _is_short_storybook_remainder(" ".join(remaining_sentences).strip(), style, page_height):
        remaining_sentences.insert(0, first_sentences.pop())

    rebalanced_first = " ".join(first_sentences).strip()
    rebalanced_remaining = " ".join(remaining_sentences).strip()
    first_plan.text_below = rebalanced_first
    return rebalanced_first, rebalanced_remaining


def _rebalance_storybook_first_page_text(
    first_plan: StorybookPagePlan,
    remaining_text: str,
    style: LayoutProfile,
    font_size: int,
    page_height: float,
) -> tuple[str, str]:
    if not first_plan.image_path:
        return "", remaining_text

    above_sentences = _split_storybook_sentences(first_plan.text_above)
    remaining_sentences = _split_storybook_sentences(remaining_text)
    if len(above_sentences) <= 2 or not remaining_sentences:
        return "", remaining_text

    while len(above_sentences) > 2:
        remaining_sentences.insert(0, above_sentences.pop())
        first_plan.text_above = " ".join(above_sentences).strip()
        candidate_remaining = " ".join(remaining_sentences).strip()
        reserved_height = _estimate_storybook_page_plan_height(first_plan, style, font_size)
        available_below_height = max(0.0, page_height - reserved_height)
        first_below, overflow_text = _split_storybook_text_to_fit_height(
            candidate_remaining,
            style,
            available_below_height,
            min_sentences_top=1,
        )
        if first_below:
            return first_below, overflow_text

    return "", " ".join(remaining_sentences).strip()


def _merge_short_continuation_back_to_first_page(
    first_plan: StorybookPagePlan,
    second_plan: StorybookPagePlan,
    style: LayoutProfile,
    font_size: int,
    page_height: float,
) -> bool:
    if not first_plan.image_path or not second_plan.text_below:
        return False

    continuation_sentences = _split_storybook_sentences(second_plan.text_below)
    if not continuation_sentences:
        return False

    continuation_height = _estimate_storybook_page_plan_height(second_plan, style, font_size)
    if len(continuation_sentences) > 2 and continuation_height > page_height * 0.34:
        return False

    merged_text = f"{str(first_plan.text_below or '').strip()} {str(second_plan.text_below or '').strip()}".strip()
    if not merged_text:
        return False

    original_width = first_plan.image_width
    original_text = first_plan.text_below
    reserved_without_below = _estimate_storybook_page_plan_height(
        StorybookPagePlan(
            chapter_title=first_plan.chapter_title,
            text_above=first_plan.text_above,
            image_path=first_plan.image_path,
            text_below="",
            title_on_page=first_plan.title_on_page,
            image_width=first_plan.image_width,
            vertical_offset=0.0,
            scene_class=first_plan.scene_class,
            page_style=first_plan.page_style,
        ),
        style,
        font_size,
    )

    if first_plan.image_width:
        adjusted_width = _ensure_storybook_text_below_room(
            first_plan.image_path,
            first_plan.image_width,
            merged_text,
            style,
            page_height,
            reserved_without_below,
        )
        if adjusted_width and adjusted_width < first_plan.image_width:
            first_plan.image_width = adjusted_width

    if not _fit_storybook_first_page_for_text(first_plan, merged_text, style, font_size, page_height):
        first_plan.image_width = original_width
        first_plan.text_below = original_text
        return False

    second_plan.text_below = ""
    return True


def _rebalance_storybook_plans(plans: list[StorybookPagePlan], style: LayoutProfile, page_height: float) -> list[StorybookPagePlan]:
    if len(plans) < 2:
        return plans

    first_plan = plans[0]
    second_plan = plans[1]
    if not first_plan.image_path or not second_plan.text_below:
        return plans

    if _merge_short_continuation_back_to_first_page(first_plan, second_plan, style, style.base_font_size, page_height):
        return [plan for plan in plans if plan.text_above or plan.text_below or plan.image_path or plan.title_on_page]

    chars_per_line = _get_storybook_chars_per_line(style)
    first_height = _estimate_storybook_page_plan_height(first_plan, style, style.base_font_size)
    first_fill_ratio = first_height / max(page_height, 1e-6)
    if first_fill_ratio >= 0.8:
        return plans

    continuation_sentences = _split_storybook_sentences(second_plan.text_below)
    if len(continuation_sentences) < 3:
        return plans

    first_sentences = _split_storybook_sentences(first_plan.text_below)
    moved_any = False
    while len(continuation_sentences) > 2:
        candidate_first = " ".join(first_sentences + [continuation_sentences[0]]).strip()
        candidate_height = _estimate_wrapped_text_height(candidate_first, style, chars_per_line)
        reserved_without_below = _estimate_storybook_page_plan_height(
            StorybookPagePlan(
                chapter_title=first_plan.chapter_title,
                text_above=first_plan.text_above,
                image_path=first_plan.image_path,
                text_below="",
                title_on_page=first_plan.title_on_page,
                image_width=first_plan.image_width,
                vertical_offset=0.0,
            ),
            style,
            style.base_font_size,
        )
        if reserved_without_below + candidate_height > page_height:
            break
        first_sentences.append(continuation_sentences.pop(0))
        moved_any = True
        if (reserved_without_below + candidate_height) / max(page_height, 1e-6) >= 0.88:
            break

    if not moved_any:
        return plans

    first_plan.text_below = " ".join(first_sentences).strip()
    second_plan.text_below = " ".join(continuation_sentences).strip()
    return [plan for plan in plans if plan.text_above or plan.text_below or plan.image_path or plan.title_on_page]


def _rebalance_storybook_continuation_chain(
    plans: list[StorybookPagePlan],
    style: LayoutProfile,
    font_size: int,
    page_height: float,
) -> list[StorybookPagePlan]:
    if len(plans) < 2:
        return plans

    rebalanced = list(plans)
    changed = True
    while changed:
        changed = False
        for idx in range(len(rebalanced) - 1, 0, -1):
            current_plan = rebalanced[idx]
            previous_plan = rebalanced[idx - 1]
            if current_plan.image_path or previous_plan.image_path:
                continue
            if current_plan.title_on_page or previous_plan.title_on_page:
                continue
            if not current_plan.text_below or not previous_plan.text_below:
                continue

            current_sentences = _split_storybook_sentences(current_plan.text_below)
            previous_sentences = _split_storybook_sentences(previous_plan.text_below)
            if len(current_sentences) != 1 or len(previous_sentences) < 2:
                continue

            merged_text = " ".join(previous_sentences + current_sentences).strip()
            merged_height = _estimate_storybook_page_plan_height(
                StorybookPagePlan(
                    chapter_title=previous_plan.chapter_title,
                    text_above="",
                    image_path=None,
                    text_below=merged_text,
                    title_on_page=False,
                    image_width=None,
                    vertical_offset=0.0,
                    scene_class=previous_plan.scene_class,
                    page_style=previous_plan.page_style,
                ),
                style,
                font_size,
            )
            if merged_height <= page_height * 1.04:
                previous_plan.text_below = merged_text
                current_plan.text_below = ""
                changed = True

        if changed:
            rebalanced = [
                plan
                for plan in rebalanced
                if plan.text_above or plan.text_below or plan.image_path or plan.title_on_page
            ]

    return rebalanced


def _estimate_storybook_page_plan_height(plan: StorybookPagePlan, style: LayoutProfile, font_size: int) -> float:
    chars_per_line = _get_storybook_chars_per_line(style)
    total = 0.0
    if plan.title_on_page:
        total += max(9.0, float(style.line_height) + 2.0)
        total += max(2, int(style.heading_spacing) - 1)
    total += _estimate_wrapped_text_height(plan.text_above, style, chars_per_line)
    if plan.image_path and plan.image_width:
        total += _estimate_image_height(plan.image_path, plan.image_width) + int(style.image_spacing)
    total += _estimate_wrapped_text_height(plan.text_below, style, chars_per_line)
    return total


def _build_storybook_page_plan_for_block(
    block: StoryChapterBlock,
    style: LayoutProfile,
    font_size: int,
    page_width: float,
    page_height: float,
    image_width: int = 0,
) -> list[StorybookPagePlan]:
    effective_width = image_width if image_width > 0 else page_width
    effective_width = min(effective_width, int(style.image_max_width), page_width)
    rebalanced_block = _rebalance_storybook_block_for_height(block, style, font_size, effective_width, page_height)
    scene_class = _classify_storybook_scene(rebalanced_block)

    image_path = rebalanced_block.image_paths[0] if rebalanced_block.image_paths else None
    chars_per_line = _get_storybook_chars_per_line(style)
    reserved_text_height = 0.0
    reserved_text_height += max(9.0, float(style.line_height) + 2.0)
    reserved_text_height += max(2, int(style.heading_spacing) - 1)
    reserved_text_height += _estimate_wrapped_text_height(rebalanced_block.text_above, style, chars_per_line)
    planned_image_width = _select_storybook_image_width(
        image_path,
        float(effective_width),
        style,
        page_height,
        reserved_text_height,
        scene_class=scene_class,
        page_style="hero" if scene_class == "hero" and image_path else "chapter-opening",
    )

    first_plan = StorybookPagePlan(
        chapter_title=rebalanced_block.chapter_title,
        text_above=rebalanced_block.text_above,
        image_path=image_path,
        text_below="",
        title_on_page=True,
        image_width=planned_image_width,
        scene_class=scene_class,
    )
    first_plan.page_style = _determine_storybook_page_style(scene_class, bool(image_path), True, False)

    reserved_height = _estimate_storybook_page_plan_height(first_plan, style, font_size)
    image_page_safety_margin = _storybook_image_page_text_safety_margin(style) if first_plan.image_path else 0.0
    available_below_height = max(0.0, page_height - reserved_height - image_page_safety_margin)
    first_below, remaining_below = _split_storybook_text_to_fit_height(
        rebalanced_block.text_below,
        style,
        available_below_height,
    )
    if not first_below and remaining_below and first_plan.image_path and first_plan.image_width:
        base_reserved_height = _estimate_storybook_page_plan_height(
            StorybookPagePlan(
                chapter_title=first_plan.chapter_title,
                text_above=first_plan.text_above,
                image_path=first_plan.image_path,
                text_below="",
                title_on_page=first_plan.title_on_page,
                image_width=None,
                vertical_offset=0.0,
            ),
            style,
            font_size,
        )
        adjusted_width = _ensure_storybook_text_below_room(
            first_plan.image_path,
            first_plan.image_width,
            rebalanced_block.text_below,
            style,
            page_height,
            base_reserved_height,
        )
        if adjusted_width and adjusted_width < first_plan.image_width:
            first_plan.image_width = adjusted_width
            reserved_height = _estimate_storybook_page_plan_height(first_plan, style, font_size)
            available_below_height = max(0.0, page_height - reserved_height - image_page_safety_margin)
            first_below, remaining_below = _split_storybook_text_to_fit_height(
                rebalanced_block.text_below,
                style,
                available_below_height,
            )
    if not first_below and remaining_below and first_plan.image_path:
        first_below, remaining_below = _rebalance_storybook_first_page_text(
            first_plan,
            rebalanced_block.text_below,
            style,
            font_size,
            page_height,
        )
    first_plan.text_below = first_below
    first_below, remaining_below = _stabilize_storybook_first_page_split(
        first_plan,
        remaining_below,
        style,
        font_size,
        page_height,
    )
    first_plan.text_below = first_below

    plans = [first_plan]
    remaining_text = remaining_below.strip()
    while remaining_text:
        continuation_text, overflow_text = _split_storybook_text_to_fit_height(
            remaining_text,
            style,
            available_height=page_height,
            min_sentences_top=2,
        )
        if not continuation_text:
            continuation_text = remaining_text
            overflow_text = ""
        plans.append(
            StorybookPagePlan(
                chapter_title=rebalanced_block.chapter_title,
                text_above="",
                image_path=None,
                text_below=continuation_text,
                title_on_page=False,
                image_width=None,
                scene_class=scene_class,
                page_style=_determine_storybook_page_style(scene_class, False, False, True),
            )
        )
        remaining_text = overflow_text.strip()

    plans = _rebalance_storybook_plans(plans, style, page_height)
    plans = _rebalance_storybook_continuation_chain(plans, style, font_size, page_height)
    for plan in plans:
        plan_height = _estimate_storybook_page_plan_height(plan, style, font_size)
        plan.vertical_offset = _compute_storybook_vertical_offset(plan_height, page_height, bool(plan.image_path))

    return plans


def _build_storybook_layout_plan(
    title: str,
    chapters: list[StoryChapterBlock],
    style: LayoutProfile,
    font_size: int,
    page_width: float,
    page_height: float,
    image_width: int = 0,
) -> dict[str, object]:
    chapter_plans: list[list[StorybookPagePlan]] = []
    for block in chapters:
        chapter_plans.append(
            _build_storybook_page_plan_for_block(
                block,
                style,
                font_size,
                page_width=page_width,
                page_height=page_height,
                image_width=image_width,
            )
        )

    return {"title": title, "chapters": chapter_plans}


def _parse_storybook_blocks(markdown_text: str) -> tuple[str, list[StoryChapterBlock], list[str]]:
    lines = str(markdown_text or "").split("\n")
    title = ""
    intro_lines: list[str] = []
    chapters: list[StoryChapterBlock] = []
    current_title = ""
    current_lines: list[str] = []
    seen_chapter = False

    def _flush_current() -> None:
        nonlocal current_title, current_lines, chapters
        if not current_title:
            return
        image_paths: list[str] = []
        text_segments: list[str] = []
        seen_image = False
        above_segments: list[str] = []
        below_segments: list[str] = []
        for raw_line in current_lines:
            stripped = raw_line.strip()
            if not stripped:
                if not seen_image:
                    above_segments.append("")
                else:
                    below_segments.append("")
                continue
            image_matches = list(_MARKDOWN_IMAGE_RE.finditer(stripped))
            if image_matches:
                for match in image_matches:
                    resolved = _resolve_markdown_image_path(match.group(1))
                    if resolved:
                        image_paths.append(resolved)
                cleaned = _MARKDOWN_IMAGE_RE.sub("", stripped).strip()
                seen_image = True
                if cleaned:
                    below_segments.append(cleaned)
                continue
            if not seen_image:
                above_segments.append(stripped)
            else:
                below_segments.append(stripped)
        raw_above = "\n".join(line for line in above_segments).strip()
        raw_below = "\n".join(line for line in below_segments).strip()
        text_above, text_below = _build_storybook_text_parts(raw_above, raw_below)
        chapters.append(
            StoryChapterBlock(
                chapter_title=current_title,
                text_above=text_above,
                image_paths=image_paths,
                text_below=text_below,
            )
        )
        current_title = ""
        current_lines = []

    for raw_line in lines:
        stripped = raw_line.strip()
        if stripped.startswith("# ") and not seen_chapter and not title:
            title = stripped[2:].strip()
            continue
        if stripped.startswith("## "):
            seen_chapter = True
            _flush_current()
            current_title = stripped[3:].strip()
            current_lines = []
            continue
        if current_title:
            current_lines.append(raw_line)
        elif stripped:
            intro_lines.append(stripped)

    _flush_current()
    return title, chapters, intro_lines


def _estimate_storybook_block_height(block: StoryChapterBlock, style: LayoutProfile, font_size: int, image_width: float) -> float:
    chars_per_line = 75 if style.base_font_size >= 15 else 95
    heading_height = max(9.0, float(style.line_height) + 2.0)
    heading_spacing = max(2, int(style.heading_spacing) - 1)
    total = heading_height + heading_spacing
    total += _estimate_wrapped_text_height(block.text_above, style, chars_per_line)
    if block.image_paths:
        total += _estimate_image_height(block.image_paths[0], image_width) + int(style.image_spacing)
    total += _estimate_wrapped_text_height(block.text_below, style, chars_per_line)
    return total


def _infer_layout_profile(source_prompt: str, content: str) -> str:
    text = f"{str(source_prompt or '')} {str(content or '')}".lower()
    profile_keywords = {
        "bilderbuch": ["kinder", "kindergeschichte", "märchen", "maerchen", "bilderbuch", "häschen", "haeschen"],
        "praesentation": ["präsentation", "praesentation", "folien", "slide", "pitch", "agenda"],
        "magazin": ["magazin", "blog", "artikel", "reportage", "feature"],
        "bericht": ["bericht", "zusammenfassung", "analyse", "dokumentation", "protokoll"],
    }

    scores = {profile: 0 for profile in profile_keywords}
    for profile, keywords in profile_keywords.items():
        for keyword in keywords:
            if keyword in text:
                scores[profile] += 1

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    if not ranked or ranked[0][1] <= 0:
        return _DEFAULT_LAYOUT_PROFILE

    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        logger.info(
            "LAYOUT-AUTO: Uneindeutige Signale (%s vs %s). Fallback auf '%s'.",
            ranked[0][0],
            ranked[1][0],
            _DEFAULT_LAYOUT_PROFILE,
        )
        return _DEFAULT_LAYOUT_PROFILE
    return ranked[0][0]


def _resolve_layout_profile(layout_profile: str, source_prompt: str, content: str) -> str:
    normalized = _normalize_layout_profile(layout_profile)
    if normalized == "auto" or not normalized:
        return _infer_layout_profile(source_prompt=source_prompt, content=content)
    if normalized in _LAYOUT_PROFILES:
        return normalized
    logger.warning("Unbekanntes layout_profile '%s'. Fallback auf '%s'.", layout_profile, _DEFAULT_LAYOUT_PROFILE)
    return _DEFAULT_LAYOUT_PROFILE


def _split_sentences_preserving_abbreviations(text: str) -> list[str]:
    protected = re.sub(r"\bca\.\s+(?=\d)", "ca<ABBR> ", str(text or ""), flags=re.IGNORECASE)
    parts = [part.strip(" ,") for part in _SENTENCE_SPLIT_RE.split(protected) if part.strip(" ,")]
    return [part.replace("ca<ABBR>", "ca.").strip() for part in parts]


class MarkdownSyntaxError(ValueError):
    """Raised when markdown input is structurally invalid for PDF rendering."""


def _execution_time_ms(started_at: float) -> float:
    return round((time.perf_counter() - started_at) * 1000, 2)


def _sanitize_filename(filename: str) -> str:
    value = str(filename or "").strip()
    if not value:
        return "output.pdf"
    if not value.lower().endswith(".pdf"):
        value += ".pdf"
    sanitized = "".join(ch for ch in value if ch.isalnum() or ch in (" ", ".", "_", "-"))
    sanitized = sanitized.strip().strip(".")
    return sanitized or "output.pdf"


def _validate_markdown_syntax(content: str) -> None:
    text = str(content or "")
    if text.count("[") != text.count("]"):
        raise MarkdownSyntaxError("Unbalancierte eckige Klammern im Markdown.")
    if text.count("(") != text.count(")"):
        raise MarkdownSyntaxError("Unbalancierte runde Klammern im Markdown.")


def _normalize_pdf_content(content: str, filename: str) -> str:
    raw = str(content or "")
    if not raw.strip():
        return ""

    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"```(?:markdown)?", "", text, flags=re.IGNORECASE)
    lines = [line.rstrip() for line in text.split("\n")]

    cleaned_lines = []
    for line in lines:
        if _AGENT_SIGNATURE_RE.match(line):
            continue
        cleaned_lines.append(line)

    cleaned_text = "\n".join(cleaned_lines).strip()
    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)
    if not cleaned_text:
        return ""

    has_markdown_structure = bool(re.search(r"^\s*(#{1,3}\s+|[-*]\s+)", cleaned_text, flags=re.MULTILINE))
    if has_markdown_structure:
        return cleaned_text

    normalized_inline = re.sub(r"\s+", " ", cleaned_text).strip()
    if normalized_inline.lower().startswith("fakten:"):
        normalized_inline = normalized_inline[7:].strip()

    title = Path(str(filename or "output.pdf")).stem.replace("_", " ").replace("-", " ").strip().title()
    sentences = _split_sentences_preserving_abbreviations(normalized_inline)
    if not sentences:
        return f"# {title}\n\n{normalized_inline}" if title else normalized_inline

    keyword_markers = ("hauptstadt", "einwohner", "entfernung", "distanz", "route", "maps", "km")
    fact_lines = [sentence for sentence in sentences if any(marker in sentence.lower() for marker in keyword_markers)]
    if not fact_lines:
        if title:
            return f"# {title}\n\n{normalized_inline}"
        return normalized_inline

    unique_fact_lines = []
    seen = set()
    for sentence in fact_lines:
        normalized_key = sentence.lower().strip()
        if normalized_key in seen:
            continue
        seen.add(normalized_key)
        unique_fact_lines.append(sentence)

    markdown_lines = []
    if title:
        markdown_lines.append(f"# {title}")
        markdown_lines.append("")
    markdown_lines.append("## Fakten")
    markdown_lines.extend(f"- {entry}" for entry in unique_fact_lines)
    return "\n".join(markdown_lines).strip()


def _resolve_markdown_image_path(raw_path: str) -> Optional[str]:
    candidate = str(raw_path or "").strip().strip("\"'")
    if not candidate:
        return None

    parsed = urlparse(candidate)
    candidate_path = candidate
    if parsed.scheme in {"http", "https"}:
        candidate_path = parsed.path or ""

    normalized = candidate_path.replace("\\", "/")
    if normalized.startswith("/user_images/"):
        relative = normalized[len("/user_images/"):].lstrip("/")
        if relative:
            absolute = os.path.join(get_images_dir(), relative.replace("/", os.sep))
            if os.path.exists(absolute):
                return absolute

    if os.path.exists(candidate):
        return candidate

    return None


def _extract_first_image_path_and_clean_content(content: str) -> tuple[Optional[str], str]:
    text = str(content or "")
    if not text:
        return None, text

    image_path: Optional[str] = None

    def _replace(match: re.Match[str]) -> str:
        nonlocal image_path
        raw_ref = match.group(1)
        if image_path is None:
            image_path = _resolve_markdown_image_path(raw_ref)
        return ""

    cleaned = _MARKDOWN_IMAGE_RE.sub(_replace, text)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return image_path, cleaned


def _extract_markdown_image_paths(content: str) -> list[str]:
    text = str(content or "")
    if not text:
        return []

    resolved_paths: list[str] = []
    seen = set()
    for raw_ref in _MARKDOWN_IMAGE_RE.findall(text):
        resolved = _resolve_markdown_image_path(raw_ref)
        if not resolved:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        resolved_paths.append(resolved)
    return resolved_paths


def _is_path_inside_root(candidate_abs: str, root_abs: str) -> bool:
    norm_root = os.path.normcase(root_abs.rstrip("\\/"))
    norm_candidate = os.path.normcase(candidate_abs)
    if norm_candidate == norm_root:
        return True
    return norm_candidate.startswith(norm_root + os.sep)


def _get_configured_storage_root() -> Path:
    env_root = str(os.getenv("JANUS_STORAGE_ROOT") or os.getenv("STORAGE_ROOT") or "").strip()
    if env_root:
        return Path(os.path.abspath(env_root))

    config_data = load_config_data()
    config_root = str(
        config_data.get("JANUS_STORAGE_ROOT")
        or config_data.get("STORAGE_ROOT")
        or config_data.get("storage_root")
        or ""
    ).strip()
    if config_root:
        return Path(os.path.abspath(config_root))

    return Path(os.path.abspath(os.path.join(get_app_data_dir(), "storage")))


def _normalize_location_for_root_join(location: str) -> str:
    raw_location = str(location or "").strip()
    if not raw_location or raw_location.lower() in {"workspace", ".", "./", "storage"}:
        return ""

    normalized = raw_location.replace("\\", "/")
    if len(normalized) >= 2 and normalized[1] == ":":
        normalized = normalized[2:]
    normalized = normalized.lstrip("/")
    if normalized.lower().startswith("storage/"):
        normalized = normalized.split("/", 1)[1] if "/" in normalized else ""
    return normalized


def get_secure_absolute_path(location: str) -> Path:
    raw_location = str(location or "").strip()
    normalized_location = raw_location.lower()

    base_root: str
    location_fragment = ""
    if normalized_location == "documents":
        base_root = os.path.abspath(os.path.join(os.path.expanduser("~"), "Documents", "JanusPDFs"))
        logger.info("Resolved user-friendly location 'Documents' to %s", base_root)
    elif normalized_location == "desktop":
        base_root = os.path.abspath(os.path.join(os.path.expanduser("~"), "Desktop"))
        logger.info("Resolved user-friendly location 'Desktop' to %s", base_root)
    else:
        base_root = os.path.abspath(str(_get_configured_storage_root()))
        if raw_location:
            candidate_path = Path(raw_location)
            if candidate_path.is_absolute() or (len(raw_location) >= 2 and raw_location[1] == ":"):
                raise PermissionError(f"Absoluter Zielpfad ist nicht erlaubt: '{raw_location}'")
        location_fragment = _normalize_location_for_root_join(raw_location)

    final_dir = os.path.abspath(
        os.path.join(base_root, location_fragment) if location_fragment else base_root
    )

    try:
        if os.path.commonpath([base_root, final_dir]) != base_root:
            raise PermissionError(f"Pfad außerhalb des konfigurierten Storage-Roots: '{location}'")
    except ValueError:
        raise PermissionError(f"Pfad außerhalb des konfigurierten Storage-Roots: '{location}'")

    if not _is_path_inside_root(final_dir, base_root):
        raise PermissionError(f"Pfad außerhalb des konfigurierten Storage-Roots: '{location}'")
    return Path(final_dir)


def _get_allowed_root_for_location(location: str) -> str:
    normalized_location = str(location or "").strip().lower()
    if normalized_location == "documents":
        return os.path.abspath(os.path.join(os.path.expanduser("~"), "Documents"))
    if normalized_location == "desktop":
        return os.path.abspath(os.path.join(os.path.expanduser("~"), "Desktop"))
    return os.path.abspath(str(_get_configured_storage_root()))


class PDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVu", "I", 8)
        self.cell(0, 10, f"Seite {self.page_no()}", 0, 0, "C")

    def _render_storybook_title_page(self, title: str, style: LayoutProfile, font_size: int) -> None:
        line_height = float(style.line_height)
        heading_alignment = style.heading_alignment or "C"
        self.set_font("DejaVu", "B", max(10, int(round(font_size * float(style.heading_scales.get("h1", 2.0))))) )
        self.set_text_color(*style.heading_color)
        self.ln(80)
        self.multi_cell(0, max(10, line_height + 3), title.strip(), 0, heading_alignment)
        self.ln(10)
        self.set_font("DejaVu", "", max(11, font_size))
        self.set_text_color(*style.text_color)
        self.multi_cell(0, line_height, "Ein Bilderbuch", 0, heading_alignment)
        self.add_page()

    def _render_storybook_intro(self, intro_lines: list[str], style: LayoutProfile, font_size: int) -> None:
        if not intro_lines:
            return
        self.set_font("DejaVu", "", font_size)
        self.set_text_color(*style.text_color)
        for line in intro_lines:
            stripped = str(line or "").strip()
            if not stripped:
                self.ln(max(3, int(style.paragraph_spacing) + 1))
                continue
            self.multi_cell(0, float(style.line_height), stripped, 0, style.text_alignment or "L")
            self.ln(int(style.paragraph_spacing))

    def _render_storybook_page_plan(self, plan: StorybookPagePlan, style: LayoutProfile, font_size: int) -> None:
        line_height = float(style.line_height)
        heading_alignment = style.heading_alignment or "C"
        text_alignment = style.text_alignment or "L"
        body_font_size = font_size
        if plan.page_style == "hero":
            body_font_size = max(font_size, int(round(font_size * 1.03)))
        elif plan.page_style in {"continuation", "continuation-soft"}:
            body_font_size = max(12, int(round(font_size * 0.94)))
        if plan.vertical_offset > 0:
            self.set_y(self.get_y() + plan.vertical_offset)

        if plan.title_on_page:
            heading_scale = float(style.heading_scales.get("h2", 1.5))
            if plan.page_style == "hero":
                heading_scale += 0.18
            self.set_font("DejaVu", "B", max(10, int(round(font_size * heading_scale))) )
            self.set_text_color(*style.heading_color)
            self.multi_cell(0, max(9, line_height + 2), plan.chapter_title.strip(), 0, heading_alignment)
            self.ln(max(2, int(style.heading_spacing) - 1))

        if plan.text_above:
            self.set_font("DejaVu", "", body_font_size)
            self.set_text_color(*style.text_color)
            self.multi_cell(0, line_height, plan.text_above.strip(), 0, text_alignment)
            extra_spacing = 2 if plan.page_style == "hero" else 0
            self.ln(int(style.paragraph_spacing) + extra_spacing)

        if plan.image_path:
            image_path = plan.image_path
            if image_path and os.path.exists(image_path):
                render_image_width = float(plan.image_width or min(self.w - 2 * self.l_margin, int(style.image_max_width)))
                x_pos = self.l_margin
                if style.image_alignment.lower() == "center":
                    x_pos = max(self.l_margin, (self.w - render_image_width) / 2)
                self.image(image_path, x=x_pos, y=None, w=render_image_width)
                image_spacing = int(style.image_spacing)
                if plan.page_style == "hero":
                    image_spacing += 2
                elif plan.page_style == "continuation-soft":
                    image_spacing = max(6, image_spacing - 2)
                self.ln(image_spacing)

        if plan.text_below:
            self.set_font("DejaVu", "", body_font_size)
            self.set_text_color(*style.text_color)
            self.multi_cell(0, line_height, plan.text_below.strip(), 0, text_alignment)
            end_spacing = int(style.paragraph_spacing)
            if plan.page_style in {"continuation", "continuation-soft"}:
                end_spacing = max(4, end_spacing - 1)
            self.ln(end_spacing)

    def _render_storybook_markdown(self, markdown_text: str, style: LayoutProfile, font_size: int, image_width: int = 0) -> None:
        title, chapters, intro_lines = _parse_storybook_blocks(markdown_text)
        page_width = self.w - 2 * self.l_margin
        page_height = getattr(self, "page_break_trigger", self.h - self.b_margin) - self.t_margin
        layout_plan = _build_storybook_layout_plan(
            title,
            chapters,
            style,
            font_size,
            page_width=page_width,
            page_height=page_height,
            image_width=image_width,
        )
        if title and style.title_page:
            self._render_storybook_title_page(title, style, font_size)
        elif title:
            self.set_font("DejaVu", "B", max(10, int(round(font_size * float(style.heading_scales.get("h1", 2.0))))) )
            self.set_text_color(*style.heading_color)
            self.multi_cell(0, max(10, float(style.line_height) + 3), title.strip(), 0, style.heading_alignment or "C")
            self.ln(int(style.heading_spacing))
        self._render_storybook_intro(intro_lines, style, font_size)
        chapter_plans = layout_plan.get("chapters", [])
        for chapter_pages in chapter_plans:
            for page_index, plan in enumerate(chapter_pages):
                if self.page_no() > 1 and self.get_y() > (self.t_margin + 5):
                    self.add_page()
                elif page_index > 0:
                    self.add_page()
                self._render_storybook_page_plan(plan, style, font_size)

    def add_markdown_text(self, markdown_text: str, font_size: int, image_width: int = 0, layout_profile: str = _DEFAULT_LAYOUT_PROFILE):
        lines = markdown_text.split("\n")
        style = _LAYOUT_PROFILES.get(layout_profile, _LAYOUT_PROFILES[_DEFAULT_LAYOUT_PROFILE])
        self.set_font("DejaVu", "", font_size)
        line_height = float(style.line_height)
        heading_alignment = style.heading_alignment or "L"
        text_alignment = style.text_alignment or "L"
        title_page_pending = style.title_page
        rendered_non_title_block = False

        page_break_trigger = getattr(self, "page_break_trigger", self.h - self.b_margin)

        if layout_profile == "bilderbuch":
            self._render_storybook_markdown(markdown_text, style, font_size, image_width=image_width)
            self.set_font("DejaVu", "", font_size)
            return

        for idx, line in enumerate(lines):
            line = line.strip()

            image_matches = list(_MARKDOWN_IMAGE_RE.finditer(line))
            if image_matches:
                for match in image_matches:
                    image_path = _resolve_markdown_image_path(match.group(1))
                    if not image_path or not os.path.exists(image_path):
                        continue

                    page_width = self.w - 2 * self.l_margin
                    effective_width = image_width if image_width > 0 else page_width
                    effective_width = min(effective_width, int(style.image_max_width))
                    if effective_width > page_width:
                        effective_width = page_width

                    available_height = page_break_trigger - self.get_y()
                    future_height = _estimate_future_text_height(lines, idx + 1, style)
                    estimated_height = _estimate_image_height(image_path, effective_width)

                    total_needed = estimated_height + style.image_spacing + future_height

                    if total_needed > available_height:
                        desired_height = available_height - future_height - style.image_spacing
                        if desired_height > (estimated_height * 0.85):
                            scale = desired_height / max(estimated_height, 1e-6)
                            effective_width = max(60, int(effective_width * scale))
                            estimated_height = _estimate_image_height(image_path, effective_width)
                        else:
                            self.add_page()
                            available_height = page_break_trigger - self.get_y()
                            leftover = available_height - (estimated_height + style.image_spacing + future_height)
                            if leftover > 20:
                                self.set_y(self.get_y() + (leftover / 3))

                    x_pos = self.l_margin
                    if style.image_alignment.lower() == "center":
                        x_pos = max(self.l_margin, (self.w - effective_width) / 2)

                    self.image(image_path, x=x_pos, y=None, w=effective_width)
                    self.ln(int(style.image_spacing))

                line = _MARKDOWN_IMAGE_RE.sub("", line).strip()
                if not line:
                    self.ln(int(style.paragraph_spacing))
                    continue

            if line.startswith("# "):
                self.set_font("DejaVu", "B", max(10, int(round(font_size * float(style.heading_scales.get("h1", 2.0))))) )
                self.set_text_color(*style.heading_color)
                if title_page_pending:
                    self.ln(80)
                self.multi_cell(0, max(10, line_height + 3), line[2:].strip(), 0, heading_alignment)
                if title_page_pending:
                    self.ln(10)
                    self.set_font("DejaVu", "", max(11, font_size))
                    self.set_text_color(*style.text_color)
                    self.multi_cell(0, line_height, "Ein Bilderbuch", 0, heading_alignment)
                    self.add_page()
                    title_page_pending = False
                self.ln(int(style.heading_spacing))

            elif line.startswith("## "):
                if style.chapter_page_break and self.get_y() > 30 and rendered_non_title_block:
                    self.add_page()

                self.set_font("DejaVu", "B", max(10, int(round(font_size * float(style.heading_scales.get("h2", 1.5))))) )
                self.set_text_color(*style.heading_color)
                self.multi_cell(0, max(9, line_height + 2), line[3:].strip(), 0, heading_alignment)
                self.ln(max(2, int(style.heading_spacing) - 1))
                rendered_non_title_block = True

            elif line.startswith("### "):
                self.set_font("DejaVu", "B", max(10, int(round(font_size * float(style.heading_scales.get("h3", 1.3))))) )
                self.set_text_color(*style.heading_color)
                self.multi_cell(0, max(8, line_height + 1), line[4:].strip(), 0, heading_alignment)
                self.ln(1)

            elif line.strip().startswith(("* ", "- ")):
                self.set_font("DejaVu", "", font_size)
                self.set_text_color(*style.text_color)
                self.cell(5)
                self.multi_cell(0, line_height, f"• {line.strip()[2:]}", 0, text_alignment)
                self.ln(1)

            elif line:
                chars_per_line = 75 if style.base_font_size >= 15 else 95
                estimated_lines = max(1, len(line) // chars_per_line + 1)
                needed_height = estimated_lines * line_height

                if (self.get_y() + needed_height) > page_break_trigger:
                    self.add_page()

                self.set_font("DejaVu", "", font_size)
                self.set_text_color(*style.text_color)
                self.multi_cell(0, line_height, line, 0, text_alignment)
                self.ln(int(style.paragraph_spacing))
                rendered_non_title_block = True

            else:
                self.ln(max(3, int(style.paragraph_spacing) + 1))
        self.set_font("DejaVu", "", font_size)

def register_and_index_file(filename: str, full_path: str, db: Session, audit_status: str = "new") -> Optional[int]:
    if not db:
        logger.warning("Kein DB-Session-Objekt verfügbar, Indexierung übersprungen.")
        return None

    try:
        file_size = os.path.getsize(full_path) if os.path.exists(full_path) else 0
        from backend.data.models import Document

        existing = db.query(Document).filter(Document.filename == filename).first()
        if existing:
            existing.file_path = full_path
            existing.file_size = file_size
            existing.file_type = "application/pdf"
            existing.error_message = None
            existing.audit_status = audit_status
            db.commit()
            db.refresh(existing)
            doc_id = existing.id
        else:
            new_doc = Document(
                filename=filename,
                file_path=full_path,
                file_size=file_size,
                audit_status=audit_status,
            )
            db.add(new_doc)
            db.commit()
            db.refresh(new_doc)
            doc_id = new_doc.id

        rag_manager.index_document(db, doc_id)
        logger.info(f"PDF '{filename}' wurde in der Datenbank registriert (ID: {doc_id}).")
        return doc_id
    except Exception as index_error:
        logger.error(
            f"Fehler bei der Registrierung der PDF '{filename}': {index_error}",
            exc_info=True,
        )
        db.rollback()
        return None


def create_pdf(
    content: str,
    filename: str,
    location: str = "workspace",
    image_path: Optional[str] = None,
    font_size: int = 11,
    image_width: int = 0,
    dry_run: bool = False,
    last_image_path: Optional[str] = None,
    layout_profile: str = "auto",
    source_prompt: str = "",
    db: Optional[Session] = None,
) -> ToolResultV1:
    """
    Kombiniert vorhandenen Text und optional das ZULETZT im Chatverlauf erstellte Bild zu einer PDF-Datei.
    """
    started_at = time.perf_counter()
    selected_layout = _resolve_layout_profile(layout_profile=layout_profile, source_prompt=source_prompt, content=content)
    profile_style = _LAYOUT_PROFILES.get(selected_layout, _LAYOUT_PROFILES[_DEFAULT_LAYOUT_PROFILE])
    effective_font_size = font_size
    if font_size == 11:
        effective_font_size = int(profile_style.base_font_size)

    markdown_image_paths = _extract_markdown_image_paths(content)

    resolved_explicit_image_path: Optional[str] = None
    if image_path:
        resolved_explicit_image_path = _resolve_markdown_image_path(image_path)
        if not resolved_explicit_image_path and os.path.exists(image_path):
            resolved_explicit_image_path = image_path
    image_path = resolved_explicit_image_path

    # Reihenfolge: explizit gesetzter image_path > letztes Bild aus Kontext (nur wenn kein Inline-Markdownbild vorhanden ist)
    if not image_path and not markdown_image_paths and last_image_path and os.path.exists(last_image_path):
        image_path = last_image_path

    def _error(code: str, message: str, details: Optional[str] = None) -> ToolResultV1:
        err_details = {"detail": details} if details else None
        return ToolResultV1(
            status="error",
            data={},
            message=message,
            error=ToolErrorDetails(code=code, message=message, details=err_details),
            metadata={"execution_time_ms": _execution_time_ms(started_at)},
        )

    try:
        logger.info("PDF-Erstellung gestartet mit folgenden Parametern:")
        logger.info(f"  - Dateiname: {filename}")
        logger.info(f"  - Speicherort: {location}")
        logger.info(f"  - Schriftgröße: {font_size}pt")
        logger.info(f"  - Bildpfad: {image_path}")
        logger.info(f"  - Bildbreite: {image_width}mm")
        logger.info(f"  - Layout-Profil: {selected_layout}")
        logger.info(f"  - Dry-Run: {dry_run}")

        valid_filename = _sanitize_filename(filename)
        normalized_content = _normalize_pdf_content(content, valid_filename)
        _validate_markdown_syntax(normalized_content)
        output_dir = get_secure_absolute_path(location)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / valid_filename

        configured_root_abs = _get_allowed_root_for_location(location)
        final_path_abs = os.path.abspath(str(output_path))
        try:
            if os.path.commonpath([configured_root_abs, final_path_abs]) != configured_root_abs:
                raise PermissionError(f"Pfad außerhalb des konfigurierten Storage-Roots: '{final_path_abs}'")
        except ValueError:
            raise PermissionError(f"Pfad außerhalb des konfigurierten Storage-Roots: '{final_path_abs}'")
        if not _is_path_inside_root(final_path_abs, configured_root_abs):
            raise PermissionError(f"Pfad außerhalb des konfigurierten Storage-Roots: '{final_path_abs}'")

        logger.info(f"Speichere PDF unter: {output_path}")

        pdf = PDF()
        if selected_layout == "bilderbuch":
            pdf.set_margins(left=25, top=25, right=25)
            pdf.set_auto_page_break(auto=True, margin=25)
        else:
            pdf.set_margins(left=15, top=15, right=15)
            pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_font("DejaVu", "", FONT_PATH, uni=True)
        pdf.add_font("DejaVu", "B", FONT_PATH, uni=True)
        pdf.add_font("DejaVu", "I", FONT_PATH, uni=True)
        pdf.add_page()

        if image_path and os.path.exists(image_path) and not markdown_image_paths:
            logger.info(f"Füge Bild hinzu: {image_path}")

            page_width = pdf.w - 2 * pdf.l_margin
            effective_width = image_width if image_width > 0 else page_width
            effective_width = min(effective_width, int(profile_style.image_max_width))
            if effective_width > page_width:
                effective_width = page_width

            x_pos = pdf.l_margin
            if profile_style.image_alignment.lower() == "center":
                x_pos = max(pdf.l_margin, (pdf.w - effective_width) / 2)
            pdf.image(image_path, x=x_pos, y=None, w=effective_width)
            pdf.ln(10)

        pdf.add_markdown_text(
            normalized_content,
            effective_font_size,
            image_width=image_width,
            layout_profile=selected_layout,
        )

        if dry_run:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                temp_path = Path(tmp_file.name)
            try:
                pdf.output(str(temp_path))
                preview_bytes = temp_path.read_bytes()
                preview_b64 = base64.b64encode(preview_bytes).decode("ascii")
                return ToolResultV1(
                    status="dry_run_success",
                    data={
                        "preview_url": f"data:application/pdf;base64,{preview_b64[:1200]}",
                        "filename": valid_filename,
                        "dry_run": True,
                    },
                    message="PDF-Vorschau (Dry-Run) erstellt.",
                    metadata={"execution_time_ms": _execution_time_ms(started_at)},
                )
            finally:
                try:
                    temp_path.unlink(missing_ok=True)
                except Exception:
                    pass

        output_result = pdf.output(str(output_path))
        if not output_path.exists() or output_path.stat().st_size <= 0:
            if isinstance(output_result, (bytes, bytearray)):
                output_path.write_bytes(bytes(output_result))
            elif isinstance(output_result, str):
                output_path.write_bytes(output_result.encode("latin-1", errors="ignore"))

        if not output_path.exists() or output_path.stat().st_size <= 0:
            raise OSError(f"PDF-Datei wurde nicht erfolgreich geschrieben: '{output_path}'")

        registered_id = None
        if db:
            registered_id = register_and_index_file(valid_filename, str(output_path), db)

        data = {
            "file_path": str(output_path),
            "ui_action": "refresh_documents",
            "document_id": registered_id,
        }
        return ToolResultV1(
            status="ok",
            data=data,
            message=f"PDF erstellt: {valid_filename}",
            metadata={"execution_time_ms": _execution_time_ms(started_at)},
        )

    except MarkdownSyntaxError as exc:
        return _error("MARKDOWN_PARSE_ERROR", "Markdown konnte nicht verarbeitet werden.", str(exc))
    except PermissionError as exc:
        return _error("WRITE_PERMISSION_DENIED", "Keine Schreibberechtigung für den Zielpfad.", str(exc))
    except OSError as exc:
        details = str(exc)
        if getattr(exc, "errno", None) == 28:
            return _error("DISK_FULL", "Nicht genügend Speicherplatz für die PDF-Erstellung.", details)
        return _error("WRITE_PERMISSION_DENIED", "Datei konnte nicht geschrieben werden.", details)
    except Exception as exc:
        logger.error("Fehler beim Erstellen der PDF mit fpdf2: %s", exc, exc_info=True)
        return _error("UNEXPECTED_ERROR", "Unerwarteter Fehler bei der PDF-Erstellung.", str(exc))


def create_pdf_from_markdown(
    content: str,
    filename: str,
    location: str = "workspace",
    image_path: Optional[str] = None,
    font_size: int = 11,
    image_width: int = 0,
    dry_run: bool = False,
    last_image_path: Optional[str] = None,
    layout_profile: str = "auto",
    source_prompt: str = "",
    db: Optional[Session] = None,
) -> ToolResultV1:
    return create_pdf(
        content=content,
        filename=filename,
        location=location,
        image_path=image_path,
        font_size=font_size,
        image_width=image_width,
        dry_run=dry_run,
        last_image_path=last_image_path,
        layout_profile=layout_profile,
        source_prompt=source_prompt,
        db=db,
    )


# --- Schema Definition ---
class CleanCreatePdfArgs(BaseModel):
    content: str = Field(
        ..., description="Der vollständige Textinhalt für die PDF (Markdown erlaubt)."
    )
    filename: str = Field(
        ...,
        description="Der Dateiname. WICHTIG: Der Parameter MUSS zwingend 'filename' heißen (NICHT 'file_name'). Endung muss .pdf sein.",
    )
    location: str = Field(
        "workspace",
        min_length=1,
        max_length=260,
        pattern=r"^[A-Za-z0-9_ .:\\/-]+$",
        description="Speicherort als sandboxed Pfad innerhalb erlaubter Workspaces.",
    )
    font_size: int = Field(default=11, ge=8, le=20, description="Die Schriftgröße.")
    image_width: int = Field(default=0, ge=0, le=800, description="Die gewünschte Breite des Bildes.")
    layout_profile: str = Field(
        default="auto",
        description="Layout-Profil: auto, bericht, bilderbuch, praesentation, magazin.",
    )
    source_prompt: str = Field(
        default="",
        description="Optional: ursprünglicher Nutzerprompt für bessere Auto-Layout-Auswahl.",
    )
    dry_run: bool = Field(False, description="Wenn true, nur Vorschau erzeugen und keine Datei schreiben.")
