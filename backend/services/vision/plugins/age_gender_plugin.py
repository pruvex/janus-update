from .base import BaseVisionPlugin, FeatureResult
import logging
import numpy as np

logger = logging.getLogger("janus_backend")

class AgeGenderPlugin(BaseVisionPlugin):
    @property
    def name(self): return "AgeGender"

    @property
    def clip_labels(self):
        return [
            "woman in her 20s", "woman in her 30s", "woman in her 40s", "woman in her 50s", "woman in her 60s",
            "man in his 20s", "man in his 30s", "man in his 40s", "man in his 50s", "man in his 60s",
            "woman", "man"
        ]

    def evaluate(self, scores, context):
        results = []
        
        # Geschlecht
        g_labels = ["woman", "man"]
        g_scores = [scores.get(l, 0.0) for l in g_labels]
        best_g = g_labels[np.argmax(g_scores)]
        context["gender"] = best_g
        results.append(FeatureResult("GESCHLECHT", best_g, "SICHER", max(g_scores)))

        # Alter (Winner-Takes-All)
        age_labels = [l for l in self.clip_labels if "in h" in l]
        best_age = max(age_labels, key=lambda l: scores.get(l, 0.0))
        score = scores.get(best_age, 0.0)
        status = "SICHER" if score > 0.05 else "WAHRSCHEINLICH"
        
        # DATEN-STENT: Altersgruppe im Context speichern
        if "in his" in best_age or "in her" in best_age:
            age_group = best_age.split()[-1]  # "20s", "30s", "40s", etc.
            context["age_group"] = age_group
            logger.info(f"🔥 DATEN-STENT: age_group={age_group} (aus {best_age})")
        
        results.append(FeatureResult("ALTER", best_age, status, score))
        return results
