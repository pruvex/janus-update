import logging
import threading
import time
import numpy as np
import io
import cv2
import torch
import clip
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session
from backend.data import crud_vision
from backend.data.database import SessionLocal
from backend.services import memory_manager
import sys
import os
from pathlib import Path

# PyInstaller: Setze Pfad für CLIP Datei
if getattr(sys, 'frozen', False):
    # In production: Datei aus clip-Verzeichnis
    clip_dir = Path(sys._MEIPASS) / 'clip'
    if clip_dir.exists():
        # Füge clip-Verzeichnis zum Pfad hinzu, falls Datei dort ist
        if not (clip_dir / 'bpe_simple_vocab_16e6.txt.gz').exists():
            # Datei nicht im clip-Verzeichnis, versuche assets-Verzeichnis
            assets_dir = Path(sys._MEIPASS) / 'backend' / 'assets'
            if assets_dir.exists() and (assets_dir / 'bpe_simple_vocab_16e6.txt.gz').exists():
                # Kopiere Datei in clip-Verzeichnis
                import shutil
                shutil.copy(assets_dir / 'bpe_simple_vocab_16e6.txt.gz', clip_dir / 'bpe_simple_vocab_16e6.txt.gz')

# Importiere die Plugins
from backend.services.vision.plugins.age_gender_plugin import AgeGenderPlugin
from backend.services.vision.plugins.beard_plugin import BeardPlugin
from backend.services.vision.plugins.hair_plugin import HairPlugin
from backend.services.vision.plugins.glasses_plugin import GlassesPlugin
from backend.services.vision.plugins.jewelry_plugin import JewelryPlugin
from backend.services.vision.plugins.clothing_plugin import ClothingPlugin
from backend.services.vision.plugins.outerwear_plugin import OuterwearPlugin
from backend.services.vision.plugins.legwear_plugin import LegwearPlugin
from backend.services.vision.plugins.material_plugin import MaterialPlugin
from backend.services.vision.plugins.bag_plugin import BagPlugin
from backend.services.vision.plugins.skin_eye_plugin import SkinEyePlugin
from backend.services.vision.plugins.accessory_meta_plugin import AccessoryMetaPlugin  # NEU: Anomalie-Plugin
from backend.services.vision.plugins.earrings_plugin import EarringsPlugin  # NEU: Plugin-Split
from backend.services.vision.plugins.necklace_plugin import NecklacePlugin  # NEU: Plugin-Split
from backend.services.vision.plugins.headwear_plugin import HeadwearPlugin  # NEU: Cluster 5 Headwear & Audio
from backend.services.vision.plugins.footwear_plugin import FootwearPlugin # NEU: Cluster 12 Footwear
from backend.services.vision.plugins.pose_interaction_plugin import PoseInteractionPlugin # NEU: Cluster 13 Pose & Interaction
from backend.services.vision.plugins.environment_plugin import EnvironmentPlugin # NEU: Cluster 14 Environment & Lighting
from backend.services.vision.vision_settings import VisionSettings # Importiere VisionSettings

logger = logging.getLogger("janus_backend")

