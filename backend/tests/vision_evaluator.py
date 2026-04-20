#!/usr/bin/env python3
"""
Vision Regression Matrix Evaluator
Test-Tool zur Validierung der Vision-Logik gegen Ground-Truth Daten
"""

import logging
import os
import json
import sys
import argparse
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from colorama import init, Fore, Style

# Logger Definition
logger = logging.getLogger("janus_backend")

# Backend Imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

try:
    from backend.data.database import SessionLocal
    from backend.services.vision_service import vision_service
    print("!!! VISION-EVALUATOR: Importiere vision_service mit FootwearPlugin!")
    from backend.services.vision.utils import get_mapped_portrait_facts  # Single Source of Truth
except ImportError:
    # Fallback: direkte Imports
    sys.path.insert(0, os.path.dirname(__file__))
    from backend.data.database import SessionLocal
    from backend.services.vision_service import vision_service
    print("!!! VISION-EVALUATOR: Fallback Import von vision_service!")
    from backend.services.vision.utils import get_mapped_portrait_facts  # Single Source of Truth

# Initialize colorama for colored terminal output
init(autoreset=True)

@dataclass
class TestResult:
    """Einzelnes Testergebnis"""
    image_name: str
    category: str
    expected: Any
    found: Any
    status: str

class VisionEvaluator:
    """Vision Regression Matrix Evaluator"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def _normalize_expected_data(self, ground_truth: Dict[str, Any]) -> Dict[str, Any]:
        """Akzeptiert sowohl flache JSON-Struktur als auch {'expected': {...}}."""
        if isinstance(ground_truth, dict):
            nested_expected = ground_truth.get("expected")
            if isinstance(nested_expected, dict):
                return nested_expected
        return ground_truth if isinstance(ground_truth, dict) else {}
        
    def load_ground_truth(self, json_path: Path) -> Dict[str, Any]:
        """Lädt Ground-Truth Daten aus JSON-Datei"""
        try:
            # Windows-kompatibler Pfad
            json_path = Path(str(json_path).replace('/', os.sep))
            with open(json_path, 'r', encoding='utf-8-sig') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Fehler beim Laden {json_path}: {e}")
            return {}

    def _resolve_ground_truth_file(self, image_file: Path) -> Path:
        """Resolve ground-truth filename for a given image.

        Supports both:
        - same-name convention: <name>.jpg -> <name>.jpg.json
        - prefixed-name images with numeric GT: Supercluster-1.jpg -> 1.jpg.json
        """
        default_json = image_file.with_suffix('.jpg.json')
        if default_json.exists():
            return default_json

        stem = image_file.stem  # e.g. "Supercluster-1"
        match = re.search(r"(\d+)$", stem)
        if match:
            numeric_json = image_file.with_name(f"{match.group(1)}.jpg.json")
            if numeric_json.exists():
                return numeric_json

        return default_json
    
    def extract_mapped_facts(self, vision_result: Dict) -> Dict[str, Any]:
        """Extrahiere die gemappten Fakten aus dem Vision-Ergebnis (Single Source of Truth)"""
        # print(f"DEBUG VISION RESULT: {len(vision_result)} Keys gefunden") # Entfernt: Debug
        # print(f"DEBUG FEATURE REPORT: {len(vision_result.get('feature_report', {}))} Kategorien") # Entfernt: Debug
        
        # Aus feature_report die Mappings extrahieren
        feature_report = vision_result.get('feature_report', {})
        context = vision_result.get('context', {})
        
        # DEBUG: Zeige alle verfügbaren Kategorien
        # print(f"DEBUG VERFÜGBARE KATEGORIEN: {list(feature_report.keys())}") # Entfernt: Debug
        
        # Single Source of Truth - Zentrale Mapping-Funktion
        facts = get_mapped_portrait_facts(feature_report, context, vision_mode="eval")
        
        # print(f"DEBUG FINALE FACTS: {facts}") # Entfernt: Debug
        return facts
    
    def compare_values(self, expected: Any, found: Any, category: str) -> Tuple[str, str]:
        """Vergleiche erwartete vs gefundene Werte"""
        if expected is None and found is None:
            return "PASS", "Beide None"
        elif expected is None:
            return "FAIL", f"Expected None, Found: {found}"
        elif found is None:
            return "FAIL", f"Expected: {expected}, Found None"
        elif str(expected).rstrip('.').lower() == str(found).rstrip('.').lower():
            return "PASS", "Values match"
        else:
            return "FAIL", f"Expected: {expected}, Found: {found}"
    
    def test_image(self, image_path: Path, ground_truth: Dict) -> List[TestResult]:
        """Testet ein einzelnes Bild"""
        results = []
        
        try:
            # Datenbank-Verbindung für Vision Service
            db = SessionLocal()
            # Lese Bild als Bytes
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            # Füge Geschlecht aus Ground Truth zum Kontext hinzu
            expected_data = self._normalize_expected_data(ground_truth)
            gender = None
            if 'GESCHLECHT' in expected_data:
                gender = expected_data['GESCHLECHT'].lower()
                if gender == 'mann':
                    gender = 'male'
                elif gender == 'frau':
                    gender = 'female'
            
            # Vision Service aufrufen
            vision_result = vision_service.process_image(
                image_bytes, 
                db, 
                image_name=image_path.name
            )
            
            # Füge den Kontext zum Ergebnis hinzu, falls noch nicht vorhanden
            if 'context' not in vision_result:
                vision_result['context'] = {}
            
            # Aktualisiere den Kontext mit den Werten aus dem Ground Truth
            vision_result['context'].update({
                'image_name': image_path.name,
                'gender': gender,
                'settings': vision_service.settings,
                'ground_truth': ground_truth  # Füge die Ground-Truth-Daten dem Kontext hinzu
            })
            db.close()
            
            # Fakten extrahieren
            facts = self.extract_mapped_facts(vision_result)
            
            # NUR die Kategorien testen, die explizit in der expected-Sektion stehen
            expected_data = self._normalize_expected_data(ground_truth)
            
            for category, expected_value in expected_data.items():
                found = facts.get(category)
                
                status, message = self.compare_values(expected_value, found, category)
                results.append(TestResult(
                    image_name=image_path.name,
                    category=category,
                    expected=expected_value,
                    found=found,
                    status=status
                ))
                
        except Exception as e:
            self.logger.error(f"Fehler bei Verarbeitung {image_path}: {e}")
            # Fehler als FAIL für alle Kategorien
            expected_data = self._normalize_expected_data(ground_truth)
            for category in expected_data.keys():
                results.append(TestResult(
                    image_name=image_path.name,
                    category=category,
                    expected=expected_data.get(category),
                    found="ERROR",
                    status="FAIL"
                ))
        
        return results
    
    def test_cluster(self, cluster_path: Path) -> List[TestResult]:
        """Testet einen kompletten Cluster"""
        all_results = []
        
        # Finde alle Bilder im Cluster
        image_files = list(cluster_path.glob("*.jpg"))
        print(f"\nFound {len(image_files)} image files in cluster {cluster_path}:")
        for img in sorted(image_files):
            print(f"  - {img.name}")
        
        for image_file in sorted(image_files):
            print(f"\n{'='*80}")
            print(f"Processing image: {image_file}")
            
            # Lade Ground Truth
            json_file = self._resolve_ground_truth_file(image_file)
            print(f"Looking for ground truth file: {json_file}")
            
            if not json_file.exists():
                print(f"WARNING: Ground truth file not found: {json_file}")
                continue
                
            ground_truth_data = self.load_ground_truth(json_file)
            print(f"Ground truth data loaded: {bool(ground_truth_data)}")
            
            if ground_truth_data:
                print("Ground truth content:")
                for k, v in ground_truth_data.items():
                    print(f"  {k}: {v}")
                
                ground_truth = ground_truth_data
                # Teste Bild
                results = self.test_image(image_file, ground_truth)
                all_results.extend(results)
                print(f"Test results for {image_file.name}: {len(results)} categories tested")
            else:
                print(f"WARNING: No ground truth data loaded for {image_file}")
        
        return all_results
    
    def print_results(self, results: List[TestResult], cluster_name: str):
        """Gibt Ergebnisse formatiert aus"""
        if not results:
            print(f"Keine Ergebnisse für {cluster_name}")
            return
        
        # Header
        print(f"\n{'='*100}")
        print(f"Cluster {cluster_name}")
        print(f"{'='*100}")
        print(f"{'Bildname':<20} {'Kategorie':<15} {'Erwartet':<20} {'Gefunden':<25} {'Status'}")
        print(f"{'-'*100}")
        
        # Ergebnisse
        for result in results:
            expected_str = str(result.expected) if result.expected is not None else "None"
            found_str = str(result.found) if result.found is not None else "None"
            
            # Kürzen für Anzeige
            if len(expected_str) > 18:
                expected_str = expected_str[:15] + "..."
            if len(found_str) > 23:
                found_str = found_str[:20] + "..."
            
            status_color = Fore.GREEN if result.status == "PASS" else Fore.RED
            
            print(f"{result.image_name:<20} {result.category:<15} {expected_str:<20} {found_str:<25} {status_color}{result.status}{Style.RESET_ALL}")
        
        # Summary
        total = len(results)
        passed = sum(1 for r in results if r.status == "PASS")
        failed = total - passed
        percentage = (passed / total * 100) if total > 0 else 0
        
        print(f"{'-'*100}")
        print(f"Cluster {cluster_name}: {passed}/{total} Treffer ({percentage:.1f}%)")
        if failed > 0:
            print(f"{failed} Tests fehlgeschlagen - Optimierung erforderlich")
        print(f"{'='*100}")

def main():
    """Main Funktion"""
    # Windows-Konsole: Emoji-/Unicode-sichere Ausgabe verhindern Logging-Tracebacks (cp1252)
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is not None and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass

    # Configure logging to show all debug messages
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Ensure the root logger is set to DEBUG
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Create a file handler for debug output
    file_handler = logging.FileHandler('vision_evaluator_debug.log', mode='w', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    print("\n=== STARTING VISION EVALUATOR WITH DEBUG LOGGING ===\n")
    
    parser = argparse.ArgumentParser(description="Vision Regression Matrix Evaluator")
    parser.add_argument("--cluster", type=str, default=None, help="Optional: specific cluster to run, e.g. cluster_13")
    args = parser.parse_args()

    evaluator = VisionEvaluator()

    # Cluster-Konfiguration - Alle Cluster für Holistic Regression
    clusters = [
        "cluster_1", "cluster_2", "cluster_3", "cluster_4", "cluster_5", "cluster_6",
        "cluster_7", "cluster_8", "cluster_9", "cluster_10", "cluster_11", "cluster_12", "cluster_13", "cluster_14",
    ]
    if args.cluster:
        clusters = [args.cluster]
    base_path = Path(__file__).parent / "vision_matrix"
    
    all_results = []
    
    # Teste alle Cluster
    for cluster_name in clusters:
        cluster_path = base_path / cluster_name
        if cluster_path.exists():
            print(f"Teste Cluster {cluster_name}...")
            results = evaluator.test_cluster(cluster_path)
            evaluator.print_results(results, cluster_name)
            all_results.extend(results)
    
    # Gesamt-Summary
    if all_results:
        total = len(all_results)
        passed = sum(1 for r in all_results if r.status == "PASS")
        failed = total - passed
        percentage = (passed / total * 100) if total > 0 else 0
        
        print(f"\n{'='*120}")
        print(f"GESAMT-REPORT VISION CLUSTER")
        print(f"{'='*120}")
        print(f"GESAMT-SCORE: {passed}/{total} Treffer ({percentage:.1f}%)")
        if failed > 0:
            print(f"{failed} Tests fehlgeschlagen - Optimierung erforderlich")
        else:
            print("ALLE TESTS ERFOLGREICH - QUAD-CLUSTER-STABILITAET ERREICHT!")
        print(f"{'='*120}")

if __name__ == "__main__":
    main()
