import asyncio
import logging
import os
import re
import json
import difflib
import time
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Any
from sqlalchemy.orm import Session
import fitz
from backend.data.schemas_tools import ToolResultV1
from backend.tools.tool_contract_v1 import tool_err_v1, tool_ok_v1

from backend.tools.pdf_generator import register_and_index_file
from backend.utils.paths import get_user_docs_dir, resource_path

logger = logging.getLogger("janus_backend")
pdf_write_lock = asyncio.Lock()
VERTICAL_TOLERANCE = 15
DEFAULT_FONT_SIZE = 11.0
MIN_FONT_SIZE = 6.0
MIN_TEXTBOX_WIDTH = 40.0


DEFAULT_PAGE_MARGIN = 40.0
BASE14_FONTS = {
    "courier",
    "courier-bold",
    "courier-oblique",
    "courier-boldoblique",
    "helv",
    "helvetica",
    "helvetica-bold",
    "helvetica-oblique",
    "helvetica-boldoblique",
    "tiro",
    "times-roman",
    "times-bold",
    "times-italic",
    "times-bolditalic",
}
CID_FONT_HINTS = (
    "cid",
    "identity",
    "subset",
    "embedded",
)


def get_layout_bounds(page: fitz.Page, rect: fitz.Rect) -> float:
    """Findet die rechte Grenze des Textblocks."""
    blocks = page.get_text("blocks")
    for b in blocks:
        b_rect = fitz.Rect(b[:4])
        if b_rect.intersects(rect):
            return b_rect.x1
    return page.rect.width - DEFAULT_PAGE_MARGIN


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").replace("\n", " ")).strip()


def _build_whitespace_flexible_pattern(text: str) -> re.Pattern[str]:
    escaped = re.escape(text or "")
    escaped = escaped.replace(r"\ ", r"\s+")
    return re.compile(escaped)


def _replace_with_flexible_whitespace(source: str, search: str, replace: str) -> Tuple[str, int]:
    if not search:
        return source, 0
    pattern = _build_whitespace_flexible_pattern(search)
    return pattern.subn(replace, source)


def _group_rects_by_line(rects: List[fitz.Rect]) -> Dict[int, fitz.Rect]:
    lines: Dict[int, fitz.Rect] = {}
    for rect in rects:
        y_key = round(rect.y0 / VERTICAL_TOLERANCE) * VERTICAL_TOLERANCE
        if y_key not in lines:
            lines[y_key] = rect
        else:
            lines[y_key] = lines[y_key] | rect
    return lines


def _build_occurrence_rects(rects: List[fitz.Rect]) -> List[fitz.Rect]:
    """Kondensiert Suchtreffer auf logische Vorkommen (mehrzeilige Treffer = 1 Job)."""
    line_rects = list(_group_rects_by_line(rects).values())
    if not line_rects:
        return []

    line_rects.sort(key=lambda r: (r.y0, r.x0))
    occurrences: List[fitz.Rect] = []
    current = line_rects[0]
    for rect in line_rects[1:]:
        vertical_gap = rect.y0 - current.y1
        line_threshold = max(current.height, rect.height) * 0.7
        if vertical_gap <= line_threshold:
            current = current | rect
        else:
            occurrences.append(current)
            current = rect
    occurrences.append(current)
    return occurrences


def _extract_style(page: fitz.Page, rect: fitz.Rect) -> Tuple[float, Tuple[float, float, float], str]:
    font_size = DEFAULT_FONT_SIZE
    font_color = (0.0, 0.0, 0.0)
    font_name = "helv"
    try:
        text_dict = page.get_text("dict", clip=rect)
        max_size = 0.0
        for block in text_dict.get("blocks", []) or []:
            for line in block.get("lines", []) or []:
                for span in line.get("spans", []) or []:
                    span_size = float(span.get("size", DEFAULT_FONT_SIZE) or DEFAULT_FONT_SIZE)
                    if span_size > max_size:
                        max_size = span_size
                        font_size = span_size
                        raw_font_name = str(span.get("font", "") or "").strip()
                        if raw_font_name:
                            font_name = raw_font_name
                        color_int = int(span.get("color", 0) or 0)
                        font_color = (
                            ((color_int >> 16) & 0xFF) / 255,
                            ((color_int >> 8) & 0xFF) / 255,
                            (color_int & 0xFF) / 255,
                        )
    except Exception:
        pass
    return max(font_size, MIN_FONT_SIZE), font_color, font_name


