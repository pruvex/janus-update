import sys
from pathlib import Path

# Pfad-Setup (Datei liegt in backend/tests/tools)
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.data.database import SessionLocal
from backend.services.vision_service import vision_service
from backend.services.vision.utils import get_mapped_portrait_facts


def _analyze_image(image_path: Path) -> dict:
    db = SessionLocal()
    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        result = vision_service.process_image(image_bytes, db, image_name=image_path.name)
        facts = get_mapped_portrait_facts(
            result.get("feature_report", {}),
            result.get("context", {}),
            vision_mode="eval",
        )

        rendered = " ".join(
            [
                str(facts.get("KLEIDUNG", "")),
                str(facts.get("MATERIAL_SATZ", "")),
                str(facts.get("LEGWEAR_SATZ", "")),
                str(facts.get("OUTERWEAR_SATZ", "")),
                str(result.get("local_description", "")),
            ]
        )

        report_text = ""
        for category_items in (result.get("feature_report", {}) or {}).values():
            if isinstance(category_items, list):
                report_text += " " + " ".join(str(i.get("label", "")) for i in category_items)

        return {
            "result": result,
            "facts": facts,
            "rendered": rendered,
            "report_text": report_text,
        }
    finally:
        db.close()


def run_sequence_test() -> int:
    image1 = Path("backend/tests/vision_matrix/cluster_3/Cluster3-1.jpg")  # Frau mit Schal
    image2 = Path("backend/tests/vision_matrix/cluster_3/Cluster3-2.jpg")  # Frau mit Rollkragen

    if not image1.exists() or not image2.exists():
        print("❌ Testbilder fehlen:", image1, image2)
        return 2

    print("=== SEQUENCE TEST: Bild 1 -> Bild 2 im selben Prozess ===")
    print(f"Bild 1: {image1}")
    first = _analyze_image(image1)
    print(f"Bild 2: {image2}")
    second = _analyze_image(image2)

    print("\n--- Ergebnis Bild 1 (Fakten) ---")
    for key in ["OUTFIT_OBEN", "MUSTER_INFO", "HAAR_DETAILS"]:
        print(f"{key}: {first['facts'].get(key, '')}")

    print("\n--- Ergebnis Bild 2 (Fakten) ---")
    for key in ["OUTFIT_OBEN", "OUTFIT_UNTEN", "MUSTER_INFO", "HAAR_DETAILS"]:
        print(f"{key}: {second['facts'].get(key, '')}")

    preview_text = (
        f"Auf dem Bild sehe ich {second['facts'].get('ALTER_GESCHLECHT_SATZ', 'eine Person')}. "
        f"Die Physis wirkt {second['facts'].get('TEINT', '')}, {second['facts'].get('AUGEN', '')}, {second['facts'].get('HAAR_DETAILS', '')}. "
        f"Oben trägt die Person {second['facts'].get('OUTFIT_OBEN', '')}, unten {second['facts'].get('OUTFIT_UNTEN', '')}. "
        f"{second['facts'].get('AMBIENTE_SATZ', '')}"
    )
    print("\n--- Structured Reporter Preview (Bild 2) ---")
    print(preview_text)

    first_all_text = (
        str(first["rendered"]) + " " + str(first["report_text"]) + " " + str(first["facts"])
    ).lower()
    has_scarf_first = "schal" in first_all_text
    has_pattern_first = ("muster" in first_all_text) or ("karo" in first_all_text) or ("streifen" in first_all_text)

    if not has_scarf_first or not has_pattern_first:
        missing = []
        if not has_scarf_first:
            missing.append("Schal")
        if not has_pattern_first:
            missing.append("Muster")
        print(f"\n❌ FAIL: Bild 1 enthält nicht alle Pflichtmerkmale: {missing}")
        return 1

    second_all_text = (
        str(second["rendered"]) + " " + str(second["report_text"]) + " " + str(second["facts"])
    ).lower()

    banned_tokens = ["schal"]
    leaked = [tok for tok in banned_tokens if tok in second_all_text]

    if leaked:
        print(f"\n❌ FAIL: State-Leak erkannt im zweiten Durchlauf: {leaked}")
        return 1

    print("\n✅ PASS: Bild 1 enthält Schal+Muster, Bild 2 enthält keinen Schal (Memory-Wipe ok).")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_sequence_test())
