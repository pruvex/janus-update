"""
Diamond Task Orchestrator UI - Dashboard
=========================================
Category : C7 (Code-Gen)
Task     : task_orchestrator_02_streamlit_ui_layout.md
Version  : 1.0

Run with:
    streamlit run tools/orchestrator_ui/app.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

# Allow direct import of parser.py from the same package directory
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import streamlit.components.v1 as components
from parser import (
    DeferredTask,
    Epic,
    MacroTask,
    MicroTask,
    StandaloneBug,
    SystemState,
    approve_bug,
    approve_task,
    extract_metadata,
    get_task_content,
    load_full_system_state,
)

# Repo root: tools/orchestrator_ui/app.py -> tools/orchestrator_ui -> tools -> repo_root
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------------------------
# Page Config  (must be first Streamlit call)
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Diamond Task Orchestrator",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Style helpers & Clipboard
# ---------------------------------------------------------------------------

_STATUS_COLORS: dict[str, str] = {
    "In Development": "#f59e0b",
    "Design Phase":   "#3b82f6",
    "Done":           "#22c55e",
    "TODO":           "#ef4444",  # Red for open tasks
    "IN_PROGRESS":    "#f59e0b",  # Orange for active
    "DEFERRED":       "#6b7280",  # Gray for deferred
    "Blocked":        "#ef4444",
}

_PRIORITY_COLORS: dict[str, str] = {
    "Hoch":    "#ef4444",
    "Mittel":  "#f59e0b",
    "Niedrig": "#22c55e",
}

# Priority colors for Macro-Tasks (P0-P3)
_PRIO_COLORS: dict[str, str] = {
    "P0": "#ef4444",  # Critical - Red
    "P1": "#f59e0b",  # High - Orange
    "P2": "#3b82f6",  # Medium - Blue
    "P3": "#22c55e",  # Low - Green
}


def _badge(text: str, color_map: dict[str, str], default: str = "#6b7280") -> str:
    color = color_map.get(text, default)
    return (
        f'<span style="background:{color};color:#fff;padding:2px 10px;'
        f'border-radius:12px;font-size:0.78em;font-weight:700;">{text}</span>'
    )


def _progress_html(progress_str: str) -> str:
    """Convert '1/5 Tasks' to an inline HTML progress bar."""
    try:
        left, right = progress_str.split("/")
        done  = int(left.strip())
        total = int(right.strip().split()[0])
        pct   = int(done / total * 100) if total else 0
    except Exception:
        return f"<code>{progress_str}</code>"

    bar_color = "#22c55e" if pct == 100 else "#3b82f6"
    return (
        f'<div style="display:flex;align-items:center;gap:8px;">'
        f'<div style="background:#e5e7eb;border-radius:6px;height:10px;width:140px;">'
        f'<div style="background:{bar_color};width:{pct}%;height:10px;border-radius:6px;"></div>'
        f'</div>'
        f'<span style="font-size:0.85em;color:#374151;">{done}/{total}</span>'
        f'</div>'
    )


def _make_copy_html(content: str) -> str:
    """Return a self-executing HTML snippet that copies *content* to the clipboard.

    Uses document.execCommand('copy') via a hidden textarea — this works inside
    Streamlit's sandboxed iframe (allow-scripts only) where navigator.clipboard
    is blocked by the missing allow-same-origin attribute.
    """
    safe = json.dumps(content)  # escapes newlines, quotes, backticks etc.
    return (
        "<html><body>"
        "<script>"
        "(function(){"
        f"var el=document.createElement('textarea');"
        f"el.value={safe};"
        "el.style.cssText='position:fixed;top:-9999px;font-size:12pt;opacity:0';"
        "document.body.appendChild(el);"
        "el.focus();el.select();el.setSelectionRange(0,99999);"
        "try{document.execCommand('copy');}catch(e){}"
        "document.body.removeChild(el);"
        "})();"
        "</script>"
        "</body></html>"
    )


def render_copy_button(text_to_copy: str) -> None:
    """Render a styled copy-button as an HTML component.

    The button lives *inside* the iframe so the browser treats the click as a
    direct user gesture — the only reliable way to get clipboard write access
    in a sandboxed Streamlit environment.

    navigator.clipboard.writeText() succeeds here because the call originates
    from the onclick handler (user gesture), not from an auto-running script.
    """
    safe = json.dumps(text_to_copy)
    html = f"""