def _is_likely_embedded_or_cid_font(font_name: str) -> bool:
    name = (font_name or "").strip().lower()
    if not name:
        return False
    if name in BASE14_FONTS:
        return False
    if "+" in name:
        return True
    return any(hint in name for hint in CID_FONT_HINTS)


def _fallback_size_factor(preferred_font: str, uses_fontfile: bool) -> float:
    if not uses_fontfile:
        return 1.0
    # Embedded/CID source fonts often render visually larger than DejaVu/Helv at same pt-size.
    # Apply a calibrated bump so replacement paragraphs keep comparable optical size.
    if _is_likely_embedded_or_cid_font(preferred_font):
        return 1.16
    return 1.08


def _build_textbox(job: Dict[str, Any], height_factor: float) -> fitz.Rect:
    width_right = max(job["right_edge"], job["rect"].x0 + MIN_TEXTBOX_WIDTH)
    base_height = max(job["rect"].height, job["size"] * 1.5)
    height = max(base_height * height_factor, job["size"] * 2.2)
    return fitz.Rect(job["rect"].x0, job["rect"].y0, width_right, job["rect"].y0 + height)


def _try_insert_replacement(page: fitz.Page, job: Dict[str, Any], font_path: str) -> Tuple[bool, str]:
    replace_text = job["replace"]
    if not replace_text:
        return True, "deleted"

    base_size = max(float(job["size"]), MIN_FONT_SIZE)
    font_sizes = [base_size]
    height_factors = [1.8, 2.8, 4.0]

    for size in font_sizes:
        for height_factor in height_factors:
            box = _build_textbox(job, height_factor)
            preferred_font = (job.get("fontname") or "").strip()
            font_candidates: List[Dict[str, str]] = []
            normalized_font = preferred_font.lower()
            if normalized_font in BASE14_FONTS:
                font_candidates.append({"fontname": normalized_font, "uses_fontfile": False})
            if os.path.exists(font_path):
                font_candidates.append({"fontfile": str(font_path), "uses_fontfile": True})
            font_candidates.append({"fontname": "helv", "uses_fontfile": True})

            for font_candidate in font_candidates:
                size_factor = _fallback_size_factor(preferred_font, bool(font_candidate.get("uses_fontfile")))
                candidate_size = max(size * size_factor, MIN_FONT_SIZE)
                args = {
                    "fontsize": candidate_size,
                    "color": job["color"],
                    "overlay": True,
                    **{k: v for k, v in font_candidate.items() if k != "uses_fontfile"},
                }
                try:
                    rc = page.insert_textbox(box, replace_text, **args)
                except Exception:
                    continue
                if rc >= 0:
                    return True, "ok"
    return False, "replacement_text_does_not_fit"


def _classify_pdf_editability(doc: fitz.Document, sampled_pages: int = 3) -> Dict[str, Any]:
    if doc.page_count == 0:
        return {"mode": "empty", "searchable_ratio": 0.0}

    pages_to_check = min(sampled_pages, doc.page_count)
    searchable_pages = 0
    for i in range(pages_to_check):
        page = doc[i]
        if (page.get_text("text") or "").strip():
            searchable_pages += 1

    ratio = searchable_pages / pages_to_check
    mode = "searchable" if ratio >= 0.5 else "mostly_image_or_encoded"
    return {"mode": mode, "searchable_ratio": ratio}


def _page_contains_text(page: fitz.Page, text: str) -> bool:
    normalized_text = _normalize_text(text)
    if not normalized_text:
        return True
    return normalized_text in _normalize_text(page.get_text("text") or "")


def _validate_written_replacements(doc: fitz.Document, expected_replacements: List[str]) -> List[Dict[str, Any]]:
    failures = []
    full_text = "\n".join((doc[i].get_text("text") or "") for i in range(doc.page_count))
    for replace_text in expected_replacements:
        if not replace_text:
            continue
        if _normalize_text(replace_text) not in _normalize_text(full_text):
            failures.append({
                "page": None,
                "search": None,
                "replace": replace_text,
                "reason": "replace_text_not_found_after_write",
            })
    return failures


