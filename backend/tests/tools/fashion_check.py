import sys
import logging
from pathlib import Path
from typing import Any, Dict

# Pfad-Setup (Datei liegt in backend/tests/tools)
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.data.database import SessionLocal
from backend.services.vision.utils import fuse_vision_results, get_mapped_portrait_facts
from backend.services.vision_service import vision_service


logging.getLogger("janus_backend").setLevel(logging.WARNING)
logging.getLogger("backend.services.vision.utils").setLevel(logging.WARNING)


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
        return {"result": result, "facts": facts}
    finally:
        db.close()


def _contains_any(text: str, tokens: list[str]) -> bool:
    lower = text.lower()
    return any(token.lower() in lower for token in tokens)


def mock_analyze_image_with_cloud(image_path: Path) -> Dict[str, Any]:
    objects = []
    if "Clustrer14-9" in image_path.name:
        objects = [
            {"name": "Blazer", "color": "schwarz", "material": "Stoff", "details": "einreihig"},
            {"name": "Hemd", "color": "beige", "material": "Baumwolle", "details": "geknöpft"},
            {"name": "Jeans", "color": "dunkelblau", "material": "Denim", "details": "Skinny Fit"},
            {"name": "Gürtel", "color": "braun", "material": "Leder", "details": "große, silberne Schnalle"},
            {
                "name": "Schuhe",
                "color": "weiß",
                "material": "Leder",
                "details": "Nike Sneaker mit gelben Akzenten",
            },
            {"name": "Schmuck", "color": "gold", "material": "Metall", "details": "mehrere Armbänder und eine Kette"},
        ]
    return {"objects": objects}


def run_fashion_check() -> int:
    rollkragen_image = Path("backend/tests/vision_matrix/cluster_3/Cluster3-2.jpg")
    mantel_image = Path("backend/tests/vision_matrix/cluster_14/Clustrer14-9.jpg")

    if not rollkragen_image.exists() or not mantel_image.exists():
        print("ERROR: Referenzbilder fehlen:")
        print(f"  - {rollkragen_image}")
        print(f"  - {mantel_image}")
        return 2

    print("=== FASHION IQ CHECK (targeted, 2 images only) ===")

    print(f"\n[1/2] Rollkragen-Referenz: {rollkragen_image}")
    roll_data = _analyze_image(rollkragen_image)
    roll_facts = roll_data["facts"]

    roll_outfit_oben = str(roll_facts.get("OUTFIT_OBEN", ""))
    roll_clothing = str(roll_facts.get("KLEIDUNG", ""))
    roll_full = f"{roll_outfit_oben} {roll_clothing}".lower()

    has_rollkragen = _contains_any(roll_full, ["rollkragenpullover"])
    has_schal = _contains_any(roll_full, ["schal", "scarf"])

    print(f"  KLEIDUNG: {roll_clothing}")
    print(f"  OUTFIT_OBEN: {roll_outfit_oben}")

    print(f"\n[2/2] Mantel-Referenz: {mantel_image}")
    coat_data = _analyze_image(mantel_image)
    coat_facts = coat_data["facts"]
    coat_feature_report = coat_data["result"].get("feature_report", {})
    coat_context = coat_data["result"].get("context", {})
    print("  DEBUG HAAR_STRUKTUR:", coat_feature_report.get("HAAR_STRUKTUR"))
    print("  DEBUG FRISUR:", coat_feature_report.get("FRISUR"))
    print("  DEBUG SCHUH_SATZ:", coat_feature_report.get("SCHUH_SATZ"))
    print("  DEBUG CONTEXT HAIR_TYPE:", coat_context.get("hair_type"))
    print("  DEBUG FULL FEATURE REPORT:")
    for category, items in coat_feature_report.items():
        print(f"    {category}:", items)

    hair_details = str(coat_facts.get("HAAR_DETAILS", ""))
    outfit_unten = str(coat_facts.get("OUTFIT_UNTEN", ""))
    schuh_satz = str(coat_facts.get("SCHUH_SATZ", ""))

    has_long_hair = _contains_any(hair_details, ["langes"])
    has_boots = _contains_any(f"{outfit_unten} {schuh_satz}", ["stiefelett", "stiefel"])

    print(f"  HAAR_DETAILS: {hair_details}")
    print(f"  OUTFIT_UNTEN: {outfit_unten}")
    print(f"  SCHUH_SATZ: {schuh_satz}")

    failures = []

    if not has_rollkragen:
        failures.append("Rollkragen-Bild enthält keinen Rollkragenpullover")
    if has_schal:
        failures.append("Rollkragen-Bild enthält unerlaubt Schal/Scarf")
    if not has_long_hair:
        failures.append("Mantel-Bild enthält kein 'langes ... Haar'")

    mock_cloud_result = mock_analyze_image_with_cloud(mantel_image)
    fused_facts = fuse_vision_results(coat_data["result"], mock_cloud_result, vision_mode="eval")

    print("\n--- Hybrid-Fusion: Fakten ---")
    for key in sorted(fused_facts.keys()):
        print(f"  {key}: {fused_facts[key]}")

    fused_text = " ".join(str(fused_facts.get(key, "")).lower() for key in [
        "LEGWEAR_SATZ",
        "OUTFIT_UNTEN",
        "GUERTEL_SATZ",
        "SCHUH_SATZ",
    ])

    detail_failures = []
    if "dunkelblaue jeans" not in fused_text:
        detail_failures.append("Fusionierte Fakten enthalten keine 'dunkelblaue Jeans'.")
    if not any(token in fused_text for token in ["brauner gürtel", "braune ledergürtel", "braunen gürtel"]):
        detail_failures.append("Fusionierte Fakten enthalten keinen 'brauner Ledergürtel'.")
    if "nike sneaker" not in fused_text:
        detail_failures.append("Fusionierte Fakten enthalten keine 'Nike Sneaker'.")

    failures.extend(detail_failures)

    if failures:
        print("\nFAIL:")
        for item in failures:
            print(f"  - {item}")
        return 1

    print("\nPASS: Fashion IQ targeted checks sind erfuellt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_fashion_check())
