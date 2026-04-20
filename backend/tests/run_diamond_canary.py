import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from backend.tools.pdf_editor import edit_pdf_text_in_place
from backend.utils.paths import get_user_docs_dir

DEFAULT_DOCS_DIR = Path(get_user_docs_dir())
DIAMOND_TEST_DIR = DEFAULT_DOCS_DIR / "diamond_test_pdfs"

CANARY_TARGETS = {
    "simple_paragraph.pdf": [
        {"search": "110,4 Mio Einwohner", "replace": "116,5 Mio Einwohner"},
    ],
    "multi_column.pdf": [
        {"search": "Spalte B: Faktencheck: Die Hauptstadt ist Berlin.", "replace": "Spalte B: Faktencheck: Die Hauptstadt ist Berlin ist immer noch schön."},
    ],
    "table_layout.pdf": [
        {"search": "Ägypten | 110,4 Mio | 1.010.000 km²", "replace": "Ägypten | 116,5 Mio | 1.010.000 km²"},
    ],
    "mixed_font_block.pdf": [
        {"search": "Die Fläche von Deutschland beträgt 357.000 km².", "replace": "Die Fläche von Deutschland beträgt 357.386 km²."},
    ],
    "column_footer.pdf": [
        {"search": "Kopfzeile: Zusammenfassung (falsch) - Bevölkerung 83 Mio.", "replace": "Kopfzeile: Zusammenfassung (korrekt) - Bevölkerung 83 Mio."},
    ],
}

async def run_canary() -> None:
    os.environ["JANUS_PDF_ENABLE_REBUILD_EXECUTION"] = "1"
    os.environ["JANUS_PDF_SHADOW_REBUILD"] = "1"
    os.environ["JANUS_PDF_WRITE_LAYOUT_SNAPSHOT"] = "1"

    pdfs = []
    for target_name, modifications in CANARY_TARGETS.items():
        pdf_path = DIAMOND_TEST_DIR / target_name
        if not pdf_path.exists():
            print(f"Skipping {target_name}: Datei fehlt")
            continue
        stale_target = DEFAULT_DOCS_DIR / f"{pdf_path.stem}_korrigiert{pdf_path.suffix}"
        if stale_target.exists():
            stale_target.unlink()
        print(f"Running canary for {target_name} using {len(modifications)} modifications")
        nested_original = Path("diamond_test_pdfs") / target_name
        result = await edit_pdf_text_in_place(
            original_filename=str(nested_original),
            modifications=modifications,
            edit_mode="rebuild_v1",
            shadow_run=True,
        )
        print(result)


def main() -> None:
    asyncio.run(run_canary())


if __name__ == "__main__":
    main()
