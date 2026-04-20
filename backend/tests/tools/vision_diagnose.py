import sys
from pathlib import Path

# Pfad-Setup (Datei liegt jetzt in backend/tests/tools)
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.services.vision_service import vision_service
from backend.data.database import SessionLocal
from backend.services.vision.utils import PORTRAIT_FACT_TEMPLATE_KEYS


def fast_check(image_path: Path):
    print(f"--- FAST CHECK: {image_path} ---")
    db = SessionLocal()
    with open(image_path, "rb") as f:
        img_bytes = f.read()

    # Analyse
    res = vision_service.process_image(img_bytes, db)

    # Mapping
    from backend.services.vision.utils import get_mapped_portrait_facts

    facts = get_mapped_portrait_facts(res["feature_report"], res["context"], vision_mode="eval")

    print("\nRAW FEATURE REPORT (label / score / status):")
    for category, items in (res.get("feature_report", {}) or {}).items():
        if not isinstance(items, list):
            continue
        print(f"\n[{category}]")
        for item in items:
            label = item.get("label", "")
            score = item.get("score", 0.0)
            status = item.get("status", "")
            print(f"  - label={label!r}, score={score:.4f}, status={status}")

    # Kritische Prüfung (alle 20 Template-Keys inkl. leerer Werte)
    print("\nERGEBNIS (Portrait-Facts, alle 20 Template-Keys):")
    for key in PORTRAIT_FACT_TEMPLATE_KEYS:
        value = facts.get(key, "")
        print(f"  {key}: {value}")

    # Halluzinations-Check
    hallucinations = ["beanie", "mütze", "holzohrringe", "handschuhe"]
    found = [h for h in hallucinations if h in str(facts).lower()]
    if found:
        print(f"\n❌ WARNUNG: Halluzinationen gefunden: {found}")
    else:
        print("\n✅ Sauber: Keine bekannten Halluzinationen im Mapping.")
    db.close()


if __name__ == "__main__":
    fast_check(Path("backend/tests/vision_matrix/Supercluster/Supercluster-61.jpg"))
