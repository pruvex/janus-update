import os
import sys

def validate_deep():
    print("Starte 'Deep Validation' der Projektstruktur...")
    errors = []

    # 1. Erwartete Verzeichnisse auf oberster Ebene
    expected_top_level = ["backend", "frontend", "waechter"]
    for d in expected_top_level:
        if not os.path.isdir(d):
            errors.append(f"FEHLT: Top-Level-Ordner '{d}' nicht gefunden.")

    # 2. Erwartete Unterverzeichnisse (NEU)
    expected_sub_dirs = ["backend/agents", "frontend/src", "waechter/tests"]
    for sd in expected_sub_dirs:
        if not os.path.isdir(os.path.join(*sd.split('/'))):
            errors.append(f"FEHLT: Unterordner '{sd}' nicht gefunden.")

    # 3. Überprüfung der venv im Backend-Verzeichnis
    backend_venv_path = os.path.join("backend", "venv")
    if not os.path.isdir(backend_venv_path):
        errors.append(f"FEHLT: Virtuelle Umgebung im Backend unter '{backend_venv_path}' nicht gefunden.")

    # 4. Überprüfung der requirements.txt im Backend-Verzeichnis
    backend_requirements_path = os.path.join("backend", "requirements.txt")
    if not os.path.isfile(backend_requirements_path):
        errors.append(f"FEHLT: requirements.txt im Backend unter '{backend_requirements_path}' nicht gefunden.")

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