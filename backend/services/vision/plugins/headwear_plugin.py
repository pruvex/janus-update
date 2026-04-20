from .base import BaseVisionPlugin, FeatureResult
import logging

logger = logging.getLogger("janus_backend")

class HeadwearPlugin(BaseVisionPlugin):
    @property
    def name(self): return "Headwear"

    @property
    def clip_labels(self):
        return [
            # --- TARGETS: KOPFBEDECKUNG ---
            "grey beanie", "knit cap", "winter hat", "wool hat",
            "black baseball cap", "baseball hat", "trucker hat", "sports cap",
            "wide brim hat", "sun hat", "straw hat",
            
            # --- TARGETS: AUDIO ---
            "large over-ear headphones", "gaming headset", "wireless headphones", "studio headphones",
            "white earbuds", "in-ear headphones", "airpods",
            
            # --- CONFUSERS (Rauschen / Verwechslungsgefahr) ---
            "hoodie", "hooded sweatshirt",  # Kapuze ist keine Mütze
            "hair volume", "styled hair", "messy hair bun", "high ponytail", # Frisur vs Mütze
            "earmuffs", "winter ear warmers", # Ohrenschützer vs Kopfhörer
            "shadow on forehead", "dark hair", # Schatten vs Cap
            "hair clips", "large earrings", # Schmuck vs Audio
            
            # --- NEGATIVES (Null-Hypothese / Anker) ---
            "bare head", "no hat", "uncovered hair", "visible hairstyle",
            "no headphones", "visible ears", "bare ears", "no headset"
        ]

    def evaluate(self, scores, context):
        results = []
        
        # --- TEIL 1: KOPFBEDECKUNG ---
        headwear_labels = [
            "grey beanie", "knit cap", "winter hat", "wool hat",
            "black baseball cap", "baseball hat", "trucker hat", "sports cap",
            "wide brim hat", "sun hat", "straw hat"
        ]
        
        # Beste Kopfbedeckung finden
        best_headwear = max(headwear_labels, key=lambda l: scores.get(l, 0.0))
        headwear_score = scores.get(best_headwear, 0.0)
        
        # Confusers für Headwear (Haare, Kapuzen, Schatten)
        hw_confusers = ["hoodie", "hair volume", "styled hair", "messy hair bun", "shadow on forehead", "dark hair"]
        max_hw_confuser = max([scores.get(l, 0.0) for l in hw_confusers])
        
        # Negatives (Null-Hypothese)
        hw_negatives = ["bare head", "no hat", "uncovered hair", "visible hairstyle"]
        max_hw_negative = max([scores.get(l, 0.0) for l in hw_negatives])
        
        # Metriken berechnen
        snr_hw = headwear_score - max_hw_confuser
        delta_hw = headwear_score - max_hw_negative
        
        # Context Check: Wenn sehr lockiges/voluminöses Haar erkannt wurde, Schwelle erhöhen
        threshold_hw = 0.015
        if context.get("is_curly", False):
            threshold_hw = 0.025 # Locken werden oft als Mützen fehlanalysiert
            
        # Entscheidung Headwear
        status_hw = "REJECTED"
        if headwear_score > threshold_hw and delta_hw > 0.005:
            if snr_hw > 0.002:
                status_hw = "SICHER"
            else:
                status_hw = "WAHRSCHEINLICH" # Guter Score, aber Rauschen vorhanden
        
        if status_hw != "REJECTED":
            # Label-Bereinigung für Orchestrator Mapping
            clean_label = best_headwear
            if any(x in best_headwear for x in ["beanie", "knit", "wool", "winter hat"]):
                clean_label = "grey beanie" # Mapping Key für Orchestrator
            elif any(x in best_headwear for x in ["cap", "baseball", "trucker"]):
                clean_label = "black baseball cap" # Mapping Key für Orchestrator
                
            results.append(FeatureResult("KOPF_BEDECKUNG", clean_label, status_hw, headwear_score))
            logger.info(f"🧢 Headwear DETECTED: {clean_label} ({status_hw}, Score: {headwear_score:.4f}, Delta: {delta_hw:.4f})")
        else:
            logger.info(f"🧢 Headwear REJECTED: {best_headwear} (Score: {headwear_score:.4f} < {threshold_hw} or Delta {delta_hw:.4f} low)")


        # --- TEIL 2: AUDIO HARDWARE ---
        audio_labels = [
            "large over-ear headphones", "gaming headset", "wireless headphones", "studio headphones",
            "white earbuds", "in-ear headphones", "airpods"
        ]
        
        best_audio = max(audio_labels, key=lambda l: scores.get(l, 0.0))
        audio_score = scores.get(best_audio, 0.0)
        
        # Confusers für Audio (Ohrenschützer, Frisur-Knoten, Ohrringe)
        au_confusers = ["earmuffs", "messy hair bun", "large earrings", "hair clips"]
        max_au_confuser = max([scores.get(l, 0.0) for l in au_confusers])
        
        # Negatives (Null-Hypothese)
        au_negatives = ["no headphones", "visible ears", "bare ears", "no headset"]
        max_au_negative = max([scores.get(l, 0.0) for l in au_negatives])
        
        # Metriken
        snr_au = audio_score - max_au_confuser
        delta_au = audio_score - max_au_negative
        
        # Entscheidung Audio
        status_au = "REJECTED"
        # Audio braucht hohe Präzision, da oft mit Haaren/Ohren verwechselt
        if audio_score > 0.02 and delta_au > 0.01: 
            if snr_au > 0.005:
                status_au = "SICHER"
            elif snr_au > -0.005: # Leichtes Rauschen erlaubt bei hohem Score
                status_au = "WAHRSCHEINLICH"
                
        if status_au != "REJECTED":
            clean_label = best_audio
            if "headphones" in best_audio or "headset" in best_audio:
                clean_label = "large over-ear headphones" # Mapping Key
                
            results.append(FeatureResult("AUDIO_HARDWARE", clean_label, status_au, audio_score))
            logger.info(f"🎧 Audio DETECTED: {clean_label} ({status_au}, Score: {audio_score:.4f}, Delta: {delta_au:.4f})")

        return results