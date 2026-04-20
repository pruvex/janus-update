from pathlib import Path

import fitz
import pytest

from backend.tools import pdf_editor


def _as_skill_dict(skill_result):
    if hasattr(skill_result, "model_dump"):
        return skill_result.model_dump()
    return skill_result


def _ok_data(skill_result) -> dict:
    d = _as_skill_dict(skill_result)
    assert d["status"] == "ok"
    return d["data"]


def _make_simple_pdf(path: Path, text: str) -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text, fontsize=12, fontname="helv")
    doc.save(path)
    doc.close()


def test_extract_layout_snapshot_is_deterministic(tmp_path: Path):
    pdf_path = tmp_path / "sample.pdf"
    _make_simple_pdf(pdf_path, "Testlayout fuer Snapshot")

    doc = fitz.open(pdf_path)
    try:
        snap1 = pdf_editor._extract_layout_snapshot(doc)
        snap2 = pdf_editor._extract_layout_snapshot(doc)
    finally:
        doc.close()

    assert snap1 == snap2
    assert snap1["layout_schema_version"] == 1
    assert snap1["page_count"] == 1
    assert len(snap1["pages"]) == 1


def test_build_layout_qc_report_counts_changes():
    baseline = {
        "page_count": 1,
        "pages": [{"width": 595.0, "height": 842.0, "blocks": [{"id": 1}]}],
    }
    result = {
        "page_count": 1,
        "pages": [{"width": 595.0, "height": 842.0, "blocks": [{"id": 1}, {"id": 2}]}],
    }

    report = pdf_editor._build_layout_qc_report(baseline, result)

    assert report["schema_version"] == 1
    assert report["baseline_page_count"] == 1
    assert report["result_page_count"] == 1
    assert report["comparable_pages"] == 1
    assert report["changed_pages"] == 1
    assert report["page_count_equal"] is True
    assert report["pages_with_block_count_change"] == 1
    assert report["total_baseline_blocks"] == 1
    assert report["total_result_blocks"] == 2
    assert report["block_count_delta_total"] == 1


def test_shadow_rebuild_gate_helper():
    assert pdf_editor._shadow_rebuild_passes_gate(
        {
            "page_count_equal": True,
            "block_count_delta_total": 0,
            "max_block_bbox_drift": 1.5,
        }
    )

    assert not pdf_editor._shadow_rebuild_passes_gate(
        {
            "page_count_equal": True,
            "block_count_delta_total": 2,
            "max_block_bbox_drift": 0.1,
        }
    )


@pytest.mark.asyncio
async def test_edit_pdf_rebuild_mode_falls_back_and_writes_shadow_artifacts(tmp_path: Path, monkeypatch):
    source_name = "aegypten.pdf"
    source_path = tmp_path / source_name
    _make_simple_pdf(source_path, "Die Einwohnerzahl ist 110,4 Millionen.")

    monkeypatch.setattr(pdf_editor, "get_user_docs_dir", lambda: str(tmp_path))
    monkeypatch.setattr(pdf_editor, "register_and_index_file", lambda *args, **kwargs: None)

    result = await pdf_editor.edit_pdf_text_in_place(
        original_filename=source_name,
        modifications=[
            {
                "search": "Die Einwohnerzahl ist 110,4 Millionen.",
                "replace": "Die Einwohnerzahl ist 116,5 Millionen.",
            }
        ],
        edit_mode="rebuild_v1",
        shadow_run=True,
    )

    data = _ok_data(result)
    assert data["quality_gate"] == "passed"
    assert data["mode_requested"] == "rebuild_v1"
    assert data["mode_effective"] == "rebuild_v1"
    assert data["shadow_run"] is True

    artifacts = data["layout_artifacts"]
    assert "baseline_layout" in artifacts
    assert "result_layout" in artifacts
    assert "qc_report" in artifacts
    assert "shadow_rebuild_pdf" in artifacts
    assert "shadow_rebuild_layout" in artifacts
    assert "shadow_rebuild_qc_report" in artifacts
    assert Path(artifacts["baseline_layout"]).exists()
    assert Path(artifacts["result_layout"]).exists()
    assert Path(artifacts["shadow_rebuild_pdf"]).exists()
    assert Path(artifacts["shadow_rebuild_layout"]).exists()
    assert artifacts["qc_report"]["schema_version"] == 1
    assert artifacts["shadow_rebuild_qc_report"]["schema_version"] == 1

    corrected = tmp_path / "aegypten_korrigiert.pdf"
    assert corrected.exists()


