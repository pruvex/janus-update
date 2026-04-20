from .base import BaseVisionPlugin, FeatureResult
import logging

logger = logging.getLogger("janus_backend")

class AccessoryMetaPlugin(BaseVisionPlugin):
    @property
    def name(self): return "AccessoryMeta"

    @property
    def clip_labels(self):
        # POSITIVE: Direkte Objekte + Indirekte Anomalien
        positive_labels = [
            # Direkte Brillen-Labels
            "sunglasses on head", "glasses on face", "metallic frames", "rimless glasses",
            "sunglasses perched on head", "eyewear on forehead", "dark glasses on top of head",
            "dark sunglasses on top of head", "brown lenses on head", "tortoise shell sunglasses",
            "dark sunglasses on dark hair", "reflective glass on forehead", "tortoise shell glasses on head",
            "shiny sunglasses lenses", "dark frames on top of head", "plastic eyewear on hair",
            # Indirekte Anomalie-Labels
            "reflective object on hair", "hard object on head", "straight line on hair",
            "shiny plastic in hair", "symmetrical object on forehead", "glass-like reflection"
        ]
        
        # NEGATIVES: Explizite Abwesenheit (Null-Hypothese)
        negative_labels = [
            "no glasses", "bare forehead", "plain hair without accessories", 
            "empty hair", "no eyewear", "clear forehead", "no headwear"
        ]
        
        # NOISE: Umgebungsfaktoren
        noise_labels = [
            "hair shine", "curly hair reflections", "skin shine", "light reflection",
            "natural hair gloss", "light glare", "specular reflection"
        ]
        
        return positive_labels + negative_labels + noise_labels

    def evaluate(self, scores, context):
        results = []
        
        # Label-Gruppen definieren
        positive_labels = [
            "sunglasses on head", "glasses on face", "metallic frames", "rimless glasses",
            "sunglasses perched on head", "eyewear on forehead", "dark glasses on top of head",
            "dark sunglasses on top of head", "brown lenses on head", "tortoise shell sunglasses",
            "dark sunglasses on dark hair", "reflective glass on forehead", "tortoise shell glasses on head",
            "shiny sunglasses lenses", "dark frames on top of head", "plastic eyewear on hair",
            "reflective object on hair", "hard object on head", "straight line on hair",
            "shiny plastic in hair", "symmetrical object on forehead", "glass-like reflection"
        ]
        
        negative_labels = [
            "no glasses", "bare forehead", "plain hair without accessories", 
            "empty hair", "no eyewear", "clear forehead", "no headwear"
        ]
        
        noise_labels = [
            "hair shine", "curly hair reflections", "skin shine", "light reflection",
            "natural hair gloss", "light glare", "specular reflection"
        ]
        
        # Diamond-Mathematik: Delta & SNR Berechnung
        pos_signal = max([scores.get(label, 0.0) for label in positive_labels])
        neg_signal = max([scores.get(label, 0.0) for label in negative_labels])
        noise_floor = max([scores.get(label, 0.0) for label in noise_labels])
        
        # Beweisübergewicht und Signal-Rausch-Verhältnis
        delta = pos_signal - neg_signal
        snr = pos_signal / (noise_floor + 1e-6)  # Verhindere Division durch Null
        
        # Debug-Logging für Diamond-Mathematik
        logger.info(f"DIAMOND MATH: Pos={pos_signal:.4f}, Neg={neg_signal:.4f}, Noise={noise_floor:.4f}")
        logger.info(f"DIAMOND MATH: Delta={delta:.4f}, SNR={snr:.2f}")
        
        # Universelle Validierung (Diamond Thresholds)
        if delta > 0.012 and snr > 2.0:
            status = "SICHER"
        elif delta > 0.005 and snr > 1.3:
            status = "WAHRSCHEINLICH"
        else:
            status = "REJECTED"  # Kein HINWEIS mehr für finalen Text!
        
        # Bestes Label finden (für Debug-Zwecke)
        if pos_signal > 0:
            best_label = max(positive_labels, key=lambda l: scores.get(l, 0.0))
            best_score = scores.get(best_label, 0.0)
            
            if status != "REJECTED":
                results.append(FeatureResult("KOPF_ACCESSOIRE", best_label, status, best_score))
                logger.info(f"PLUGIN AccessoryMeta: {best_label} ({status}, Delta={delta:.4f}, SNR={snr:.2f})")
        
        # Wenn nichts gefunden, expliziter REJECTED-Eintrag
        if not results:
            results.append(FeatureResult("KOPF_ACCESSOIRE", "kein Accessoire", "REJECTED", 0.0))
            
        return results
