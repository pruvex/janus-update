from .base import BaseVisionPlugin, FeatureResult
import logging

logger = logging.getLogger("janus_backend")

SUNGLASSES_LABELS = [
    "sunglasses",
    "dark sunglasses",
    "aviator sunglasses",
    "person wearing sunglasses",
    "sunglasses on head",
    "dark sunglasses on dark hair",
]

OPTICAL_GLASSES_LABELS = [
    "tortoise shell glasses on head",
    "eyewear on forehead",
]

CONFUSER_LABELS = [
    "hair shine",
    "curly hair highlights",
    "skin reflection",
    "forehead shine",
    "bare forehead",
    "hair without accessories",
]

class GlassesPlugin(BaseVisionPlugin):
    @property
    def name(self): return "Glasses"

    @property
    def clip_labels(self):
        return SUNGLASSES_LABELS + OPTICAL_GLASSES_LABELS + CONFUSER_LABELS

    def evaluate(self, scores, context):
        results = []
        max_sunglasses = max((scores.get(l, 0.0) for l in SUNGLASSES_LABELS), default=0.0)
        max_optical = max((scores.get(l, 0.0) for l in OPTICAL_GLASSES_LABELS), default=0.0)
        max_glasses = max(max_sunglasses, max_optical)
        max_confuser = max((scores.get(l, 0.0) for l in CONFUSER_LABELS), default=0.0)

        logger.info(
            "WAHRHEITS-ANKER: Max Glasses=%.4f, Max Optical=%.4f, Max Sunglasses=%.4f, Max Confuser=%.4f",
            max_glasses,
            max_optical,
            max_sunglasses,
            max_confuser,
        )
        
        # 3-Zonen-Entscheidungslogik
        def final_glasses_decision(max_glasses, max_confuser):
            # Zonen-Definition (Physik-basiert)
            HARD_NOISE = 0.003        # Alles darunter ist Rauschen
            SOFT_STRUCTURAL = 0.008   # Typischer Bereich für Brillen-Schatten
            DOMINANCE = 1.8           # Faktor für "Harte Beweise"
            
            # 1. Zone: Absolutes Rauschen (Maggy-Filter)
            if max_glasses < HARD_NOISE:
                return "KEINE_BRILLE"
            
            # 2. Zone: Harter Beweis (Elena-Idealfall)
            if max_glasses > max_confuser * DOMINANCE:
                return "BRILLE"
            
            # 3. Zone: Strukturell schwach aber konsistent (Der Retter für Elena im Schatten)
            # Wenn das Signal okay ist (0.008) UND der Confuser nicht übermächtig ist (Faktor 1.2)
            if max_glasses >= SOFT_STRUCTURAL and max_confuser < (max_glasses * 1.2):
                return "BRILLE_STRUKTURELL"
            
            return "KEINE_BRILLE"
        
        decision = final_glasses_decision(max_glasses, max_confuser)
        logger.info(f"WAHRHEITS-ANKER: Entscheidung={decision}")

        def _best_label(labels):
            if not labels:
                return ""
            return max(labels, key=lambda l: scores.get(l, 0.0))

        best_optical_label = _best_label(OPTICAL_GLASSES_LABELS)
        best_sunglasses_label = _best_label(SUNGLASSES_LABELS)

        # Klassen-Selektion: in Ambiguitaet konservativ gegen Sonnenbrillen-Halluzination.
        selected_label = ""
        if best_sunglasses_label and max_sunglasses >= max_optical * 1.20 and max_sunglasses >= 0.01:
            selected_label = best_sunglasses_label
        elif best_optical_label and max_optical >= max_sunglasses * 0.95:
            selected_label = best_optical_label
        else:
            selected_label = best_optical_label or best_sunglasses_label

        if decision == "BRILLE":
            status = "SICHER"
            best_score = scores.get(selected_label, 0.0)
            if selected_label:
                results.append(FeatureResult("KOPF_ACCESSOIRE", selected_label, status, best_score))
                logger.info(f"PLUGIN Glasses: {selected_label} (SICHER, Score: {best_score:.4f})")

        elif decision == "BRILLE_STRUKTURELL":
            status = "WAHRSCHEINLICH"
            best_score = scores.get(selected_label, 0.0)
            if selected_label:
                results.append(FeatureResult("KOPF_ACCESSOIRE", selected_label, status, best_score))
                logger.info(f"PLUGIN Glasses: {selected_label} (WAHRSCHEINLICH, Score: {best_score:.4f})")

        else:
            logger.info(f"PLUGIN Glasses: Keine gültige Brille gefunden - Rauschen dominiert")

        return results