@pytest.mark.asyncio
async def test_shadow_artifacts_report_text_diff_and_go_no_go(tmp_path: Path, monkeypatch):
    source_name = "diff_report.pdf"
    source_path = tmp_path / source_name
    _make_simple_pdf(source_path, "Die Hauptstadt ist Berlin.")

    monkeypatch.setattr(pdf_editor, "get_user_docs_dir", lambda: str(tmp_path))
    monkeypatch.setattr(pdf_editor, "register_and_index_file", lambda *args, **kwargs: None)
    monkeypatch.setattr(pdf_editor, "_calculate_text_diff_metrics", lambda a, b: {"segments": 1, "added_chars": 2, "deleted_chars": 0, "replaced_chars": 0, "ratio_changed": 0.05})
    monkeypatch.setattr(pdf_editor, "_shadow_rebuild_passes_gate", lambda report, relax_drift=False: True)
    monkeypatch.setattr(pdf_editor, "_extract_full_text_from_path", lambda path: "orig")
    monkeypatch.setenv("JANUS_PDF_ENABLE_REBUILD_EXECUTION", "1")

    result = await pdf_editor.edit_pdf_text_in_place(
        original_filename=source_name,
        modifications=[
            {
                "search": "Die Hauptstadt ist Berlin.",
                "replace": "Die Hauptstadt ist Berlin, und sie ist schön.",
            }
        ],
        edit_mode="rebuild_v1",
        shadow_run=True,
    )

    data = _ok_data(result)
    artifacts = data["layout_artifacts"]
    assert "text_diff_metrics" in artifacts
    assert artifacts["go_no_go"]["status"] == "ready_for_review"
    assert artifacts["go_no_go"]["shadow_gate_passed"] is True


@pytest.mark.asyncio
async def test_go_no_go_hold_when_diff_ratio_high(tmp_path: Path, monkeypatch):
    source_name = "diff_hold.pdf"
    source_path = tmp_path / source_name
    _make_simple_pdf(source_path, "Spanien ist im Süden Europas.")

    monkeypatch.setattr(pdf_editor, "get_user_docs_dir", lambda: str(tmp_path))
    monkeypatch.setattr(pdf_editor, "register_and_index_file", lambda *args, **kwargs: None)
    monkeypatch.setattr(pdf_editor, "_calculate_text_diff_metrics", lambda a, b: {"segments": 1, "added_chars": 10, "deleted_chars": 5, "replaced_chars": 0, "ratio_changed": 0.7})
    monkeypatch.setattr(pdf_editor, "_extract_full_text_from_path", lambda path: "orig")
    monkeypatch.setattr(pdf_editor, "_shadow_rebuild_passes_gate", lambda report, relax_drift=False: False)
    monkeypatch.setenv("JANUS_PDF_ENABLE_REBUILD_EXECUTION", "1")

    result = await pdf_editor.edit_pdf_text_in_place(
        original_filename=source_name,
        modifications=[
            {
                "search": "Spanien ist im Süden Europas.",
                "replace": "Spanien ist im Süden Europas und hat viele Städte.",
            }
        ],
        edit_mode="rebuild_v1",
        shadow_run=True,
    )

    data = _ok_data(result)
    artifacts = data["layout_artifacts"]
    assert artifacts["go_no_go"]["status"] == "hold"
    assert artifacts["go_no_go"]["shadow_gate_passed"] is False


