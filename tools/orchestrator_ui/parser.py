"""
Diamond Task Orchestrator UI - Parser Module
============================================
Category : B6 (Schema-Design)
Task     : task_orchestrator_01_schema_and_parser.md
Version  : 1.1 (A3-Review hardened)

Parses 01_CENTRAL_TASK_REGISTRY.md and linked Epic files into structured
Pydantic models.

SECURITY RULE (A3-Review):
  All checkbox matching uses CONTEXT-BOUND REGEX anchored to the task
  FILENAME (task_*.md).  Global re.sub on '[ ]' is strictly forbidden.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import List, Optional, TypedDict

from filelock import FileLock
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class MicroTask(BaseModel):
    filename: str
    description: str
    status: str          # "open" | "done"
    line_index: int = -1  # 0-based line number inside the epic file


class Epic(BaseModel):
    name: str
    ref_file: str                    # relative path e.g. documentation/features/epic_xyz.md
    status: str
    progress: str                    # e.g. "2/5 Tasks"
    next_blocker: Optional[str] = None
    """Raw blocker text from registry (may be human-readable)."""
    next_blocker_task_filename: Optional[str] = None
    """Resolved `task_*.md` filename for UI / Mark-Done (matches MicroTask.filename)."""
    tasks: List[MicroTask] = Field(default_factory=list)
    archived: bool = False           # True when parsed from "## ✅ Archivierte & Erledigte Epics"


class StandaloneBug(BaseModel):
    task_filename: str
    ref: str             # e.g. "system.websearch"
    status: str
    priority: str


class MacroTask(BaseModel):
    """Task aus der Macro-Dashboard Tabelle (V3.0 — 12 Spalten)."""
    task_id: str
    cu: int
    status: str
    app: str
    model: str
    prio: str
    milestone: str
    tags: str = ""
    meilenstein: str = ""
    master_prompt: str
    references: str
    ergebnis: str


class DeferredTask(BaseModel):
    """Task im DEFERRED Pool (wartet auf Ressourcen)."""
    task_id: str
    cu: int
    cu_log: str
    original_editor: str
    reason: str
    since: str
    prio: str
    unblock_condition: str


class SystemState(BaseModel):
    registry_path: str
    epics: List[Epic] = Field(default_factory=list)
    standalone_bugs: List[StandaloneBug] = Field(default_factory=list)
    macro_tasks: List[MacroTask] = Field(default_factory=list)
    deferred_tasks: List[DeferredTask] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Registry Parser
# ---------------------------------------------------------------------------

# Epic Header Patterns (fuzzy matching for different formats)
_EPIC_HEADER = re.compile(
    r"^### Epic:\s*(.+?)\s*\(Ref:\s*`([^`]+)`\)",
    re.MULTILINE | re.IGNORECASE,
)
# Simple fallback: Just capture everything after ### Epic:
_EPIC_HEADER_FALLBACK = re.compile(
    r"^### Epic:\s*(.+)$",
    re.MULTILINE | re.IGNORECASE,
)
# Extract Ref from body if not in header
_EPIC_REF_IN_BODY = re.compile(
    r"[-*]\s+\*\*Referenz:\*\*\s*`([^`]+)`",
    re.MULTILINE,
)
_STATUS_LINE   = re.compile(r"[-*]\s+\*\*Status:\*\*\s+(.+?)$",    re.MULTILINE)
_PROGRESS_LINE = re.compile(r"[-*]\s+\*\*Progress:\*\*\s+(.+?)$",  re.MULTILINE)
_BLOCKER_LINE  = re.compile(r"[-*]\s+\*\*N.CHSTER BLOCKER:\*\*\s+`([^`]*)`", re.MULTILINE)
# Extract Task-to-Epic mapping from macro table (Task XXX → Epic)
_TASK_EPIC_MAP = re.compile(
    r"Epic\s+MCL\s*§\s*M[1-5]|Epic\s+Universal\s+Modal|task_(\d+).*?\.md",
    re.IGNORECASE,
)

_BUG_TASK   = re.compile(r"[-*]\s+\*\*Task:\*\*\s+`([^`]+)`\s+\(Ref:\s+`([^`]+)`\)", re.MULTILINE)
_BUG_STATUS = re.compile(r"[-*]\s+\*\*Status:\*\*\s+(.+?)$",    re.MULTILINE)
_BUG_PRIO   = re.compile(r"[-*]\s+\*\*Priorit.t:\*\*\s+(.+?)$", re.MULTILINE)

# Macro-Dashboard Parser (V3.0 — 12-column support with Tags + Meilenstein)
_MACRO_TABLE_LINE = re.compile(
    r"^\|\s*([^|]+)\s*\|\s*(\d+|—)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|",
    re.MULTILINE,
)

# DEFERRED Pool Parser
_DEFERRED_TABLE_LINE = re.compile(
    r"^\|\s*([^|]+)\s*\|\s*(\d+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|",
    re.MULTILINE,
)

# Archived epic summary table (| Epic | Status | Zertifizierung | Referenz |)
_ARCHIVED_EPIC_TABLE_ROW = re.compile(
    r"^\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|",
)


def _epic_status_is_complete(status: str) -> bool:
    """Registry status text implies terminal epic (DONE / COMPLETE / SEALED)."""
    if not status or not str(status).strip():
        return False
    u = str(status).upper()
    return bool(re.search(r"\b(DONE|COMPLETE|COMPLETED|SEALED)\b", u))


def _force_epic_progress_complete(raw: dict) -> bool:
    """
    Use synthetic 100%% progress instead of counting missing task files.
    Table-summary rows are complete unless status shows 🟡 (partial / still open work).
    """
    if raw.get("epic_source") == "table":
        st = raw.get("status") or ""
        if "🟡" in st:
            return False
        return True
    st = raw.get("status") or ""
    if "🟡" in st:
        return False
    return _epic_status_is_complete(st)


def _strip_md_bold(s: str) -> str:
    return s.replace("**", "").strip()


def _extract_h2_section_body(content: str, heading_prefix: str) -> Optional[str]:
    """
    Return body after an H2 line that starts with heading_prefix, until the next H2 (## not ###).
    """
    lines = content.splitlines(keepends=True)
    start_body: Optional[int] = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("## ") and not stripped.startswith("###"):
            if stripped.startswith(heading_prefix):
                start_body = i + 1
                break
    if start_body is None:
        return None
    out: list[str] = []
    for j in range(start_body, len(lines)):
        line = lines[j]
        if line.startswith("## ") and not line.startswith("###"):
            break
        out.append(line)
    return "".join(out)


def _parse_epic_blocks_in_text(block_source: str, archived: bool) -> list[dict]:
    """
    Find all ### Epic: ... blocks in block_source (single registry section slice).
    """
    epics_out: list[dict] = []
    epic_starts = [m.start() for m in _EPIC_HEADER.finditer(block_source)]
    fallback_matches = list(_EPIC_HEADER_FALLBACK.finditer(block_source))
    all_epic_positions: set[int] = set(epic_starts)
    for m in fallback_matches:
        pos = m.start()
        if not any(abs(pos - existing) < 50 for existing in epic_starts):
            all_epic_positions.add(pos)
    sorted_positions = sorted(all_epic_positions)
    sorted_positions.append(len(block_source))

    for i, start in enumerate(sorted_positions[:-1]):
        block = block_source[start : sorted_positions[i + 1]]
        m_header = _EPIC_HEADER.search(block)
        epic_name = None
        ref_file = None
        if m_header:
            epic_name = m_header.group(1).strip()
            ref_file = m_header.group(2).strip()
        else:
            m_fallback = _EPIC_HEADER_FALLBACK.search(block)
            if m_fallback:
                epic_name = m_fallback.group(1).strip()
                m_ref_in_body = _EPIC_REF_IN_BODY.search(block)
                if m_ref_in_body:
                    ref_file = m_ref_in_body.group(1).strip()
        if not epic_name:
            continue
        m_status = _STATUS_LINE.search(block)
        m_progress = _PROGRESS_LINE.search(block)
        m_blocker = _BLOCKER_LINE.search(block)
        status = m_status.group(1).strip() if m_status else "Unknown"
        progress = m_progress.group(1).strip() if m_progress else "0/0"
        blocker = m_blocker.group(1).strip() if m_blocker else None
        epics_out.append(
            {
                "name": epic_name,
                "ref_file": ref_file or f"documentation/tasks/{epic_name.lower().replace(' ', '_')}.md",
                "status": status,
                "progress": progress,
                "next_blocker": blocker,
                "archived": archived,
                "epic_source": "block",
            }
        )
    return epics_out


def _parse_archived_epic_table_rows(section_body: str) -> list[dict]:
    """Rows from | Epic | Status | Zertifizierung | Referenz | (skip header / rules)."""
    rows: list[dict] = []
    if not section_body:
        return rows
    for line in section_body.splitlines():
        line = line.rstrip()
        if not line.strip().startswith("|"):
            continue
        if "| Epic |" in line or "|---------" in line:
            continue
        m = _ARCHIVED_EPIC_TABLE_ROW.match(line)
        if not m:
            continue
        name = _strip_md_bold(m.group(1))
        status = _strip_md_bold(m.group(2))
        _cert = _strip_md_bold(m.group(3))
        ref_cell = _strip_md_bold(m.group(4))
        if not name or name.lower() == "epic":
            continue
        ref_file = ref_cell
        if ref_cell.startswith("`") and ref_cell.endswith("`"):
            ref_file = ref_cell.strip("`").strip()
        progress = "1/1 Tasks"
        if "\U0001f7e1" in status or "🟡" in status:
            progress = ""
        rows.append(
            {
                "name": name,
                "ref_file": ref_file or f"documentation/tasks/{name.lower().replace(' ', '_')}.md",
                "status": status,
                "progress": progress,
                "next_blocker": None,
                "archived": True,
                "epic_source": "table",
            }
        )
    return rows


def _parse_macro_dashboard_active_lines(content: str) -> list[dict]:
    """
    Parse ONLY the active Macro-Dashboard (Copy/Paste) table — stops at '---' or next H2.
    Ignores '## Macro-Dashboard Archiv' and duplicate tables at EOF.
    """
    lines = content.splitlines()
    i = 0
    header_idx = -1
    while i < len(lines):
        if lines[i].startswith("## Macro-Dashboard (Copy/Paste"):
            header_idx = i
            break
        i += 1
    if header_idx < 0:
        return []
    i = header_idx + 1
    while i < len(lines) and "| Task-ID |" not in lines[i]:
        i += 1
    if i >= len(lines):
        return []
    i += 1
    if i < len(lines) and lines[i].strip().startswith("|---------"):
        i += 1
    macros_raw: list[dict] = []
    while i < len(lines):
        line = lines[i]
        if line.strip() == "---":
            break
        if line.startswith("## ") and not line.startswith("###"):
            break
        if line.strip().startswith("|"):
            m = _MACRO_TABLE_LINE.match(line)
            if m:
                task_id = m.group(1).strip().replace("**", "")
                if task_id and task_id != "Task-ID":
                    cu_val = m.group(2).strip()
                    macros_raw.append(
                        {
                            "task_id": task_id,
                            "cu": int(cu_val) if cu_val.isdigit() else 0,
                            "status": m.group(3).strip(),
                            "app": m.group(4).strip(),
                            "model": m.group(5).strip(),
                            "prio": m.group(6).strip(),
                            "milestone": m.group(7).strip(),
                            "tags": m.group(8).strip(),
                            "meilenstein": m.group(9).strip(),
                            "master_prompt": m.group(10).strip(),
                            "references": m.group(11).strip(),
                            "ergebnis": m.group(12).strip(),
                        }
                    )
        i += 1
    return macros_raw


def _parse_registry(registry_path: Path) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    """
    Parse 01_CENTRAL_TASK_REGISTRY.md.

    Returns (epics_raw, bugs_raw, macros_raw, deferred_raw).
    Epics under ``## Epics in Entwicklung`` are active (archived=False).
    Epics under ``## ✅ Archivierte & Erledigte Epics`` (### blocks + summary table)
    are archived (archived=True) for metrics; completed status forces 100%% progress in loader.
    """
    content = registry_path.read_text(encoding="utf-8")

    epics_raw: list[dict] = []
    bugs_raw: list[dict] = []
    macros_raw: list[dict] = []
    deferred_raw: list[dict] = []

    dev_slice = _extract_h2_section_body(content, "## Epics in Entwicklung")
    if dev_slice:
        epics_raw.extend(_parse_epic_blocks_in_text(dev_slice, archived=False))

    arch_heading = "## ✅ Archivierte & Erledigte Epics"
    if arch_heading not in content:
        arch_heading = "## Archivierte Epics"
    arch_slice = _extract_h2_section_body(content, arch_heading)
    if arch_slice:
        from_blocks = _parse_epic_blocks_in_text(arch_slice, archived=True)
        epics_raw.extend(from_blocks)
        from_table = _parse_archived_epic_table_rows(arch_slice)
        block_names = {b["name"].strip().lower() for b in from_blocks}
        for row in from_table:
            if row["name"].strip().lower() in block_names:
                continue
            epics_raw.append(row)

    macros_raw = _parse_macro_dashboard_active_lines(content)

    # Parse standalone bugs section
    # Find Bugfix section boundaries
    bug_section_match = re.search(
        r"## .*Isolierte Bugfixes.*?(?=\n## |\Z)",
        content, re.DOTALL
    )
    if bug_section_match:
        bug_block = bug_section_match.group()
        for m_task in _BUG_TASK.finditer(bug_block):
            task_filename = m_task.group(1).strip()
            ref           = m_task.group(2).strip()
            # Find Status and Priorität following this task line
            after = bug_block[m_task.end():]
            m_s = _BUG_STATUS.search(after)
            m_p = _BUG_PRIO.search(after)
            bugs_raw.append({
                "task_filename": task_filename,
                "ref":           ref,
                "status":        m_s.group(1).strip() if m_s else "Unbekannt",
                "priority":      m_p.group(1).strip() if m_p else "Unbekannt",
            })

    # Parse DEFERRED Pool table
    deferred_section = re.search(
        r"## DEFERRED Pool.*?\| Task-ID \|.*?(?=\n## |\Z)",
        content, re.DOTALL
    )
    if deferred_section:
        table_content = deferred_section.group()
        for line in table_content.splitlines():
            if line.strip().startswith("|---------"):
                continue
            m = _DEFERRED_TABLE_LINE.match(line)
            if m:
                task_id = m.group(1).strip()
                if task_id and task_id != "Task-ID":  # Skip header
                    deferred_raw.append({
                        "task_id":          task_id,
                        "cu":               int(m.group(2)),
                        "cu_log":           m.group(3).strip(),
                        "original_editor":  m.group(4).strip(),
                        "reason":           m.group(5).strip(),
                        "since":            m.group(6).strip(),
                        "prio":             m.group(7).strip(),
                        "unblock_condition": m.group(8).strip(),
                    })

    return epics_raw, bugs_raw, macros_raw, deferred_raw


# ---------------------------------------------------------------------------
# Epic Parser  –  Context-Bound Regex (A3-Review Auflage)
# ---------------------------------------------------------------------------

# SECURITY: pattern is anchored by:
#   1. Line-start  (^)
#   2. Checkbox    ([ ] or [x])
#   3. Digit+dot   (\d+\.)
#   4. Backtick-quoted filename that STARTS WITH "task_" and ENDS WITH ".md"
#   5. Opening parenthesis for description
#
# This prevents matching:
#   - Plain "- [ ] text" in code blocks or descriptions (no task_ filename)
#   - Files not following the task_*.md convention
#   - Indented or otherwise malformed lines

# Numbered checklist line; optional "(description)" suffix (Diamond epic format).
_TASK_LINE = re.compile(
    r"^- \[([ x])\] \d+\. `(task_[A-Za-z0-9_]+\.md)`(?: \(([^)]+)\))?\s*$",
    re.MULTILINE,
)
# Fallback: any markdown task checkbox at line start (epics that use phases, not task_*.md files)
_EPIC_CHECKBOX_LINE = re.compile(r"^-\s+\[([ x])\]\s+", re.MULTILINE)


def _rollup_epic_file_checkboxes(epic_path: Path) -> Optional[tuple[int, int]]:
    """Return (done, total) for lines like '- [ ]' / '- [x]' in an epic file, or None if none."""
    if not epic_path.exists():
        return None
    marks = _EPIC_CHECKBOX_LINE.findall(epic_path.read_text(encoding="utf-8"))
    if not marks:
        return None
    done = sum(1 for m in marks if m == "x")
    return (done, len(marks))


def _parse_epic_tasks(epic_path: Path) -> List[MicroTask]:
    """
    Parse task checklist from an epic file.

    Only lines matching the strict TASK_LINE pattern are considered.
    Checkboxes inside code fences, plain descriptions, or any line
    not anchored to a `task_*.md` filename are silently ignored.
    """
    if not epic_path.exists():
        return []

    content  = epic_path.read_text(encoding="utf-8")
    lines    = content.splitlines()
    tasks: List[MicroTask] = []

    for line_idx, line in enumerate(lines):
        m = _TASK_LINE.match(line)
        if m:
            desc = (m.group(3) or "").strip()
            tasks.append(MicroTask(
                filename    = m.group(2),
                description = desc,
                status      = "done" if m.group(1) == "x" else "open",
                line_index  = line_idx,
            ))

    return tasks


def _resolve_blocker_to_task_filename(
    blocker_raw: Optional[str],
    tasks: List[MicroTask],
) -> Optional[str]:
    """
    Map registry **NÄCHSTER BLOCKER** text to a MicroTask.filename.

    Accepts:
      - `task_012_foo.md` (with or without backticks in source)
      - Human text like `Task 030: …` → first task whose filename contains task_030_
    """
    if not blocker_raw or not tasks:
        return None
    b = blocker_raw.strip().strip("`").strip()
    if re.fullmatch(r"task_[A-Za-z0-9_]+\.md", b):
        return b
    m = re.search(r"Task\s+0*(\d+)", b, re.IGNORECASE)
    if m:
        num = m.group(1)
        for t in tasks:
            if re.match(rf"task_0*{num}[^0-9]", t.filename):
                return t.filename
    for t in tasks:
        if t.status == "open":
            return t.filename
    return None


# ---------------------------------------------------------------------------
# Main Loader
# ---------------------------------------------------------------------------

def load_full_system_state(repo_root: Optional[Path] = None) -> SystemState:
    """
    Load the complete Diamond-OS system state.

    Reads:
      1. <repo_root>/01_CENTRAL_TASK_REGISTRY.md
      2. Each referenced documentation/features/epic_xyz.md

    Args:
        repo_root: Repo root path.  Defaults to three levels above this file
                   (tools/orchestrator_ui/parser.py -> tools/orchestrator_ui
                    -> tools -> repo_root).

    Returns:
        Fully populated SystemState.

    Raises:
        FileNotFoundError: If the registry file does not exist.
    """
    if repo_root is None:
        repo_root = Path(__file__).resolve().parent.parent.parent

    registry_path = repo_root / "01_CENTRAL_TASK_REGISTRY.md"

    if not registry_path.exists():
        raise FileNotFoundError(
            f"Registry not found at: {registry_path}\n"
            f"  (repo_root resolved to: {repo_root})"
        )

    epics_raw, bugs_raw, macros_raw, deferred_raw = _parse_registry(registry_path)

    epics: List[Epic] = []
    for raw in epics_raw:
        archived = bool(raw.get("archived"))
        effective_progress = raw["progress"]
        tasks: List[MicroTask] = []

        if _force_epic_progress_complete(raw):
            effective_progress = "1/1 Tasks"
            tasks = [
                MicroTask(
                    filename="__registry_complete__.md",
                    description="Registry: epic closed or archived summary (no task-file roll-up)",
                    status="done",
                    line_index=0,
                )
            ]
        else:
            ref_rel = (raw.get("ref_file") or "").strip()
            epic_path = repo_root / ref_rel if ref_rel else None
            tasks = _parse_epic_tasks(epic_path) if epic_path and epic_path.exists() else []

            if not tasks and epic_path and epic_path.exists():
                rollup = _rollup_epic_file_checkboxes(epic_path)
                if rollup:
                    done_r, total_r = rollup
                    tasks = [
                        MicroTask(
                            filename=f"__epic_checkbox_{i}.md",
                            description="Epic checklist line (non-task_*.md)",
                            status="done" if i < done_r else "open",
                            line_index=i,
                        )
                        for i in range(total_r)
                    ]
            if tasks:
                done_ct = sum(1 for t in tasks if t.status == "done")
                effective_progress = f"{done_ct}/{len(tasks)} Tasks"

        blocker_resolved = _resolve_blocker_to_task_filename(raw.get("next_blocker"), tasks)

        epics.append(
            Epic(
                name=raw["name"],
                ref_file=raw["ref_file"],
                status=raw["status"],
                progress=effective_progress,
                next_blocker=raw["next_blocker"],
                next_blocker_task_filename=blocker_resolved,
                tasks=tasks,
                archived=archived,
            )
        )

    standalone_bugs = [StandaloneBug(**b) for b in bugs_raw]
    macro_tasks = [MacroTask(**m) for m in macros_raw]
    deferred_tasks = [DeferredTask(**d) for d in deferred_raw]

    return SystemState(
        registry_path   = str(registry_path),
        epics           = epics,
        standalone_bugs = standalone_bugs,
        macro_tasks     = macro_tasks,
        deferred_tasks  = deferred_tasks,
    )


# ---------------------------------------------------------------------------
# Task Content Loader & Model Extractor
# ---------------------------------------------------------------------------

_MODEL_PATTERN = re.compile(
    r"\*\*Modell:\*\*\s+([^\n|]+?)(?:\s*\||\s*\n|\s*$)",
    re.MULTILINE,
)
# Table / inline row: `| **Modell:** Sonnet |`
_MODEL_PIPE_PATTERN = re.compile(
    r"\|\s*\*\*Modell:\*\*\s*([^|\n]+?)\s*(?:\||$)",
    re.MULTILINE,
)

_LOCATION_PATTERN = re.compile(
    r"\*\*Ort:\*\*\s+([^\n|]+?)(?:\s*\||\s*\n|\s*$)",
    re.MULTILINE,
)
_LOCATION_PIPE_PATTERN = re.compile(
    r"\|\s*\*\*Ort:\*\*\s*([^|\n]+?)\s*(?:\||$)",
    re.MULTILINE,
)

_IST_PATTERN = re.compile(
    r"\*\*IST:\*\*\s+([^\n]+)",
    re.MULTILINE,
)

_SOLL_PATTERN = re.compile(
    r"\*\*SOLL:\*\*\s+([^\n]+)",
    re.MULTILINE,
)

_NEXT_PATTERN = re.compile(
    r"\*\*NEXT:\*\*\s+([^\n]+(?:\n[ \t]+[^\n]+)*)",
    re.MULTILINE,
)


class TaskMetadata(TypedDict, total=False):
    model: Optional[str]
    location: Optional[str]
    ist: Optional[str]
    soll: Optional[str]
    next_step: Optional[str]


def get_task_content(task_filename: str, repo_root: Optional[Path] = None) -> Optional[str]:
    """
    Read and return the raw markdown content of a task file.

    Args:
        task_filename: Just the filename, e.g. 'task_orchestrator_01_schema_and_parser.md'.
        repo_root:     Repo root path.  Defaults to three levels above this file.

    Returns:
        Full file content as string, or None if the file does not exist.
    """
    if repo_root is None:
        repo_root = Path(__file__).resolve().parent.parent.parent

    task_path = repo_root / "documentation" / "tasks" / task_filename

    if not task_path.exists():
        return None

    return task_path.read_text(encoding="utf-8")


def extract_model_from_task(content: str) -> Optional[str]:
    """
    Extract the model recommendation from a task file.

    Looks for '**Modell:** <value>' or table cells '| **Modell:** ... |'.

    Args:
        content: Full markdown content of the task file.

    Returns:
        Model name string (e.g. 'Claude 4.6 Sonnet'), or None if not found.
    """
    m = _MODEL_PATTERN.search(content)
    if m:
        return m.group(1).strip()
    m2 = _MODEL_PIPE_PATTERN.search(content)
    return m2.group(1).strip() if m2 else None


def extract_location_from_task(content: str) -> Optional[str]:
    """
    Extract the location (Ort) from a task file.

    Looks for '**Ort:** <value>' or '| **Ort:** ... |' table cells.

    Args:
        content: Full markdown content of the task file.

    Returns:
        Location string (e.g. 'AI Studio'), or None if not found.
    """
    m = _LOCATION_PATTERN.search(content)
    if m:
        return m.group(1).strip()
    m2 = _LOCATION_PIPE_PATTERN.search(content)
    return m2.group(1).strip() if m2 else None


def extract_ist_from_task(content: str) -> Optional[str]:
    """Extract the IST (current state) description from a task file."""
    m = _IST_PATTERN.search(content)
    return m.group(1).strip() if m else None


def extract_soll_from_task(content: str) -> Optional[str]:
    """Extract the SOLL (target state) description from a task file."""
    m = _SOLL_PATTERN.search(content)
    return m.group(1).strip() if m else None


def extract_next_from_task(content: str) -> Optional[str]:
    """Extract the NEXT action instruction from a task file.

    Captures the first line after **NEXT:** plus any indented continuation
    lines (sub-bullets), so multi-line instructions are preserved.
    """
    m = _NEXT_PATTERN.search(content)
    return m.group(1).strip() if m else None


def extract_metadata(content: str) -> TaskMetadata:
    """
    Extract model, location, IST, SOLL and NEXT metadata from a task file.

    Args:
        content: Full markdown content of the task file.

    Returns:
        TaskMetadata dict with 'model', 'location', 'ist', 'soll', 'next_step' keys.
    """
    return {
        "model":     extract_model_from_task(content),
        "location":  extract_location_from_task(content),
        "ist":       extract_ist_from_task(content),
        "soll":      extract_soll_from_task(content),
        "next_step": extract_next_from_task(content),
    }


# ---------------------------------------------------------------------------
# Completion Writer (Task 04) - Backup, FileLock, Registry Update
# ---------------------------------------------------------------------------

# Captures: (1) prefix, (2) checkbox, (3) mid, (4) filename, (5) closing backtick; optional "(desc)"
_TASK_LINE_REPLACE = re.compile(
    r"^(- \[)([ x])(\] \d+\. `)(task_[A-Za-z0-9_]+\.md)(`)(?: \([^)]+\))?\s*$",
    re.MULTILINE,
)


def _create_backup(file_path: Path) -> Path:
    """Create a .bak backup of the file via shutil.copy2."""
    backup_path = file_path.with_suffix(file_path.suffix + ".bak")
    shutil.copy2(file_path, backup_path)
    return backup_path


def _find_next_blocker(epic_content: str) -> Optional[str]:
    """
    Find the first open task ([ ]) in the epic content.
    Returns the task filename or None if all done.
    """
    for m in _TASK_LINE_REPLACE.finditer(epic_content):
        checkbox = m.group(2)
        if checkbox == " ":
            return m.group(4)
    return None


def _update_epic_task_checkbox(
    epic_content: str,
    task_filename: str,
) -> str:
    """
    Replace [ ] with [x] ONLY on the exact line that contains task_filename.

    Safety: uses re.sub anchored to the task_filename so that:
      - Only the checkbox immediately preceding `task_filename` is replaced.
      - No other `[ ]` on the page is touched (no cascade).
      - Already-[x] lines are idempotent (pattern only matches `[ ]`).
    """
    # Optional " (description)" after the closing backtick
    pattern = rf"- \[ \] (\d+\. `{re.escape(task_filename)}`)(?: \([^)]+\))?"
    replacement = r"- [x] \1"
    return re.sub(pattern, replacement, epic_content)


def _update_registry_epic_completion(
    registry_content: str,
    epic_ref_file: str,
    epic_content: str,
) -> str:
    """
    Mark an Epic as fully completed in the registry.

    When the last task of an Epic is closed, this function:
      1. Sets the **Status:** line to '\u2705 Completed'.
      2. Updates the **Progress:** counter to 'X/X Tasks' (all done).
      3. Removes the **N\u00c4CHSTER BLOCKER:** line entirely.

    Line-by-line: scoped to the target epic block only.
    """
    # Count total tasks from updated epic content
    all_tasks = _TASK_LINE_REPLACE.findall(epic_content)
    total = len(all_tasks)
    done  = sum(1 for t in all_tasks if t[1] == "x")
    progress_str = f"{done}/{total} Tasks"

    lines = registry_content.splitlines(keepends=True)
    result = []
    in_target_epic = False

    for line in lines:
        if line.startswith("### Epic:") and f"`{epic_ref_file}`" in line:
            in_target_epic = True
        elif line.startswith("### "):
            in_target_epic = False

        if in_target_epic:
            if "**Status:**" in line:
                line = re.sub(
                    r"(\*\*Status:\*\*\s+).+",
                    lambda m: m.group(1) + "✅ Completed",
                    line,
                )
            elif "**Progress:**" in line:
                _ps = progress_str  # capture for lambda
                line = re.sub(
                    r"(\*\*Progress:\*\*\s+).+",
                    lambda m: m.group(1) + _ps,
                    line,
                )
            elif "BLOCKER" in line and "**" in line:
                # Remove the NÄCHSTER BLOCKER line completely
                continue

        result.append(line)

    return "".join(result)


def _update_registry_blocker(
    registry_content: str,
    epic_ref_file: str,
    new_blocker: Optional[str],
) -> str:
    """
    Update the NÄCHSTER BLOCKER line for the given epic in the registry.
    Line-by-line: no DOTALL, no cross-section ambiguity.
    """
    lines = registry_content.splitlines(keepends=True)
    result = []
    in_target_epic = False

    for line in lines:
        # Detect the start of our target epic section
        if line.startswith("### Epic:") and f"`{epic_ref_file}`" in line:
            in_target_epic = True
        elif line.startswith("### "):
            in_target_epic = False

        # Replace BLOCKER value only inside the target section
        if in_target_epic and "BLOCKER" in line and "**" in line:
            blocker_val = new_blocker if new_blocker else ""
            line = re.sub(r"`[^`]*`", f"`{blocker_val}`", line, count=1)

        result.append(line)

    return "".join(result)


def approve_task(
    epic_ref_file: str,
    task_filename: str,
    repo_root: Optional[Path] = None,
) -> dict:
    """
    Complete a task: backup, lock, update epic checkbox, update registry blocker.

    Args:
        epic_ref_file: Relative path to epic markdown (e.g. 'documentation/features/epic_xyz.md').
        task_filename: The task file to mark done (e.g. 'task_orchestrator_04_completion_writer_with_backup.md').
        repo_root:     Repo root. Defaults to three levels above this file.

    Returns:
        Dict with status, backups created, and new blocker.

    Raises:
        FileNotFoundError: If epic or registry not found.
        ValueError: If task not found in epic.
    """
    if repo_root is None:
        repo_root = Path(__file__).resolve().parent.parent.parent

    epic_path = repo_root / epic_ref_file
    registry_path = repo_root / "01_CENTRAL_TASK_REGISTRY.md"

    if not epic_path.exists():
        raise FileNotFoundError(f"Epic not found: {epic_path}")
    if not registry_path.exists():
        raise FileNotFoundError(f"Registry not found: {registry_path}")

    # Lock both files
    epic_lock = FileLock(str(epic_path) + ".lock")
    registry_lock = FileLock(str(registry_path) + ".lock")

    with epic_lock, registry_lock:
        # Create backups
        epic_backup = _create_backup(epic_path)
        registry_backup = _create_backup(registry_path)

        # Read current content
        epic_content = epic_path.read_text(encoding="utf-8")
        registry_content = registry_path.read_text(encoding="utf-8")

        # Verify task exists in epic
        if task_filename not in epic_content:
            raise ValueError(f"Task {task_filename} not found in {epic_path}")

        # Update epic: mark task done
        new_epic_content = _update_epic_task_checkbox(epic_content, task_filename)

        # Find new blocker (first open task)
        new_blocker = _find_next_blocker(new_epic_content)

        # Update registry: blocker update OR full epic-completion
        if new_blocker is None:
            new_registry_content = _update_registry_epic_completion(
                registry_content, epic_ref_file, new_epic_content
            )
        else:
            new_registry_content = _update_registry_blocker(
                registry_content, epic_ref_file, new_blocker
            )

        # Write updated content
        epic_path.write_text(new_epic_content, encoding="utf-8")
        registry_path.write_text(new_registry_content, encoding="utf-8")

    return {
        "status": "success",
        "epic_backup": str(epic_backup),
        "registry_backup": str(registry_backup),
        "new_blocker": new_blocker,
    }


def _update_bug_status(
    registry_content: str,
    task_filename: str,
    new_status: str = "✅ Erledigt",
) -> str:
    """
    Update the Status of a standalone bug in the registry.
    Line-by-line: finds the Task line anchored on task_filename,
    then replaces the very next **Status:** line.
    """
    lines = registry_content.splitlines(keepends=True)
    result = []
    found_bug = False

    for line in lines:
        if not found_bug and f"`{task_filename}`" in line and "**Task:**" in line:
            found_bug = True
        elif found_bug and "**Status:**" in line:
            line = re.sub(r"(\*\*Status:\*\*\s+).+", rf"\1{new_status}", line)
            found_bug = False  # only update once

        result.append(line)

    return "".join(result)


def approve_bug(
    task_filename: str,
    repo_root: Optional[Path] = None,
) -> dict:
    """
    Mark a standalone bug as done in 01_CENTRAL_TASK_REGISTRY.md.

    Args:
        task_filename: Bug task filename (e.g. 'task_bug_websearch_xml.md').
        repo_root:     Repo root. Defaults to three levels above this file.

    Returns:
        Dict with status and registry_backup path.

    Raises:
        FileNotFoundError: If registry not found.
        ValueError: If task_filename not found in registry bugs section.
    """
    if repo_root is None:
        repo_root = Path(__file__).resolve().parent.parent.parent

    registry_path = repo_root / "01_CENTRAL_TASK_REGISTRY.md"

    if not registry_path.exists():
        raise FileNotFoundError(f"Registry not found: {registry_path}")

    registry_lock = FileLock(str(registry_path) + ".lock")

    with registry_lock:
        registry_content = registry_path.read_text(encoding="utf-8")

        if task_filename not in registry_content:
            raise ValueError(f"Bug {task_filename} not found in registry.")

        registry_backup = _create_backup(registry_path)
        new_content = _update_bug_status(registry_content, task_filename)
        registry_path.write_text(new_content, encoding="utf-8")

    return {
        "status": "success",
        "registry_backup": str(registry_backup),
    }


# ---------------------------------------------------------------------------
# Regex Robustness Unit Tests
# ---------------------------------------------------------------------------

def _run_unit_tests() -> bool:
    """
    Five unit tests verifying the context-bound regex is robust.
    Critical: Checkboxes in code blocks or non-task files must NOT match.
    """
    print("\n--- Running Unit Tests (Regex Robustness) ---")
    passed = 0
    total  = 5

    def check(label: str, condition: bool) -> None:
        nonlocal passed
        tag = "PASS ✅" if condition else "FAIL ❌"
        print(f"  [{tag}] {label}")
        if condition:
            passed += 1

    # T1: Open task is matched
    t1 = "- [ ] 1. `task_foo_01_bar.md` (Some description)"
    m1 = _TASK_LINE.match(t1)
    check(
        "T1: Open task matched",
        m1 is not None and m1.group(1) == " " and m1.group(2) == "task_foo_01_bar.md",
    )

    # T2: Done task [x] is matched
    t2 = "- [x] 2. `task_foo_02_done.md` (Completed task)"
    m2 = _TASK_LINE.match(t2)
    check(
        "T2: Done task [x] matched",
        m2 is not None and m2.group(1) == "x",
    )

    # T3: Plain checkbox in code block is NOT matched (no task_ filename)
    t3 = "- [ ] This is just a plain checkbox in a code block"
    check(
        "T3: Plain checkbox in code block NOT matched",
        _TASK_LINE.match(t3) is None,
    )

    # T4: Non-task_ filename is NOT matched
    t4 = "- [ ] 1. `some_random_file.md` (Not a task)"
    check(
        "T4: Non-task_ filename NOT matched",
        _TASK_LINE.match(t4) is None,
    )

    # T5: Missing number prefix is NOT matched
    t5 = "- [ ] `task_foo_01_bar.md` (Missing number)"
    check(
        "T5: Missing number prefix NOT matched",
        _TASK_LINE.match(t5) is None,
    )

    all_ok = passed == total
    print(f"\n--- Results: {passed}/{total} {'ALL PASSED ✅' if all_ok else 'FAILURES ❌'} ---")
    return all_ok


# ---------------------------------------------------------------------------
# Test Routine  (python parser.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    ok = _run_unit_tests()
    if not ok:
        print("\n❌ Unit tests failed. Fix regex before proceeding.")
        sys.exit(1)

    print("\n--- Loading Full System State ---")
    try:
        state = load_full_system_state()
    except FileNotFoundError as exc:
        print(f"\n❌ {exc}")
        sys.exit(1)

    print(f"Registry   : {state.registry_path}")
    print(f"Epics found: {len(state.epics)}")
    for epic in state.epics:
        open_tasks = sum(1 for t in epic.tasks if t.status == "open")
        done_tasks = sum(1 for t in epic.tasks if t.status == "done")
        print(f"  ├─ [{epic.status}] {epic.name}  "
              f"(tasks: {done_tasks} done / {open_tasks} open | "
              f"next: {epic.next_blocker})")
    print(f"Standalone bugs: {len(state.standalone_bugs)}")
    for bug in state.standalone_bugs:
        print(f"  └─ [{bug.priority}] {bug.task_filename}")
    print(f"Deferred tasks: {len(state.deferred_tasks)}")
    for dt in state.deferred_tasks:
        print(f"  └─ [{dt.prio}] {dt.task_id} — {dt.reason} (since {dt.since})")

    print("\n" + "=" * 60)
    print("FULL SYSTEM STATE (JSON):")
    print("=" * 60)
    print(state.model_dump_json(indent=2))
