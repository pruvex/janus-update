import os
import sys
import subprocess

def check_python_dependencies():
    print("Überprüfe Python-Abhängigkeiten mit 'pip check'...")
    errors = []
    backend_venv_python = os.path.join("backend", "venv", "Scripts", "python.exe") if sys.platform == "win32" else os.path.join("backend", "venv", "bin", "python")
    
    if not os.path.exists(backend_venv_python):
        errors.append(f"FEHLER: Python-Interpreter der virtuellen Umgebung nicht gefunden: {backend_venv_python}")
        return errors

    try:
        result = subprocess.run([backend_venv_python, "-m", "pip", "check"], capture_output=True, text=True, check=True)
        if result.stdout and "No broken requirements found." not in result.stdout:
            errors.append(f"WARNUNG: 'pip check' meldete Probleme:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        errors.append(f"FEHLER: 'pip check' fehlgeschlagen:\n{e.stderr}")
    except FileNotFoundError:
        errors.append("FEHLER: 'pip' Befehl nicht gefunden. Ist die virtuelle Umgebung aktiviert oder korrekt eingerichtet?")
    return errors

def check_node_dependencies():
    print("Überprüfe Node.js-Abhängigkeiten mit 'npm audit'...")
    errors = []
    frontend_dir = "frontend"

    if not os.path.isdir(frontend_dir):
        errors.append(f"FEHLER: Frontend-Verzeichnis '{frontend_dir}' nicht gefunden.")
        return errors

    try:
        # npm audit kann auch bei Warnungen einen Fehlercode zurückgeben, daher check=False
        result = subprocess.run(["npm", "audit"], cwd=frontend_dir, capture_output=True, text=True, check=False, shell=True)
        if result.returncode != 0 and "found 0 vulnerabilities" not in result.stdout:
            errors.append(f"WARNUNG: 'npm audit' meldete Probleme:\n{result.stdout}\n{result.stderr}")
    except FileNotFoundError:
        errors.append("FEHLER: 'npm' Befehl nicht gefunden. Ist Node.js installiert und im PATH?")
    return errors

def find_misplaced_config_files():
    misplaced_files = []
    for root, dirs, files in os.walk("."):
        if "config.json" in files and os.path.join(root, "config.json") != os.path.join("backend", "config.json"):
            misplaced_files.append(os.path.join(root, "config.json"))
    return misplaced_files

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

    # 4. Überprüfung der requirements.in und requirements.txt im Backend-Verzeichnis
    backend_requirements_in_path = os.path.join("backend", "requirements.in")
    if not os.path.isfile(backend_requirements_in_path):
        errors.append(f"FEHLT: requirements.in im Backend unter '{backend_requirements_in_path}' nicht gefunden.")

    backend_requirements_txt_path = os.path.join("backend", "requirements.txt")
    if not os.path.isfile(backend_requirements_txt_path):
        errors.append(f"FEHLT: requirements.txt im Backend unter '{backend_requirements_txt_path}' nicht gefunden.")

    # 5. Überprüfung der Frontend-Paketdateien
    frontend_package_json_path = os.path.join("frontend", "package.json")
    if not os.path.isfile(frontend_package_json_path):
        errors.append(f"FEHLT: package.json im Frontend unter '{frontend_package_json_path}' nicht gefunden.")

    frontend_package_lock_json_path = os.path.join("frontend", "package-lock.json")
    if not os.path.isfile(frontend_package_lock_json_path):
        errors.append(f"FEHLT: package-lock.json im Frontend unter '{frontend_package_lock_json_path}' nicht gefunden.")

    # Führe Abhängigkeitsprüfungen aus
    errors.extend(check_python_dependencies())
    errors.extend(check_node_dependencies())

    # 6. Überprüfung auf falsch platzierte config.json Dateien
    misplaced_configs = find_misplaced_config_files()
    for f in misplaced_configs:
        errors.append(f"WARNUNG: Falsch platzierte config.json gefunden: '{f}'. Sie sollte sich nur unter 'backend/config.json' befinden.")

    if not errors:
        print("VALIDATION PASSED: Die Projektstruktur und Abhängigkeiten sind in Ordnung.")
        sys.exit(0)
    else:
        print("VALIDATION FAILED: Die folgenden Probleme wurden gefunden:")
        for error in errors:
            print(f"- {error}")
        sys.exit(1)