<html>
<head><style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: transparent; }}
  .btn {{
    display: block;
    width: 100%;
    height: 38px;
    background: #f0f2f6;
    color: #31333f;
    border: 1px solid rgba(49,51,63,0.2);
    border-radius: 0.5rem;
    font-size: 0.875rem;
    font-family: "Source Sans Pro", sans-serif;
    font-weight: 400;
    cursor: pointer;
    transition: background 0.15s, border-color 0.15s;
  }}
  .btn:hover  {{ background: #e4e6eb; border-color: rgba(49,51,63,0.4); }}
  .btn:active {{ background: #d5d7de; }}
  .btn.ok     {{ background: #d4edda; color: #155724; border-color: #c3e6cb; }}
</style></head>
<body>
<button class="btn" id="b" onclick="doCopy()">&#128203; Copy Prompt</button>
<script>
var _text = {safe};
function doCopy() {{
  var btn = document.getElementById('b');
  navigator.clipboard.writeText(_text)
    .then(function() {{
      btn.textContent = '\u2705 Kopiert!';
      btn.classList.add('ok');
      setTimeout(function() {{
        btn.textContent = '\U0001f4cb Copy Prompt';
        btn.classList.remove('ok');
      }}, 2000);
    }})
    .catch(function() {{
      btn.textContent = '\u26a0\ufe0f Fehler';
      setTimeout(function() {{ btn.textContent = '\U0001f4cb Copy Prompt'; }}, 2000);
    }});
}}
</script>
</body></html>"""
    components.html(html, height=40, scrolling=False)


# ---------------------------------------------------------------------------
# Data loading (cached, auto-expires every 30 s)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=30)
def _load() -> dict:
    """Return SystemState as plain dict for Streamlit cache compatibility."""
    return load_full_system_state().model_dump()


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def _render_sidebar(state: SystemState) -> None:
    with st.sidebar:
        st.header("⚙️ Steuerung")

        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        st.divider()
        st.caption(f"Stand: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        st.caption("Quelle: `01_CENTRAL_TASK_REGISTRY.md`")
        st.divider()

        st.subheader("📊 Kennzahlen")
        total_tasks = sum(len(e.tasks) for e in state.epics)
        done_tasks  = sum(
            sum(1 for t in e.tasks if t.status == "done")
            for e in state.epics
        )
        n_active = sum(1 for e in state.epics if not e.archived)
        st.metric("Epics", len(state.epics))
        st.caption(f"Aktiv im Radar: {n_active} · Archiviert: {len(state.epics) - n_active}")
        st.metric("Tasks erledigt", f"{done_tasks} / {total_tasks}")
        st.metric("Offene Bugs",  len(state.standalone_bugs))
        st.metric("Macro-Tasks",  len(state.macro_tasks))
        st.metric("🔒 Deferred", len(state.deferred_tasks))


# ---------------------------------------------------------------------------
# Tab 1 – Epic overview table
# ---------------------------------------------------------------------------

def _render_overview(epics: list[Epic], macro_tasks: list[MacroTask]) -> None:
    # --- Epics Section ---
    st.subheader("🚀 Aktive Epics")

    if epics:
        # Column headers
        h0, h1, h2, h3 = st.columns([3, 2, 2, 3])
        h0.markdown("**Epic**")
        h1.markdown("**Status**")
        h2.markdown("**Progress**")
        h3.markdown("**Nächster Blocker**")
        st.divider()

        for epic in epics:
            c0, c1, c2, c3 = st.columns([3, 2, 2, 3])
            c0.markdown(f"**{epic.name}**")
            c1.markdown(_badge(epic.status, _STATUS_COLORS), unsafe_allow_html=True)
            c2.markdown(_progress_html(epic.progress), unsafe_allow_html=True)
            blocker = f"`{epic.next_blocker}`" if epic.next_blocker else "—"
            c3.markdown(blocker)
    else:
        st.info("Keine Epics in der Registry gefunden.")

    st.divider()

    # --- Macro-Tasks Section (TODO only) ---
    st.subheader("📋 Offene Macro-Tasks (TODO)")

    todo_macros = [m for m in macro_tasks if m.status.upper() == "TODO"]

    if todo_macros:
        # Column headers
        h0, h1, h2, h3, h4 = st.columns([1.5, 0.8, 1.2, 1.5, 4])
        h0.markdown("**Task-ID**")
        h1.markdown("**CU**")
        h2.markdown("**Prio**")
        h3.markdown("**App/Modell**")
        h4.markdown("**Master-Prompt**")
        st.divider()

        for task in todo_macros:
            c0, c1, c2, c3, c4 = st.columns([1.5, 0.8, 1.2, 1.5, 4])
            c0.markdown(f"`{task.task_id}`")
            c1.markdown(str(task.cu))
            c2.markdown(_badge(task.prio, _PRIO_COLORS), unsafe_allow_html=True)
            c3.markdown(f"{task.app}<br/>{task.model}", unsafe_allow_html=True)
            c4.markdown(f"*{task.master_prompt}*")
    else:
        st.success("✅ Keine offenen Macro-Tasks — alles erledigt!")


# ---------------------------------------------------------------------------
# Approve Action with Feedback
# ---------------------------------------------------------------------------

def on_approve_click(epic_ref_file: str, task_filename: str) -> None:
    """
    Execute approve_task and provide Streamlit feedback.
    st.rerun() is placed OUTSIDE the try block so that Streamlit's
    internal RerunException is never swallowed by except.
    """
    error_occurred = False
    try:
        result = approve_task(epic_ref_file, task_filename, _REPO_ROOT)
        new_blocker = result.get("new_blocker")
        st.cache_data.clear()  # force fresh registry + epic data on rerun
        if new_blocker:
            st.success(f"✅ Task abgeschlossen! Nächster Blocker: `{new_blocker}`")
        else:
            st.success("✅ Task abgeschlossen! Epic ist fertig.")
    except Exception as exc:
        st.error(f"❌ Fehler beim Abschließen: {exc}")
        error_occurred = True

    if not error_occurred:
        st.rerun()


# ---------------------------------------------------------------------------
# Tab 2 – Epic task checklists
# ---------------------------------------------------------------------------

def _is_real_task_artifact(filename: str) -> bool:
    """True if this row maps to a real `documentation/tasks/*.md` file (not synthetic / rollup)."""
    if not filename or not filename.endswith(".md"):
        return False
    if filename.startswith("synthetic_") or filename.startswith("__"):
        return False
    return True


def _render_details(epics: list[Epic]) -> None:
    st.subheader("📋 Task-Checklisten")

    if not epics:
        st.info("Keine Epics vorhanden.")
        return

    for epic in epics:
        done_n  = sum(1 for t in epic.tasks if t.status == "done")
        open_n  = sum(1 for t in epic.tasks if t.status == "open")
        total_n = done_n + open_n

        label = f"{epic.name}  —  {done_n}/{total_n} erledigt"
        expand = open_n > 0 and done_n < total_n

        with st.expander(label, expanded=expand):
            if not epic.tasks:
                st.caption("Epic-Datei nicht gefunden oder enthält keine Task-Zeilen.")
                st.caption(f"Ref: `{epic.ref_file}`")
                st.divider()
                continue

            for task in epic.tasks:
                done_icon = "✅" if task.status == "done" else "⬜"
                is_blocker = (
                    epic.next_blocker_task_filename is not None
                    and task.filename == epic.next_blocker_task_filename
                )

                if task.status == "done" or not _is_real_task_artifact(task.filename):
                    st.markdown(
                        f"{done_icon} `{task.filename}`  \n"
                        f"&nbsp;&nbsp;&nbsp;&nbsp;_{task.description}_"
                    )
                    continue

                content = get_task_content(task.filename, _REPO_ROOT)
                meta = extract_metadata(content) if content else {}
                model = meta.get("model")
                location = meta.get("location")
                key_sfx = f"{epic.name}_{task.filename}".replace(" ", "_").replace("/", "_")

                col_info, col_copy, col_done = st.columns([3, 1.2, 1.2])

                with col_info:
                    ist = meta.get("ist")
                    soll = meta.get("soll")
                    blocker_tag = "🔴 **NÄCHSTER BLOCKER** — " if is_blocker else ""
                    st.markdown(
                        f"{done_icon} {blocker_tag}`{task.filename}`  \n"
                        f"<span style='color:#6b7280;font-size:0.85em;'>_{task.description}_</span>",
                        unsafe_allow_html=True,
                    )
                    if ist or soll:
                        ist_line = f"🔴 **IST:** {ist}" if ist else ""
                        soll_line = f"🟢 **SOLL:** {soll}" if soll else ""
                        separator = "  \n" if ist and soll else ""
                        st.caption(f"{ist_line}{separator}{soll_line}")
                    badges = []
                    if model:
                        badges.append(
                            f'<span style="background:#fef3c7;color:#92400e;'
                            f'padding:2px 8px;border-radius:4px;font-size:0.78em;'
                            f'font-weight:700;border:1px solid #fcd34d;margin-right:6px;">'
                            f'🏷️ Modell: {model}</span>'
                        )
                    if location:
                        loc_icon = "🧠" if "AI Studio" in location else "💻"
                        badges.append(
                            f'<span style="background:#e0f2fe;color:#0369a1;'
                            f'padding:2px 8px;border-radius:4px;font-size:0.78em;'
                            f'font-weight:700;border:1px solid #7dd3fc;">'
                            f'📍 Ort: {loc_icon} {location}</span>'
                        )
                    if badges:
                        st.markdown("".join(badges), unsafe_allow_html=True)

                with col_copy:
                    if content:
                        render_copy_button(content)
                    else:
                        st.warning("⚠️ Datei fehlt")

                with col_done:
                    if st.button(
                        "✅ Mark Done",
                        key=f"done_{key_sfx}",
                        use_container_width=True,
                    ):
                        on_approve_click(epic.ref_file, task.filename)

                next_step = meta.get("next_step")
                if next_step:
                    st.info(f"🚀 **Next Action:** {next_step}")

            st.divider()
            st.caption(f"Ref: `{epic.ref_file}`")


# ---------------------------------------------------------------------------
# Bug Approve Action
# ---------------------------------------------------------------------------

def on_approve_bug_click(task_filename: str) -> None:
    """
    Execute approve_bug and provide Streamlit feedback.
    """
    error_occurred = False
    try:
        approve_bug(task_filename, _REPO_ROOT)
        st.cache_data.clear()
        st.success(f"✅ Bug `{task_filename}` als erledigt markiert!")
    except Exception as exc:
        st.error(f"❌ Fehler: {exc}")
        error_occurred = True

    if not error_occurred:
        st.rerun()


# ---------------------------------------------------------------------------
# Tab 3 – Standalone bugs & audits
# ---------------------------------------------------------------------------

_DONE_KEYWORDS = ("✅", "erledigt", "done", "closed", "geschlossen")


def _is_bug_done(status: str) -> bool:
    return any(kw in status.lower() for kw in _DONE_KEYWORDS)


def _render_bugs(bugs: list[StandaloneBug]) -> None:
    st.subheader("🐛 Isolierte Bugfixes & Audits")

    if not bugs:
        st.success("Keine offenen Bugs.")
        return

    open_bugs  = [b for b in bugs if not _is_bug_done(b.status)]
    done_bugs  = [b for b in bugs if _is_bug_done(b.status)]

    # --- Open bugs: interactive action rows ---
    if open_bugs:
        st.markdown("**Offen**")
        for bug in open_bugs:
            key_sfx = bug.task_filename.replace(".", "_")
            content  = get_task_content(bug.task_filename, _REPO_ROOT)
            meta     = extract_metadata(content) if content else {}
            model    = meta.get("model")
            location = meta.get("location")
            ist      = meta.get("ist")
            soll     = meta.get("soll")
            next_step = meta.get("next_step")

            # --- [3, 1.2, 1.2] layout: info | copy | done ---
            col_info, col_copy, col_done = st.columns([3, 1.2, 1.2])

            with col_info:
                st.markdown(
                    f"🔴 **`{bug.task_filename}`**  \n"
                    f"<span style='color:#6b7280;font-size:0.85em;'>"
                    f"Ref: `{bug.ref}`"
                    f"</span>",
                    unsafe_allow_html=True,
                )
                if ist or soll:
                    ist_line  = f"🔴 **IST:** {ist}" if ist else ""
                    soll_line = f"🟢 **SOLL:** {soll}" if soll else ""
                    separator = "  \n" if ist and soll else ""
                    st.caption(f"{ist_line}{separator}{soll_line}")
                badges = [
                    f'<span style="background:#fee2e2;color:#991b1b;'
                    f'padding:2px 8px;border-radius:4px;font-size:0.78em;'
                    f'font-weight:700;border:1px solid #fca5a5;margin-right:6px;">'
                    f'🔥 {bug.priority}</span>'
                ]
                if model:
                    badges.append(
                        f'<span style="background:#fef3c7;color:#92400e;'
                        f'padding:2px 8px;border-radius:4px;font-size:0.78em;'
                        f'font-weight:700;border:1px solid #fcd34d;margin-right:6px;">'
                        f'🏷️ Modell: {model}</span>'
                    )
                if location:
                    loc_icon = "🧠" if "AI Studio" in location else "💻"
                    badges.append(
                        f'<span style="background:#e0f2fe;color:#0369a1;'
                        f'padding:2px 8px;border-radius:4px;font-size:0.78em;'
                        f'font-weight:700;border:1px solid #7dd3fc;">'
                        f'📍 Ort: {loc_icon} {location}</span>'
                    )
                st.markdown("".join(badges), unsafe_allow_html=True)

            with col_copy:
                if content:
                    render_copy_button(content)
                else:
                    st.caption("⚠️ Kein Inhalt")

            with col_done:
                if st.button("✅ Mark Done",
                             key=f"bug_done_{key_sfx}",
                             use_container_width=True):
                    on_approve_bug_click(bug.task_filename)

            # Next Action box
            if next_step:
                st.info(f"🚀 **Next Action:** {next_step}")

            st.divider()

    # --- Done bugs: compact list ---
    if done_bugs:
        with st.expander(f"✅ Erledigte Bugs ({len(done_bugs)})", expanded=False):
            for bug in done_bugs:
                st.markdown(
                    f"✅ ~~`{bug.task_filename}`~~ — "
                    f"<span style='color:#6b7280;font-size:0.85em;'>{bug.status}</span>",
                    unsafe_allow_html=True,
                )


# ---------------------------------------------------------------------------
# Tab 4 – Macro-Dashboard Tasks
# ---------------------------------------------------------------------------

def _render_macro_tasks(macro_tasks: list[MacroTask]) -> None:
    st.subheader("📋 Macro-Dashboard Tasks")

    if not macro_tasks:
        st.info("Keine Macro-Tasks in der Registry gefunden.")
        return

    # Column headers (V3.0 — 7 Spalten mit Tags + Meilenstein)
    h0, h1, h2, h3, h4, h5, h6 = st.columns([1.2, 0.8, 1.2, 1.2, 1.5, 2, 2.5])
    h0.markdown("**Task-ID**")
    h1.markdown("**CU**")
    h2.markdown("**Status**")
    h3.markdown("**App/Modell**")
    h4.markdown("**Tags**")
    h5.markdown("**Meilenstein**")
    h6.markdown("**Master-Prompt**")
    st.divider()

    for task in macro_tasks:
        c0, c1, c2, c3, c4, c5, c6 = st.columns([1.2, 0.8, 1.2, 1.2, 1.5, 2, 2.5])
        c0.markdown(f"`{task.task_id}`")
        c1.markdown(str(task.cu))
        c2.markdown(_badge(task.status, _STATUS_COLORS), unsafe_allow_html=True)
        c3.markdown(f"{task.app}<br/>{task.model}", unsafe_allow_html=True)
        c4.markdown(f"<small>{task.tags}</small>", unsafe_allow_html=True)
        c5.markdown(f"_{task.meilenstein}_" if task.meilenstein else "—")
        c6.markdown(f"*{task.master_prompt}*")


# ---------------------------------------------------------------------------
# Tab 5 – Deferred Pool (Warteschlange)
# ---------------------------------------------------------------------------

_DEFERRED_PRIO_COLORS: dict[str, str] = {
    "P0": "#ef4444",  # Critical - Rot
    "P1": "#f59e0b",  # High - Orange
    "P2": "#3b82f6",  # Medium - Blau
    "P3": "#22c55e",  # Low - Grün
}


def _render_deferred(deferred_tasks: list[DeferredTask]) -> None:
    st.subheader("🔒 DEFERRED Pool — Warteschlange")
    st.caption("Tasks, die auf Ressourcen-Freigabe warten (Quota erschöpft oder Loop-Fail)")

    if not deferred_tasks:
        st.success("✅ Keine Tasks im DEFERRED Pool — alle Systeme operational!")
        return

    # Warnung wenn Deferred Tasks vorhanden
    st.warning(f"⚠️ **{len(deferred_tasks)} Task(s) blockiert** — Quota- oder Ressourcen-Limit erreicht")

    # Column headers
    h0, h1, h2, h3, h4, h5, h6 = st.columns([1.5, 1, 2, 2, 2, 1.5, 3])
    h0.markdown("**Task-ID**")
    h1.markdown("**CU**")
    h2.markdown("**CU-Log**")
    h3.markdown("**Editor**")
    h4.markdown("**Grund**")
    h5.markdown("**Prio**")
    h6.markdown("**Entblockung**")
    st.divider()

    for dt in deferred_tasks:
        c0, c1, c2, c3, c4, c5, c6 = st.columns([1.5, 1, 2, 2, 2, 1.5, 3])
        c0.markdown(f"`{dt.task_id}`")
        c1.markdown(str(dt.cu))
        c2.markdown(f"_{dt.cu_log}_")
        c3.markdown(dt.original_editor)
        c4.markdown(dt.reason)
        # Priority with color badge
        prio_color = _DEFERRED_PRIO_COLORS.get(dt.prio.upper(), "#6b7280")
        c5.markdown(
            f'<span style="background:{prio_color};color:#fff;padding:2px 8px;'
            f'border-radius:4px;font-size:0.78em;font-weight:700;">'
            f'{dt.prio}</span>',
            unsafe_allow_html=True
        )
        c6.markdown(f"_{dt.unblock_condition}_")

    st.divider()
    st.info("💡 **DEFERRED → ACTIVE Transition:** Wenn Quota wieder verfügbar → Status: TODO → Editor-Zuweisung")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    st.title("💎 Diamond Task Orchestrator")
    st.caption("Diamond-OS V2.5 — Operational Dashboard")

    try:
        raw   = _load()
        state = SystemState(**raw)
    except FileNotFoundError as exc:
        st.error(f"❌ Registry nicht gefunden: {exc}")
        st.stop()
    except Exception as exc:
        st.error(f"❌ Ladefehler: {exc}")
        st.stop()

    _render_sidebar(state)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Übersicht", "📋 Task-Details", "🐛 Bugs & Audits", "📋 Macro-Tasks", "🔒 Deferred"])

    with tab1:
        active_epics = [e for e in state.epics if not e.archived]
        _render_overview(active_epics, state.macro_tasks)

    with tab2:
        _render_details([e for e in state.epics if not e.archived])

    with tab3:
        _render_bugs(state.standalone_bugs)

    with tab4:
        _render_macro_tasks(state.macro_tasks)

    with tab5:
        _render_deferred(state.deferred_tasks)


if __name__ == "__main__":
    main()