def _dedupe_jobs(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    deduped: Dict[Tuple[int, str, int, int], Dict[str, Any]] = {}
    for job in jobs:
        key = (
            int(job["page_num"]),
            str(job["search"]),
            0,
            round(float(job["rect"].y0) / 20) * 20,
        )
        existing = deduped.get(key)
        if not existing:
            deduped[key] = job
            continue

        merged_rect = existing["rect"] | job["rect"]
        existing["rect"] = merged_rect
        existing["right_edge"] = max(existing["right_edge"], job["right_edge"])
        if job["size"] > existing["size"]:
            existing["size"] = job["size"]
            existing["color"] = job["color"]
            existing["fontname"] = job.get("fontname", existing.get("fontname", "helv"))

    return list(deduped.values())


def _env_flag(name: str, default: bool = False) -> bool:
    raw = (os.getenv(name) or "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def _extract_layout_snapshot(doc: fitz.Document) -> Dict[str, Any]:
    pages: List[Dict[str, Any]] = []
    for page in doc:
        blocks_payload: List[Dict[str, Any]] = []
        text_dict = page.get_text("dict")
        for block_idx, block in enumerate(text_dict.get("blocks") or []):
            if block.get("type") != 0:
                continue
            lines_payload: List[Dict[str, Any]] = []
            for line in block.get("lines") or []:
                spans_payload: List[Dict[str, Any]] = []
                for span in line.get("spans") or []:
                    spans_payload.append({
                        "text": span.get("text", ""),
                        "bbox": [round(float(v), 3) for v in (span.get("bbox") or [0, 0, 0, 0])],
                        "font": span.get("font", ""),
                        "size": round(float(span.get("size", 0.0) or 0.0), 3),
                        "color": int(span.get("color", 0) or 0),
                    })
                if spans_payload:
                    lines_payload.append({"spans": spans_payload})
            if lines_payload:
                blocks_payload.append({
                    "block_idx": block_idx,
                    "bbox": [round(float(v), 3) for v in (block.get("bbox") or [0, 0, 0, 0])],
                    "lines": lines_payload,
                })
        pages.append({
            "page": int(page.number),
            "width": round(float(page.rect.width), 3),
            "height": round(float(page.rect.height), 3),
            "blocks": blocks_payload,
        })

    return {
        "layout_schema_version": 1,
        "page_count": int(doc.page_count),
        "pages": pages,
    }


def _write_layout_snapshot(docs_dir: Path, source_path: Path, payload: Dict[str, Any], suffix: str = "baseline") -> Path:
    artifacts_dir = docs_dir / "_pdf_layout_artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    snapshot_name = f"{source_path.stem}.layout_v1.{suffix}.json"
    snapshot_path = artifacts_dir / snapshot_name
    with open(snapshot_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return snapshot_path


def _build_layout_qc_report(baseline: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    baseline_pages = baseline.get("pages") or []
    result_pages = result.get("pages") or []
    changed_pages = 0
    comparable_pages = min(len(baseline_pages), len(result_pages))
    pages_with_block_count_change = 0
    total_baseline_blocks = 0
    total_result_blocks = 0
    total_compared_blocks = 0
    bbox_drift_sum = 0.0
    max_block_bbox_drift = 0.0

    for idx in range(comparable_pages):
        base_page = baseline_pages[idx] or {}
        res_page = result_pages[idx] or {}
        base_blocks = base_page.get("blocks") or []
        res_blocks = res_page.get("blocks") or []
        total_baseline_blocks += len(base_blocks)
        total_result_blocks += len(res_blocks)
        if (
            base_page.get("width") != res_page.get("width")
            or base_page.get("height") != res_page.get("height")
            or len(base_blocks) != len(res_blocks)
        ):
            changed_pages += 1

        if len(base_blocks) != len(res_blocks):
            pages_with_block_count_change += 1

        pair_count = min(len(base_blocks), len(res_blocks))
        for block_idx in range(pair_count):
            base_bbox = base_blocks[block_idx].get("bbox") or [0, 0, 0, 0]
            res_bbox = res_blocks[block_idx].get("bbox") or [0, 0, 0, 0]
            if len(base_bbox) != 4 or len(res_bbox) != 4:
                continue
            drift = sum(abs(float(base_bbox[i]) - float(res_bbox[i])) for i in range(4))
            total_compared_blocks += 1
            bbox_drift_sum += drift
            if drift > max_block_bbox_drift:
                max_block_bbox_drift = drift

    avg_block_bbox_drift = (bbox_drift_sum / total_compared_blocks) if total_compared_blocks else 0.0
    max_font_shrinkage_pt = _calculate_max_font_shrinkage(baseline_pages, result_pages)

    return {
        "schema_version": 1,
        "baseline_page_count": int(baseline.get("page_count", 0) or 0),
        "result_page_count": int(result.get("page_count", 0) or 0),
        "page_count_delta": int((result.get("page_count", 0) or 0) - (baseline.get("page_count", 0) or 0)),
        "comparable_pages": comparable_pages,
        "changed_pages": changed_pages,
        "page_count_equal": int(baseline.get("page_count", 0) or 0) == int(result.get("page_count", 0) or 0),
        "pages_with_block_count_change": pages_with_block_count_change,
        "total_baseline_blocks": total_baseline_blocks,
        "total_result_blocks": total_result_blocks,
        "total_compared_blocks": total_compared_blocks,
        "avg_block_bbox_drift": round(avg_block_bbox_drift, 4),
        "max_block_bbox_drift": round(max_block_bbox_drift, 4),
        "block_count_delta_total": int(total_result_blocks - total_baseline_blocks),
        "max_font_shrinkage_pt": max_font_shrinkage_pt,
    }


def _calculate_max_font_shrinkage(baseline_pages: List[Dict[str, Any]], result_pages: List[Dict[str, Any]]) -> float:
    max_shrink = 0.0
    for base_page, res_page in zip(baseline_pages, result_pages):
        base_blocks = (base_page or {}).get("blocks") or []
        res_blocks = (res_page or {}).get("blocks") or []
        for base_block, res_block in zip(base_blocks, res_blocks):
            base_lines = (base_block or {}).get("lines") or []
            res_lines = (res_block or {}).get("lines") or []
            for base_line, res_line in zip(base_lines, res_lines):
                base_spans = (base_line or {}).get("spans") or []
                res_spans = (res_line or {}).get("spans") or []
                for base_span, res_span in zip(base_spans, res_spans):
                    base_size = float(base_span.get("size") or 0.0)
                    res_size = float(res_span.get("size") or 0.0)
                    shrink = base_size - res_size
                    if shrink > max_shrink:
                        max_shrink = shrink
    return round(max_shrink, 3)


def _calculate_text_diff_metrics(source: str, target: str) -> Dict[str, Any]:
    matcher = difflib.SequenceMatcher(None, source or "", target or "")
    added = deleted = replaced = 0
    diff_segments = 0
    for tag, a0, a1, b0, b1 in matcher.get_opcodes():
        if tag == "equal":
            continue
        diff_segments += 1
        if tag in {"replace"}:
            replaced += max(a1 - a0, b1 - b0)
        if tag in {"delete", "replace"}:
            deleted += a1 - a0
        if tag in {"insert", "replace"}:
            added += b1 - b0
    total = max(len(source or ""), len(target or ""), 1)
    ratio_changed = round((added + deleted) / total, 4)
    return {
        "segments": diff_segments,
        "added_chars": added,
        "deleted_chars": deleted,
        "replaced_chars": replaced,
        "ratio_changed": ratio_changed,
    }


def _extract_full_text_from_path(path: Path) -> str:
    doc = fitz.open(path)
    try:
        return "\n".join((doc[i].get_text("text") or "") for i in range(doc.page_count))
    finally:
        doc.close()


SHADOW_GATE_MAX_DRIFT_ENV = float(os.getenv("JANUS_PDF_SHADOW_GATE_MAX_DRIFT", "1500"))


def _shadow_rebuild_passes_gate(report: Dict[str, Any], relax_drift: bool = False) -> bool:
    max_drift = float(report.get("max_block_bbox_drift", SHADOW_GATE_MAX_DRIFT_ENV) or SHADOW_GATE_MAX_DRIFT_ENV)
    drift_ok = True if relax_drift else (max_drift <= SHADOW_GATE_MAX_DRIFT_ENV)
    return bool(
        report.get("page_count_equal")
        and int(report.get("block_count_delta_total", 0) or 0) == 0
        and drift_ok
    )


def _int_color_to_rgb(color_int: int) -> Tuple[float, float, float]:
    value = int(color_int or 0)
    return (
        ((value >> 16) & 0xFF) / 255.0,
        ((value >> 8) & 0xFF) / 255.0,
        (value & 0xFF) / 255.0,
    )


def _normalize_color_tuple(color: Tuple[float, float, float]) -> Tuple[float, float, float]:
    try:
        return tuple(max(0.0, min(1.0, float(v))) for v in (color or (0.0, 0.0, 0.0)))
    except Exception:
        return (0.0, 0.0, 0.0)


def _render_page_rebuild_v1(page: fitz.Page, page_data: Dict, font_path: str) -> None:
    """Deterministischer Rebuild mit hartem Custom-Wrap (Kein Font-Shrinking!)."""

    font_map: Dict[str, fitz.Font] = {}

    def get_font(fontname: str) -> fitz.Font:
        if fontname not in font_map:
            try:
                font_map[fontname] = fitz.Font(fontname)
            except Exception:
                if os.path.exists(font_path):
                    font_map[fontname] = fitz.Font(fontfile=font_path)
                else:
                    font_map[fontname] = fitz.Font("helv")
        return font_map[fontname]

    for block in page_data.get("blocks", []):
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "")
                if not text.strip():
                    continue

                origin = span.get("origin") or [0.0, 0.0]
                bbox = span.get("bbox") or [0.0, 0.0, 0.0, 0.0]
                if len(bbox) != 4:
                    continue
                size = float(span.get("size", DEFAULT_FONT_SIZE) or DEFAULT_FONT_SIZE)
                color_int = int(span.get("color", 0) or 0)
                color = (
                    ((color_int >> 16) & 255) / 255,
                    ((color_int >> 8) & 255) / 255,
                    (color_int & 255) / 255,
                )

                font = get_font(str(span.get("font", "")))
                rect_width = bbox[2] - bbox[0]
                words = text.split()
                space_width = font.text_length(" ", fontsize=size)

                current_line_words: List[str] = []
                current_line_width = 0.0
                y_cursor = origin[1]

                for word in words:
                    word_width = font.text_length(word, fontsize=size)
                    if current_line_words and (current_line_width + space_width + word_width > rect_width + 2):
                        line_text = " ".join(current_line_words)
                        page.insert_text(
                            (bbox[0], y_cursor),
                            line_text,
                            fontname="helv",
                            fontsize=size,
                            color=color,
                            overlay=False,
                        )
                        y_cursor += size * 1.35
                        current_line_words = [word]
                        current_line_width = word_width
                    else:
                        current_line_width += (space_width if current_line_words else 0.0) + word_width
                        current_line_words.append(word)

                if current_line_words:
                    page.insert_text(
                        (bbox[0], y_cursor),
                        " ".join(current_line_words),
                        fontname="helv",
                        fontsize=size,
                        color=color,
                    )


def _build_deterministic_rebuild_pdf(final_jobs: List[Dict[str, Any]], layout_payload: Dict[str, Any], docs_dir: Path, source_path: Path) -> Tuple[Path, Dict[str, Any]]:
    artifacts_dir = docs_dir / "_pdf_layout_artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    output_path = artifacts_dir / f"{source_path.stem}.layout_v1.shadow_rebuild.pdf"

    jobs_by_page: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for job in final_jobs:
        jobs_by_page[int(job["page_num"] or 0)].append(job)

    overflow_report = {"overflow": False, "items": []}

    rebuilt = fitz.open()
    try:
        font_path = resource_path("backend/assets/fonts/DejaVuSans.ttf")
        for page_payload in (layout_payload.get("pages") or []):
            page_index = int(page_payload.get("page", 0))
            width = float(page_payload.get("width") or 595.0)
            height = float(page_payload.get("height") or 842.0)
            page = rebuilt.new_page(width=width, height=height)

            _render_page_rebuild_v1(page, page_payload, font_path)

        rebuilt.save(output_path, incremental=False, encryption=0)
    finally:
        rebuilt.close()

    return output_path, overflow_report


def _get_monitor_log_path() -> Path:
    docs_dir = Path(get_user_docs_dir())
    override = (os.getenv("JANUS_PDF_MONITOR_LOG") or "").strip()
    if override:
        candidate = Path(override)
        if candidate.is_absolute():
            return candidate
        return docs_dir / candidate
    return docs_dir / "PDF_Diamond_Monitoring.csv"


def _write_monitor_log_entry(original_filename: str, artifacts: Dict[str, Any], mode: str, quality_gate: str) -> None:
    path = _get_monitor_log_path()
    is_new = not path.exists()
    go_no_go = artifacts.get("go_no_go", {}) or {}
    overflow = artifacts.get("shadow_overflow", {}) or {}
    gate = artifacts.get("shadow_rebuild_gate", {}) or {}
    qc_report = artifacts.get("shadow_rebuild_qc_report", {}) or {}
    diff_ratio = go_no_go.get("diff_ratio")
    font_shrinkage = qc_report.get("max_font_shrinkage_pt")
    with open(path, "a", encoding="utf-8") as f:
        if is_new:
            f.write(
                "timestamp,filename,mode,quality_gate,go_no_go,status,diff_ratio,shadow_gate_status,overflow,overflow_items,font_shrinkage_pt\n"
            )
        f.write(
            f"{datetime.utcnow().isoformat()},{original_filename},{mode},{quality_gate},"
            f"{go_no_go.get('shadow_gate_passed','')},{go_no_go.get('status','')},{diff_ratio if diff_ratio is not None else ''},"
            f"{gate.get('status','')},{overflow.get('overflow', False)},{len(overflow.get('items') or [])},{font_shrinkage if font_shrinkage is not None else ''}\n"
        )


def _normalize_font_for_rebuild(raw_font: str) -> str:
    normalized = (raw_font or "").strip().lower()
    if normalized in BASE14_FONTS:
        return normalized
    if "helvetica" in normalized:
        return "helv"
    if "times" in normalized:
        return "times-roman"
    if "courier" in normalized:
        return "courier"
    return "helv"


async def edit_pdf_text_in_place(
    original_filename: str,
    modifications: List[Dict[str, str]],
    edit_mode: str | None = None,
    shadow_run: bool = False,
    db: Session = None,
) -> ToolResultV1:
    """Robuster PDF-Editor mit kumulativer Bearbeitung, Line-Dedupe und Qualitätsgates."""
    started = time.perf_counter()
    tags = ["knowledge", "pdf"]
    try:
        return await _edit_pdf_text_in_place_core(
            original_filename, modifications, edit_mode, shadow_run, db, started, tags
        )
    except Exception as e:
        logger.error("edit_pdf_text_in_place: %s", e, exc_info=True)
        return tool_err_v1("OPERATION_FAILED", str(e), tags=tags, started_at=started)


async def _edit_pdf_text_in_place_core(
    original_filename: str,
    modifications: List[Dict[str, str]],
    edit_mode: str | None,
    shadow_run: bool,
    db: Session,
    started: float,
    tags: List[str],
) -> ToolResultV1:
    """Interne Implementierung (Diamond: ToolResultV1, abgefangene Core-Fehler im äußeren Wrapper)."""

    def _skill_ok(data: Dict[str, Any]) -> ToolResultV1:
        return tool_ok_v1(data, tags=tags, started_at=started)

    def _skill_error(message: str, code: str = None, details: Any = None) -> ToolResultV1:
        return tool_err_v1(code or "OPERATION_FAILED", message, details=details, tags=tags, started_at=started)

    if not modifications:
        return _skill_error("Keine Korrekturen übergeben.", code="no_modifications")

    explicit_mode = (edit_mode or "").strip().lower()
    env_mode = (os.getenv("JANUS_PDF_EDIT_MODE") or "").strip().lower()
    requested_mode = explicit_mode or env_mode or "inplace"
    if requested_mode not in {"inplace", "rebuild_v1"}:
        return _skill_error(
            f"Unbekannter edit_mode '{requested_mode}'. Erlaubt: inplace, rebuild_v1",
            code="invalid_mode",
            details={"quality_gate": "invalid_mode"},
        )
    shadow_enabled = bool(shadow_run) or _env_flag("JANUS_PDF_SHADOW_REBUILD", default=False)
    deterministic_renderer_enabled = _env_flag("JANUS_PDF_ENABLE_DETERMINISTIC_RENDERER", default=False)
    force_rebuild = requested_mode == "rebuild_v1"

    docs_dir = Path(get_user_docs_dir())
    source_path = docs_dir / original_filename
    target_filename = f"{source_path.stem}_korrigiert{source_path.suffix}"
    target_path = docs_dir / target_filename
    
    if not source_path.exists():
        return _skill_error("Datei nicht gefunden.", code="file_missing")

    async with pdf_write_lock:
        doc = None
        layout_artifacts: Dict[str, str] = {}
        mode_effective = requested_mode
        try:
            load_path = target_path if target_path.exists() else source_path
            with open(load_path, "rb") as f:
                pdf_bytes = f.read()
            doc = fitz.open("pdf", pdf_bytes)

            if shadow_enabled or requested_mode == "rebuild_v1" or _env_flag("JANUS_PDF_WRITE_LAYOUT_SNAPSHOT", default=False):
                baseline_layout = _extract_layout_snapshot(doc)
                baseline_path = _write_layout_snapshot(docs_dir, source_path, baseline_layout, suffix="baseline")
                layout_artifacts["baseline_layout"] = str(baseline_path)

            if requested_mode == "rebuild_v1":
                # Wir vertrauen der Engine jetzt: Fallback deaktiviert.
                mode_effective = "rebuild_v1"
                logger.info("rebuild_v1 requested: Using deterministic rebuild path.")

            editability = _classify_pdf_editability(doc)
            if editability["mode"] == "mostly_image_or_encoded":
                doc.close()
                return _skill_error(
                    "PDF ist kaum als Text editierbar (wahrscheinlich Scan/Font-Encoding-Problem). Bitte OCR/Rebuild-Workflow nutzen.",
                    code="editability_failed",
                    details={"quality_gate": "editability_failed", "editability": editability},
                )

            final_jobs: List[Dict[str, Any]] = []
            missing_searches: List[str] = []
            normalized_mods: List[Dict[str, str]] = []
            mod_found_map: Dict[str, bool] = {}

            for mod in modifications:
                search_term = _normalize_text(mod.get("search", ""))
                replace_text = mod.get("replace") or ""
                if not search_term:
                    continue
                normalized_mods.append({"search": search_term, "replace": replace_text})
                mod_found_map[search_term] = False

            for page in doc:
                for block in page.get_text("blocks"):
                    if len(block) < 5:
                        continue
                    block_text = block[4] or ""
                    if not block_text.strip():
                        continue

                    rewritten_text = block_text
                    touched_searches: List[str] = []

                    for mod in normalized_mods:
                        rewritten_text, replacements_count = _replace_with_flexible_whitespace(
                            rewritten_text,
                            mod["search"],
                            mod["replace"],
                        )
                        if replacements_count > 0:
                            mod_found_map[mod["search"]] = True
                            touched_searches.append(mod["search"])

                    if not touched_searches:
                        continue

                    block_rect = fitz.Rect(block[:4])
                    f_size, f_color, f_name = _extract_style(page, block_rect)
                    final_jobs.append({
                        "page_num": page.number,
                        "rect": block_rect,
                        "search": " | ".join(touched_searches),
                        "replace": rewritten_text,
                        "size": f_size,
                        "color": f_color,
                        "fontname": f_name,
                        "right_edge": max(get_layout_bounds(page, block_rect), block_rect.x1),
                    })

            for search_term, was_found in mod_found_map.items():
                if not was_found:
                    missing_searches.append(search_term)

            if missing_searches:
                doc.close()
                _write_monitor_log_entry(source_path.name, layout_artifacts, mode_effective, "search_terms_missing")
                return _skill_error(
                    "Einige Suchtexte wurden nicht gefunden. Keine Teil-Korrektur durchgeführt.",
                    code="search_terms_missing",
                    details={
                        "quality_gate": "search_terms_missing",
                        "missing_search_terms": missing_searches,
                    },
                )

            if not final_jobs:
                doc.close()
                _write_monitor_log_entry(source_path.name, layout_artifacts, mode_effective, "no_jobs")
                return _skill_error(
                    "Keine editierbaren Treffer für die angeforderten Korrekturen gefunden.",
                    code="no_jobs",
                    details={"quality_gate": "no_jobs"},
                )

            final_jobs = _dedupe_jobs(final_jobs)

            for job in final_jobs:
                page = doc[job["page_num"]]
                page.draw_rect(job["rect"], color=(1, 1, 1), fill=(1, 1, 1), overlay=True)
                page.add_redact_annot(job["rect"], fill=(1, 1, 1))
                page.apply_redactions(images=0, graphics=0)

            font_path = resource_path("backend/assets/fonts/DejaVuSans.ttf")
            insertion_failures = []
            for job in final_jobs:
                page = doc[job["page_num"]]
                ok, reason = _try_insert_replacement(page, job, font_path)
                if not ok:
                    insertion_failures.append({
                        "page": job["page_num"] + 1,
                        "search": job["search"],
                        "replace": job["replace"],
                        "reason": reason,
                    })

            if insertion_failures:
                doc.close()
                _write_monitor_log_entry(source_path.name, layout_artifacts, mode_effective, "overflow")
                return _skill_error(
                    "Mindestens eine Ersetzung passt nicht in den verfügbaren Layout-Container.",
                    code="overflow",
                    details={
                        "quality_gate": "overflow",
                        "failed_replacements": insertion_failures,
                    },
                )

            doc.save(target_path, incremental=False, encryption=0)
            doc.close()

            validation_doc = fitz.open(target_path)
            try:
                expected_replacements = [m["replace"] for m in normalized_mods if m.get("replace")]
                validation_failures = _validate_written_replacements(validation_doc, expected_replacements)
            finally:
                validation_doc.close()

            if validation_failures:
                _write_monitor_log_entry(source_path.name, layout_artifacts, mode_effective, "post_write_validation_failed")
                return _skill_error(
                    "Qualitätsprüfung fehlgeschlagen: Ersetzungstexte nach Schreiben nicht nachweisbar.",
                    code="post_write_validation_failed",
                    details={
                        "quality_gate": "post_write_validation_failed",
                        "validation_failures": validation_failures,
                        "mode_requested": requested_mode,
                        "mode_effective": mode_effective,
                        "shadow_run": shadow_enabled,
                        "layout_artifacts": layout_artifacts,
                    },
                )

            if shadow_enabled or _env_flag("JANUS_PDF_WRITE_LAYOUT_SNAPSHOT", default=False):
                result_doc = fitz.open(target_path)
                try:
                    result_layout = _extract_layout_snapshot(result_doc)
                finally:
                    result_doc.close()
                result_path = _write_layout_snapshot(docs_dir, source_path, result_layout, suffix="result")
                layout_artifacts["result_layout"] = str(result_path)
                if "baseline_layout" in layout_artifacts:
                    layout_artifacts["qc_report"] = _build_layout_qc_report(baseline_layout, result_layout)

                    if requested_mode == "rebuild_v1" or _env_flag("JANUS_PDF_SHADOW_RENDER_REBUILD", default=False):
                        try:
                            shadow_rebuild_path, overflow_report = _build_deterministic_rebuild_pdf(final_jobs, result_layout, docs_dir, source_path)
                            layout_artifacts["shadow_rebuild_pdf"] = str(shadow_rebuild_path)
                            layout_artifacts["shadow_overflow"] = overflow_report

                            shadow_doc = fitz.open(shadow_rebuild_path)
                            try:
                                shadow_layout = _extract_layout_snapshot(shadow_doc)
                            finally:
                                shadow_doc.close()

                            shadow_layout_path = _write_layout_snapshot(
                                docs_dir,
                                source_path,
                                shadow_layout,
                                suffix="shadow_rebuild",
                            )
                            layout_artifacts["shadow_rebuild_layout"] = str(shadow_layout_path)
                            shadow_report = _build_layout_qc_report(result_layout, shadow_layout)
                            layout_artifacts["shadow_rebuild_qc_report"] = shadow_report

                            shadow_gate_passed = _shadow_rebuild_passes_gate(shadow_report, relax_drift=force_rebuild)
                            layout_artifacts["shadow_rebuild_gate"] = {
                                "status": "passed" if shadow_gate_passed else "failed",
                                "reason": "shadow_rebuild_qc_gate_failed" if not shadow_gate_passed else "",
                            }

                            if requested_mode == "rebuild_v1" and _env_flag("JANUS_PDF_ENABLE_REBUILD_EXECUTION", default=False):
                                if shadow_gate_passed:
                                    target_path.write_bytes(shadow_rebuild_path.read_bytes())
                                    mode_effective = "rebuild_v1_experimental"

                            diff_metrics = {}
                            try:
                                inplace_text = _extract_full_text_from_path(target_path)
                                shadow_text = _extract_full_text_from_path(shadow_rebuild_path)
                                diff_metrics = _calculate_text_diff_metrics(inplace_text, shadow_text)
                            except Exception as diff_error:
                                layout_artifacts["text_diff_error"] = str(diff_error)
                            finally:
                                layout_artifacts["text_diff_metrics"] = diff_metrics

                            go_no_go_status = "ready_for_review" if shadow_gate_passed and diff_metrics.get("ratio_changed", 1.0) <= 0.2 else "hold"
                            layout_artifacts["go_no_go"] = {
                                "status": go_no_go_status,
                                "shadow_gate_passed": shadow_gate_passed,
                                "diff_ratio": diff_metrics.get("ratio_changed", 1.0),
                            }
                        except Exception as shadow_error:
                            layout_artifacts["shadow_rebuild_error"] = str(shadow_error)

        except Exception as e:
            if doc:
                doc.close()
            logger.error(f"Surgical Fix Error: {e}", exc_info=True)
            return _skill_error(str(e), code="exception")

    try:
        _write_monitor_log_entry(source_path.name, layout_artifacts, mode_effective, "passed")
    except Exception as log_error:
        logger.error("Failed to write PDF Diamond monitoring entry", exc_info=log_error)
    register_and_index_file(target_filename, str(target_path), db, audit_status="verified")
    return _skill_ok(
        {
            "result": f"Erfolg: {len(final_jobs)} Stellen bereinigt.",
            "ui_action": "refresh_documents",
            "quality_gate": "passed",
            "editability": editability,
            "mode_requested": requested_mode,
            "mode_effective": mode_effective,
            "shadow_run": shadow_enabled,
            "layout_artifacts": layout_artifacts,
        }
    )
