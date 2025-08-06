# Python-Code für den "Deep Validation" Health Check
import os
import sys

def validate_deep():
    print("Starte 'Deep Validation' der Projektstruktur...")
    errors = []
        # 1. Erwartete Verzeichnisse auf oberster Ebene
    expected_top_level = ["backend", "janus", "waechter"]
    for d in expected_top_level:
        if not os.path.isdir(d):
            errors.append(f"FEHLT: Top-Level-Ordner '{d}' nicht gefunden.")
        # 2. Erwartete Unterverzeichnisse (NEU)
    expected_sub_dirs = ["backend/agents", "janus/src", "waechter/tests"]
    for sd in expected_sub_dirs:
        if not os.path.isdir(sd.replace('/', os.sep)):
            errors.append(f"FEHLT: Unterordner '{sd}' nicht gefunden.")
    if not errors:
        print("VALIDATION PASSED: Die Projektstruktur entspricht dem Goldstandard.")
        sys.exit(0)
    else:
        print("VALIDATION FAILED: Die folgenden Strukturprobleme wurden gefunden:")
        for error in errors:
            print(f"- {error}")
        sys.exit(1)

if __name__ == "__main__":
    validate_deep()