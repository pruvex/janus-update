# Python-Code für den "Health Check"
import os
import sys
import subprocess
import json

def check_structure():
    errors = []
    expected_top_level = ["backend", "janus", "waechter"]
    for d in expected_top_level:
        if not os.path.isdir(d):
            errors.append(f"STRUKTUR-FEHLER: Top-Level-Ordner '{d}' fehlt.")
    
    expected_sub_dirs = ["janus/src-tauri"]
    for sd in expected_sub_dirs:
        if not os.path.isdir(sd.replace('/', os.sep)):
            errors.append(f"STRUKTUR-FEHLER: Wichtiger Unterordner '{sd}' fehlt.")
    return errors

def check_frontend_deps():
    errors = []
    package_json_path = os.path.join('janus', 'package.json')
    node_modules_path = os.path.join('janus', 'node_modules')
    if not os.path.exists(package_json_path):
        errors.append("FRONTEND-FEHLER: 'janus/package.json' nicht gefunden. Führen Sie 'npm init' aus.")
        return errors # Weitere Prüfungen sind sinnlos
        
    if not os.path.isdir(node_modules_path):
        errors.append("FRONTEND-FEHLER: 'janus/node_modules' nicht gefunden. Führen Sie 'npm install' aus.")
    return errors
    
def check_backend_deps():
    errors = []
    venv_path = os.path.join('backend', 'venv')
    if not os.path.isdir(venv_path):
        errors.append("BACKEND-FEHLER: 'backend/venv' nicht gefunden. Führen Sie 'python -m venv' aus.")
    return errors

def run_health_check():
    print("Starte umfassenden Projekt-Gesundheits-Check...")
    all_errors = []
        
    all_errors.extend(check_structure())
    all_errors.extend(check_frontend_deps())
    all_errors.extend(check_backend_deps())

    if not all_errors:
        print("HEALTH CHECK PASSED: Projektstruktur und Abhängigkeiten sind intakt.")
        sys.exit(0)
    else:
        print("HEALTH CHECK FAILED: Die folgenden Probleme wurden gefunden:")
        for error in all_errors:
            print(f"- {error}")
        sys.exit(1)

if __name__ == "__main__":
    run_health_check()