from .base import BaseVisionPlugin, FeatureResult
import logging

logger = logging.getLogger("janus_backend")

class AccessoryMetaPlugin(BaseVisionPlugin):
    @property
    def name(self): return "AccessoryMeta"

    @property
    def clip_labels(self):
        # Direkte Brillen-Labels (von glasses_plugin)
        direct_labels = [
            "sunglasses on head", "glasses on face", "metallic frames", "rimless glasses",
            "sunglasses perched on head", "eyewear on forehead", "dark glasses on top of head",
            "dark sunglasses on top of head", "brown lenses on head", "tortoise shell sunglasses",
            "dark sunglasses on dark hair", "reflective glass on forehead", "tortoise shell glasses on head",
            "shiny sunglasses lenses", "dark frames on top of head", "plastic eyewear on hair"
        ]
        
        # Indirekte Anomalie-Labels (Die "Elena-Retter")
        indirect_labels = [
            "reflective object on hair", "hard object on head", "straight line on hair",
            "shiny plastic in hair", "symmetrical object on forehead", "glass-like reflection"
        ]
        
        return direct_labels + indirect_labels

    def evaluate(self, scores, context):
        results = []
        
        # AccessoryMetaPlugin deaktiviert: Nur noch Struktur-Beweise liefern
        # Keine eigenen Brillen-Entscheidungen mehr treffen!
        # Das GlassesPlugin mit Wahrheits-Anker hat die alleinige Hoheit
        
        # Nur noch minimale Struktur-Erkennung für Debug-Zwecke
        struktur_labels = [
            "hard object on head", "straight line on hair", "symmetrical object on forehead"
        ]
        
        max_struktur_score = max([scores.get(label, 0.0) for label in struktur_labels])
        
        # Debug-Logging
        logger.info(f"ACCESSORY META DEAKTIVIERT: Struktur-Score={max_struktur_score:.4f}")
        
        # Keine Ergebnisse mehr produzieren - GlassesPlugin entscheidet allein!
        # Wenn nichts gefunden, expliziter REJECTED-Eintrag
        results.append(FeatureResult("KOPF_ACCESSOIRE", "kein Accessoire", "REJECTED", 0.0))
            
        return results