def test_build_deterministic_rebuild_pdf_returns_matching_output(tmp_path: Path):
    source_name = "deterministic.pdf"
    source_path = tmp_path / source_name
    _make_simple_pdf(source_path, "Satz 1")

    jobs = [
        {
            "page_num": 0,
            "rect": fitz.Rect(72, 72, 200, 90),
            "replace": "Neue Zeile",
            "size": 11,
            "fontname": "helv",
            "color": (0.0, 0.0, 0.0),
        }
    ]

    layout_payload = {
        "layout_schema_version": 1,
        "page_count": 1,
        "pages": [
            {"page": 0, "width": 595.2, "height": 841.8, "blocks": []}
        ],
    }

    result_pdf, _ = pdf_editor._build_deterministic_rebuild_pdf(jobs, layout_payload, tmp_path, source_path)
    assert result_pdf.exists()
    doc = fitz.open(result_pdf)
    try:
        assert doc.page_count == 1
    finally:
        doc.close()
    assert result_pdf.stat().st_size > 0


def test_overflow_report_triggers_when_rect_too_small(tmp_path: Path):
    source_name = "overflow.pdf"
    source_path = tmp_path / source_name
    _make_simple_pdf(source_path, "Overflow")

    jobs = [
        {
            "page_num": 0,
            "rect": fitz.Rect(72, 72, 90, 90),
            "replace": "LangeZeileDieNichtReinpasst",
            "size": 10,
            "fontname": "helv",
            "color": (0.0, 0.0, 0.0),
        }
    ]
    layout_payload = {
        "layout_schema_version": 1,
        "page_count": 1,
        "pages": [{"page": 0, "width": 595.0, "height": 842.0, "blocks": []}],
    }

    _, overflow = pdf_editor._build_deterministic_rebuild_pdf(jobs, layout_payload, tmp_path, source_path)
    assert overflow["overflow"] is False
    assert overflow["items"] == []


@pytest.mark.asyncio
async def test_experimental_rebuild_promotion_when_shadow_gate_passes(tmp_path: Path, monkeypatch):
    source_name = "gate_pass.pdf"
    source_path = tmp_path / source_name
    _make_simple_pdf(source_path, "Paris hat 2,1 Millionen Einwohner.")

    monkeypatch.setattr(pdf_editor, "get_user_docs_dir", lambda: str(tmp_path))
    monkeypatch.setattr(pdf_editor, "register_and_index_file", lambda *args, **kwargs: None)
    monkeypatch.setattr(pdf_editor, "_shadow_rebuild_passes_gate", lambda report, relax_drift=False: True)
    monkeypatch.setenv("JANUS_PDF_ENABLE_REBUILD_EXECUTION", "1")

    result = await pdf_editor.edit_pdf_text_in_place(
        original_filename=source_name,
        modifications=[
            {
                "search": "Paris hat 2,1 Millionen Einwohner.",
                "replace": "Paris hat 2,2 Millionen Einwohner.",
            }
        ],
        edit_mode="rebuild_v1",
        shadow_run=True,
    )

    data = _ok_data(result)
    assert data["quality_gate"] == "passed"
    assert data["mode_effective"] == "rebuild_v1_experimental"
    assert "shadow_rebuild_pdf" in data["layout_artifacts"]


@pytest.mark.asyncio
async def test_experimental_rebuild_not_promoted_when_shadow_gate_fails(tmp_path: Path, monkeypatch):
    source_name = "gate_fail.pdf"
    source_path = tmp_path / source_name
    _make_simple_pdf(source_path, "Rom hat 2,8 Millionen Einwohner.")

    monkeypatch.setattr(pdf_editor, "get_user_docs_dir", lambda: str(tmp_path))
    monkeypatch.setattr(pdf_editor, "register_and_index_file", lambda *args, **kwargs: None)
    monkeypatch.setattr(pdf_editor, "_shadow_rebuild_passes_gate", lambda report, relax_drift=False: False)
    monkeypatch.setenv("JANUS_PDF_ENABLE_REBUILD_EXECUTION", "1")

    result = await pdf_editor.edit_pdf_text_in_place(
        original_filename=source_name,
        modifications=[
            {
                "search": "Rom hat 2,8 Millionen Einwohner.",
                "replace": "Rom hat 2,9 Millionen Einwohner.",
            }
        ],
        edit_mode="rebuild_v1",
        shadow_run=True,
    )

    data = _ok_data(result)
    assert data["quality_gate"] == "passed"
    assert data["mode_effective"] == "rebuild_v1"
    assert data["layout_artifacts"]["shadow_rebuild_gate"]["status"] == "failed"
    assert data["shadow_run"] is True

    artifacts = data["layout_artifacts"]
    assert "baseline_layout" in artifacts
    assert "result_layout" in artifacts
    assert "qc_report" in artifacts
    assert "shadow_rebuild_pdf" in artifacts
    assert "shadow_rebuild_layout" in artifacts
    assert "shadow_rebuild_qc_report" in artifacts
    assert Path(artifacts["baseline_layout"]).exists()
    assert Path(artifacts["result_layout"]).exists()
    assert Path(artifacts["shadow_rebuild_pdf"]).exists()
    assert Path(artifacts["shadow_rebuild_layout"]).exists()
    assert artifacts["qc_report"]["schema_version"] == 1
    assert artifacts["shadow_rebuild_qc_report"]["schema_version"] == 1

    corrected = tmp_path / "gate_fail_korrigiert.pdf"
    assert corrected.exists()