class LocalVisionService:
    def __init__(self):
        self.TOLERANCE = 0.65
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.preprocess = None
        try:
            self.model, self.preprocess = clip.load("ViT-B/32", device=self.device)
            logger.info(f"VISION: CLIP-Modell auf {self.device} geladen.")
        except Exception as exc:
            self.model = None
            self.preprocess = None
            logger.warning(
                "⚠️ VISION-SERVICE: CLIP-Modell konnte nicht geladen werden (Bildsuche deaktiviert)"
            )
            logger.debug("VISION: CLIP-Load error details: %s", exc, exc_info=True)
        
        self.settings = VisionSettings() # Instanziiere VisionSettings hier
        
        # Plugin-Register (Reihenfolge wichtig für Kontext!)
        self.plugin_classes = [
            AgeGenderPlugin,
            BeardPlugin,
            HairPlugin,     # Setzt is_curly
            ClothingPlugin, # NEU: Setzt has_scarf für JewelryPlugin
            OuterwearPlugin,
            LegwearPlugin,
            FootwearPlugin, # NEU: Cluster 12 - Schuhe
            PoseInteractionPlugin, # NEU: Cluster 13 - Pose & Interaktion
            EnvironmentPlugin, # NEU: Cluster 14 - Environment & Lighting
            MaterialPlugin,
            BagPlugin,
            GlassesPlugin,  # Nutzt is_curly
            HeadwearPlugin, # NEU: Cluster 5 - Kopfbedeckungen & Audio-Hardware
            EarringsPlugin,  # NEU: Plugin-Split - Ohrringe
            NecklacePlugin,   # NEU: Plugin-Split - Halsschmuck
            JewelryPlugin,  # Nutzt has_scarf (Armbänder, Ringe, Broschen)
            AccessoryMetaPlugin,  # NEU: Anomalie-Erkennung
            SkinEyePlugin
        ]

        # Explizite Laufzeit-Container (werden pro Request hart geleert)
        self.fused_results = {}
        self.current_tags = []
        self.feature_report = {}

    def _reset_request_state(self):
        """Harte State-Sanitization vor/nach jeder Bildanalyse."""
        self.fused_results = {}
        self.current_tags = []
        self.feature_report = {}

    def _build_plugins_for_request(self):
        """Erzeugt frische Plugin-Instanzen pro Bildanalyse (State-Pollution-Schutz)."""
        return [plugin_class() for plugin_class in self.plugin_classes]

    def _reset_plugin_state(self, plugin):
        """Setzt mutable Plugin-Felder explizit zurück, falls ein Plugin internen Zustand hält."""
        resettable_fields = {
            "detected_items",
            "cache",
            "state",
            "last_results",
            "previous_results",
            "history",
            "buffer",
        }
        for attr_name in dir(plugin):
            if attr_name.startswith("_"):
                continue
            try:
                value = getattr(plugin, attr_name)
            except Exception:
                continue

            if callable(value):
                continue

            if attr_name not in resettable_fields:
                continue

            try:
                if isinstance(value, dict):
                    setattr(plugin, attr_name, {})
                elif isinstance(value, list):
                    setattr(plugin, attr_name, [])
                elif isinstance(value, set):
                    setattr(plugin, attr_name, set())
            except Exception:
                # Read-only properties (z.B. clip_labels @property) sicher ignorieren
                continue

    def process_image(self, image_bytes: bytes, db: Session = None, profile=None, image_name: str = None) -> dict:
        logger.info(">>> LocalVisionService startet die Analyse der Bild-Bytes...")
        self._reset_request_state()
        managed_db = db
        owns_db_session = False
        if managed_db is None:
            managed_db = SessionLocal()
            owns_db_session = True

        # Harte Stateless-Grenze: frische Plugins + lokale Container pro Request
        plugins = self._build_plugins_for_request()
        current_context = {}
        current_feature_report = {}
        result = {
            "found_faces": False,
            "identified_names": [],
            "unknown_encodings": [],
            "feature_report": current_feature_report,
            "context": current_context,
        }
        
        try:
            zone_a_categories = {"ALTER", "GESCHLECHT", "POSE", "AMBIENTE", "KLEIDUNG", "OUTERWEAR", "LEGWEAR", "SCHUH_SATZ"}
            zone_b_categories = {"HAARFARBE", "TEINT", "HAAR_STRUKTUR", "FRISUR", "AUGEN"}
            accessory_categories = {
                "KOPF_BEDECKUNG",
                "KOPF_ACCESSOIRE",
                "OHRRINGE",
                "HALSKMUCK",
                "SCHMUCK",
                "HANDBEKLEIDUNG",
                "HANDSCHUH",
                "BRILLE",
                "AUDIO_HARDWARE",
            }
            detail_categories = {"MATERIAL", "PRINT", "GUERTEL", "SCHNALLE", "TASCHE"}
            high_risk_accessory_categories = {"KOPF_ACCESSOIRE", "SCHMUCK", "HALSKMUCK", "OHRRINGE"}
            core_identity_categories = {"GESCHLECHT", "ALTER"}

            def _category_threshold(category_name: str) -> float:
                category_upper = str(category_name or "").upper()
                if category_upper in high_risk_accessory_categories:
                    return 0.60
                if category_upper in core_identity_categories:
                    return 0.04
                if category_upper in zone_a_categories:
                    return 0.05
                if category_upper in {"HAAR_STRUKTUR", "FRISUR"}:
                    return 0.02
                if category_upper in zone_b_categories:
                    return 0.05
                if category_upper in {"GUERTEL", "SCHMUCK"}:
                    return 0.45
                if category_upper in {"TASCHE", "BAG"}:
                    return 0.45
                if category_upper in detail_categories:
                    return 0.05
                if category_upper in accessory_categories:
                    return 0.45
                return 0.25

            # 1. Face Recognition (bleibt gleich)
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is not None:
                rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                face_locations = face_recognition.face_locations(rgb_img, model="hog")
                if face_locations:
                    result["found_faces"] = True
                    encodings = face_recognition.face_encodings(rgb_img, face_locations, num_jitters=10, model="large")
                    known_encodings, known_names = crud_vision.get_all_known_faces(managed_db)

                    for encoding in encodings:
                        if not known_encodings:
                            result["unknown_encodings"].append(encoding)
                            continue
                        
                        distances = face_recognition.face_distance(known_encodings, encoding)
                        best_match_idx = np.argmin(distances)
                        
                        if distances[best_match_idx] <= self.TOLERANCE:
                            name = known_names[best_match_idx]
                            result["identified_names"].append(name)
                            crud_vision.update_last_seen(managed_db, name)
                        else:
                            result["unknown_encodings"].append(encoding)
                    
            # 2. CLIP Inference (Zentralisiert)
            if self.model is None or self.preprocess is None:
                logger.info("VISION: CLIP nicht verfügbar - ueberspringe Bildsuche.")
                return result
            try:
                pil_img = Image.open(io.BytesIO(image_bytes))
            except UnidentifiedImageError as img_err:
                logger.warning("VISION: Bild konnte nicht geöffnet werden: %s", img_err)
                return None
            image_input = self.preprocess(pil_img).unsqueeze(0).to(self.device)
            
            # Sammle Labels aller Plugins
            all_labels = []
            for p in plugins:
                all_labels.extend(p.clip_labels)
            all_labels = list(set(all_labels)) # Deduplizieren
            
            text_tokens = clip.tokenize(all_labels).to(self.device)
            with torch.no_grad():
                logits, _ = self.model(image_input, text_tokens)
                # KEIN Sigmoid hier, wir nehmen die Roh-Logits!
                raw_logits = logits[0].cpu().numpy()
            
            # 3. Plugin-Execution Loop mit lokaler Normalisierung
            current_context = {
                "settings": self.settings,
                "image_name": image_name if image_name else "",
                # Harte Defaults gegen State Pollution
                "is_dark_hair": False,
                "has_scarf": False,
                "has_beard": False,
                "is_curly": False,
                "hair_color": "",
                "hair_type": "",
                "has_pattern": False,
                "has_complex_pattern": False,
                "age_items": [],
            }
            
            # Füge Geschlecht aus dem Profil hinzu, falls vorhanden
            if profile and hasattr(profile, 'gender'):
                current_context['gender'] = profile.gender
            current_feature_report = {}
            logger.info(f"Plugin-Loop startet mit {len(plugins)} Plugins...")
            logger.info(f">>> ANALYSE BILD: Starte Plugins (Gesicht gefunden: {result['found_faces']})")  # NEU: Forensisches Logging
            
            for plugin in plugins:
                logger.info(f"Plugin ausfuehren: {plugin.name}")
                self._reset_plugin_state(plugin)
                
                # 2. Im Plugin-Loop: Lokales Softmax
                # Suche Indizes der Labels dieses Plugins
                indices = [all_labels.index(l) for l in plugin.clip_labels if l in all_labels]
                
                # Extrahiere Logits und wende Softmax NUR auf diese Gruppe an
                group_logits = torch.tensor([raw_logits[i] for i in indices])
                group_probs = torch.softmax(group_logits, dim=-1).numpy()
                
                plugin_scores = {l: float(group_probs[i]) for i, l in enumerate(plugin.clip_labels)}
                
                # Plugin ausführen (mit fehlerfreiem Try-Except)
                try:
                    plugin_results = plugin.evaluate(plugin_scores, current_context)
                except Exception as e:
                    logger.error(f"Crash in Plugin {plugin.name}: {e}")
                    plugin_results = []
                
                # Ergebnisse sammeln
                for feature_result in plugin_results:
                    category_name = str(getattr(feature_result, "category", "") or "").upper()
                    safe_label = feature_result.label if feature_result.label is not None else ""
                    safe_label_l = str(safe_label).lower()
                    try:
                        score_value = float(feature_result.score)
                    except Exception:
                        score_value = 0.0

                    plugin_status = str(getattr(feature_result, "status", "") or "").upper()
                    if plugin_status == "REJECTED":
                        continue

                    threshold_value = _category_threshold(category_name)
                    pattern_keywords = ("checkered", "plaid", "tartan", "grid", "pattern")
                    if category_name in {"PRINT", "MATERIAL"} and any(k in safe_label_l for k in pattern_keywords):
                        threshold_value = min(threshold_value, 0.015)

                    # Kategorie-spezifischer Noise-Filter
                    if score_value < threshold_value:
                        continue

                    # Zwingender Accessoire-Override: unter 0.45 nie SICHER
                    if category_name in accessory_categories and score_value < 0.45:
                        plugin_status = "WAHRSCHEINLICH"

                    if feature_result.category not in current_feature_report:
                        current_feature_report[feature_result.category] = []

                    # Status-Hardening: Plugin-Status respektieren, aber mit globalen Schranken
                    status_value = "SICHER" if plugin_status == "SICHER" and score_value >= 0.45 else "WAHRSCHEINLICH"
                    if category_name in accessory_categories and score_value < 0.45:
                        status_value = "WAHRSCHEINLICH"

                    current_feature_report[feature_result.category].append({
                        'label': safe_label,
                        'score': score_value,
                        'status': status_value
                    })
                    
                    # Context-Flags setzen
                    if feature_result.category == 'HAAR_STRUKTUR' and 'lockig' in safe_label_l:
                        current_context['is_curly'] = True
                    elif feature_result.category == 'HAARFARBE':
                        # Dark-Hair Context für Melanin-Korrektur
                        if any(keyword in safe_label_l for keyword in ['black', 'dark', 'raven', 'jet', 'ebony']):
                            current_context['is_dark_hair'] = True
                            current_context['hair_color'] = safe_label
                        # Redhead Context für Green Eyes Protection
                        elif any(keyword in safe_label_l for keyword in ['auburn', 'copper', 'red', 'ginger', 'reddish']):
                            current_context['hair_color'] = safe_label
                        # Blonde Hair Context für Green Eyes Protection
                        elif any(keyword in safe_label_l for keyword in ['blonde', 'honey blonde', 'golden blonde', 'platinum blonde']):
                            current_context['hair_color'] = safe_label
                    elif feature_result.category == 'ALTER':
                        # Age-Items für Anti-Grau-Logik
                        if 'age_items' not in current_context:
                            current_context['age_items'] = []
                        current_context['age_items'].append({'label': safe_label, 'score': score_value})
                    elif feature_result.category == 'KLEIDUNG' and 'scarf' in safe_label_l:
                        current_context['has_scarf'] = True


            # Ergebnisse zum result-Dictionary hinzufügen
            result["feature_report"] = current_feature_report
            result["context"] = current_context  # DATEN-STENT: Reiche den vollständigen context weiter
            self.feature_report = current_feature_report
            logger.info(f"Feature Report erstellt: {len(current_feature_report)} Kategorien")
            logger.info(
                "DATEN-STENT: Context-Variablen: is_dark_hair=%s, age_group=%s",
                current_context.get("is_dark_hair"),
                current_context.get("age_group"),
            )
            
            # Legacy Support für Frontend/Orchestrator (handle list structure)
            legacy_tags = []
            for category, items in current_feature_report.items():
                if isinstance(items, list):
                    for item in items:
                        label = item.get('label')
                        if label:
                            legacy_tags.append(str(label))
                else:
                    label = items.get('label') if isinstance(items, dict) else None
                    if label:
                        legacy_tags.append(str(label))
            result["local_description"] = ", ".join(legacy_tags)
            self.current_tags = legacy_tags

        except Exception as e:
            logger.error(f"VISION ERROR: {e}", exc_info=True)
        finally:
            if owns_db_session and managed_db is not None:
                try:
                    managed_db.close()
                except Exception:
                    logger.warning("VISION: interne DB-Session konnte nicht sauber geschlossen werden.")
            # Explizite Freigabe request-lokaler Objekte
            plugins = None
            current_context = None
            current_feature_report = None
            self._reset_request_state()
            
        return result

    def get_tags_from_string(self, tags_string: str) -> list:
        """Gibt eine saubere Liste von Tags zurück."""
        if not tags_string: return []
        return [tag.strip() for tag in tags_string.split(",")]

    def force_save_person(
        self,
        name: str,
        encoding: np.ndarray,
        chat_id: int,
        profile_str: str = "",
        tags: str = ""
    ) -> None:
        """
        Diamond: Synchrone Personen-Speicherung mit Gesichts-Encoding und Tags.
        
        Diese Methode führt die komplette Hintergrund-Speicherung durch:
        - Person anlegen oder laden
        - Gesichts-Encoding hinzufügen
        - Tags als Memory-Facts speichern
        - Visuelles Profil speichern
        - Facts vom 'unbekannt' Subject übertragen
        
        Args:
            name: Der Name der Person
            encoding: Das Gesichts-Encoding (numpy array)
            chat_id: Die Chat-ID für Memory-Kontext
            profile_str: Optional visuelles Profil als String
            tags: Komma-separierte Tags/Merkmale
        """
        time.sleep(1)  # Kurze Verzögerung für Transaction-Safety
        db_session = SessionLocal()
        try:
            person = crud_vision.get_person_by_name(db_session, name)
            if not person:
                person = crud_vision.create_person_container(db_session, name)
            crud_vision.add_face_encoding(db_session, person.id, encoding)
            logger.info("BIOMETRIE ERWEITERT: Neues Gesicht fuer '%s' hinzugefuegt.", name)
            
            if tags:
                logger.info("SYNCHRONOUS SAVE: Sichere lokale Merkmale fuer '%s': %s", name, tags)
                for trait in tags.split(', '):
                    if not trait:
                        continue
                    fact_obj = {
                        'subject_name': name.lower(),
                        'category': 'Allgemein',
                        'predicate': 'hat_merkmal',
                        'object_value': trait.strip(),
                        'fact': f'Das System hat visuell erkannt: {trait.strip()}',
                        'canonical_key': f"{name.lower()}:vision:hat:{trait.strip().replace(' ', '_')}"
                    }
                    memory_manager.save_memory_snippet(
                        db_session, chat_id, fact_obj, source_type='vision_direct_learn'
                    )
            
            memory_manager.transfer_facts_to_new_subject(
                db_session, chat_id, 'unbekannt', name
            )
            
            if profile_str:
                fact_obj = {
                    'subject_name': name.lower(),
                    'category': 'Personen-Details',
                    'predicate': 'hat_visuelles_profil',
                    'object_value': profile_str,
                    'fact': f'Das System hat visuell erkannt: {profile_str}',
                    'canonical_key': f"{name.lower()}:vision:hat:{profile_str.replace(' ', '_')}"
                }
                memory_manager.save_memory_snippet(
                    db_session, chat_id, fact_obj,
                    source_type='vision_cloud',
                    source_metadata={'profile_string': profile_str}
                )
                logger.info('VISUELLES PROFIL GESPEICHERT fuer %s: %s...', name, profile_str[:50])
            
            db_session.commit()
            logger.info("[VISION-SERVICE] Person '%s' erfolgreich gespeichert (Chat %s)", name, chat_id)
        except Exception as e:
            logger.error('[VISION-SERVICE] Save-Fail fuer %s: %s', name, e)
        finally:
            db_session.close()

    def start_save_person_background(
        self,
        name: str,
        encoding: np.ndarray,
        chat_id: int,
        profile_str: str = "",
        tags: str = ""
    ) -> None:
        """
        Diamond: Startet die Hintergrund-Speicherung einer Person als Daemon-Thread.
        
        Sauberer Ersatz für die inline Thread-Logik im ChatOrchestrator.
        
        Args:
            name: Der Name der Person
            encoding: Das Gesichts-Encoding (numpy array)
            chat_id: Die Chat-ID für Memory-Kontext
            profile_str: Optional visuelles Profil als String
            tags: Komma-separierte Tags/Merkmale
        """
        if encoding is None:
            logger.warning("[VISION-SERVICE] Kein Encoding fuer '%s' - Hintergrund-Speicherung abgebrochen", name)
            return
        
        thread = threading.Thread(
            target=self.force_save_person,
            args=(name, encoding, chat_id, profile_str, tags),
            daemon=True
        )
        thread.start()
        logger.info("LERN-TRIGGER: '%s' erkannt. Hintergrund-Speicherung gestartet...", name)


# WICHTIG: Die Instanz wird am Ende der Datei erstellt und exportiert.
print("!!! VISION-SERVICE: Erstelle neue LocalVisionService Instanz mit aktualisiertem FootwearPlugin!")
vision_service = LocalVisionService()