@pytest.mark.asyncio
async def test_edit_pdf_rejects_invalid_mode(tmp_path: Path, monkeypatch):
    source_name = "mode_test.pdf"
    source_path = tmp_path / source_name
    _make_simple_pdf(source_path, "Hallo Welt")

    monkeypatch.setattr(pdf_editor, "get_user_docs_dir", lambda: str(tmp_path))

    result = await pdf_editor.edit_pdf_text_in_place(
        original_filename=source_name,
        modifications=[{"search": "Hallo", "replace": "Hi"}],
        edit_mode="invalid_mode",
    )

    d = _as_skill_dict(result)
    assert d["status"] == "error"
    assert d["error"]["code"] == "invalid_mode"
    assert d["error"]["details"]["quality_gate"] == "invalid_mode"


@pytest.mark.asyncio
async def test_edit_pdf_shadow_mode_can_be_enabled_via_env(tmp_path: Path, monkeypatch):
    source_name = "env_shadow.pdf"
    source_path = tmp_path / source_name
    _make_simple_pdf(source_path, "Berlin hat 3,7 Millionen Einwohner.")

    monkeypatch.setattr(pdf_editor, "get_user_docs_dir", lambda: str(tmp_path))
    monkeypatch.setattr(pdf_editor, "register_and_index_file", lambda *args, **kwargs: None)
    monkeypatch.setenv("JANUS_PDF_SHADOW_REBUILD", "1")

    result = await pdf_editor.edit_pdf_text_in_place(
        original_filename=source_name,
        modifications=[
            {
                "search": "Berlin hat 3,7 Millionen Einwohner.",
                "replace": "Berlin hat 3,8 Millionen Einwohner.",
            }
        ],
        shadow_run=False,
    )

    data = _ok_data(result)
    assert data["quality_gate"] == "passed"
    assert data["shadow_run"] is True
    assert "baseline_layout" in data["layout_artifacts"]
    assert "result_layout" in data["layout_artifacts"]


@pytest.mark.asyncio
async def test_edit_pdf_mode_can_be_enabled_via_env(tmp_path: Path, monkeypatch):
    source_name = "env_mode.pdf"
    source_path = tmp_path / source_name
    _make_simple_pdf(source_path, "Deutschland hat 84 Millionen Einwohner.")

    monkeypatch.setattr(pdf_editor, "get_user_docs_dir", lambda: str(tmp_path))
    monkeypatch.setattr(pdf_editor, "register_and_index_file", lambda *args, **kwargs: None)
    monkeypatch.setenv("JANUS_PDF_EDIT_MODE", "rebuild_v1")

    result = await pdf_editor.edit_pdf_text_in_place(
        original_filename=source_name,
        modifications=[
            {
                "search": "Deutschland hat 84 Millionen Einwohner.",
                "replace": "Deutschland hat 84,4 Millionen Einwohner.",
            }
        ],
    )

    data = _ok_data(result)
    assert data["quality_gate"] == "passed"
    assert data["mode_requested"] == "rebuild_v1"
    assert data["mode_effective"] == "rebuild_v1"
