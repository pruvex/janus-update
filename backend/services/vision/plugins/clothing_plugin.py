import logging
from .base import BaseVisionPlugin, FeatureResult

logger = logging.getLogger("janus_backend")

class ClothingPlugin(BaseVisionPlugin):
    @property
    def name(self): return "Clothing"

    @property
    def clip_labels(self):
        return [
                "dark patterned top", "flannel shirt", "solid black top", "white blouse", "gold text on shirt",
                "solid black cotton shirt", "pure black top", "black t-shirt", "black shirt", "black top", "dark clothing",  # Diamond-Abschluss
                "white t-shirt", "plain white t-shirt", "white crew neck t-shirt",
                "knitted wool scarf", "plaid textile pattern", "woven fabric around neck", "checkered cloth",  # Präzise Textil-Begriffe
                "plaid pattern", "checkered fabric", "floral print", "knitted texture", "turtleneck",  # NEU: Muster-Erkennung für Cluster 3

                # Cluster 6: Handbekleidung
                # Targets
                "black leather gloves", "dark leather gloves",
                "colorful knitted gloves", "patterned mittens", "wool gloves",
                "fingerless gloves", "tactical gloves", "cut-off gloves", "biker gloves",
                # Confusers
                "folded arms", "hands in pockets", "dark sleeves", "holding a dark object",
                # Negatives
                "bare hands", "uncovered fingers", "visible skin on hands", "no gloves",
        ]

    def evaluate(self, scores, context):
        # Gegenlicht-Check (simuliert)
        is_backlight = False # Könnte man über ein SettingPlugin noch holen

        # KLEIDUNG-Bestimmung: nur echte Kleidung-/Muster-/Schal-Labels zulassen
        clothing_only_labels = [
            "dark patterned top", "flannel shirt", "solid black top", "white blouse", "gold text on shirt",
            "solid black cotton shirt", "pure black top", "black t-shirt", "black shirt", "black top", "dark clothing",
            "white t-shirt", "plain white t-shirt", "white crew neck t-shirt",
            "knitted wool scarf", "plaid textile pattern", "woven fabric around neck", "checkered cloth",
            "plaid pattern", "checkered fabric", "floral print", "knitted texture", "turtleneck",
        ]

        best_label = max(clothing_only_labels, key=lambda l: scores.get(l, 0.0))
        score = scores.get(best_label, 0.0)
        
        # Muster-Erkennung für Cluster 3 (Enhanced)
        pattern_labels = [
            "plaid pattern",
            "checkered fabric",
            "floral print",
            "knitted texture",
            "patterned fabric",
            "geometric pattern",
        ]
        complex_pattern_labels = ["plaid pattern", "checkered fabric", "floral print", "knitted texture"]
        max_pattern_score = max([scores.get(label, 0.0) for label in pattern_labels])
        max_complex_pattern_score = max([scores.get(label, 0.0) for label in complex_pattern_labels])

        solid_top_labels = [
            "solid black top",
            "solid black cotton shirt",
            "pure black top",
            "black t-shirt",
            "black shirt",
            "black top",
            "white blouse",
            "white t-shirt",
            "plain white t-shirt",
            "white crew neck t-shirt",
        ]
        max_solid_score = max([scores.get(label, 0.0) for label in solid_top_labels])

        pattern_delta = max_pattern_score - max_solid_score
        has_pattern = max_pattern_score > 0.06 and pattern_delta > 0.02
        has_complex_pattern = max_complex_pattern_score > 0.07 and pattern_delta > 0.03  # Higher threshold for complex patterns
        
        # Kontext-Flags für Muster-Erkennung
        context["has_pattern"] = has_pattern
        context["has_complex_pattern"] = has_complex_pattern

        turtleneck_score = scores.get("turtleneck", 0.0)
        if turtleneck_score > 0.015 and turtleneck_score >= (max_solid_score * 0.8):
            context["clothing_type"] = "turtleneck"

        if has_pattern:
            # Bestimme den Kleidungstyp
            if "turtleneck" in best_label:
                context["clothing_type"] = "turtleneck"
            elif "scarf" in best_label:
                context["clothing_type"] = "scarf"
            else:
                context["clothing_type"] = "patterned"
            
            # Enhanced logging for pattern detection
            if has_complex_pattern:
                logger.info(f"Komplexes Muster erkannt: {best_label} ({max_complex_pattern_score:.4f}) -> has_complex_pattern=True")
            else:
                logger.info(f"Einfaches Muster erkannt: {best_label} ({max_pattern_score:.4f}) -> has_complex_pattern=False")
        
        # Schal-Erkennung: Präzisions-Logik mit Negativ-Check
        scarf_labels = ["knitted wool scarf", "woven fabric around neck"]
        max_scarf_score = max([scores.get(label, 0.0) for label in scarf_labels])
        
        # Negativ-Check: Schal darf nur erkannt werden, wenn stärker als Konkurrenten
        hair_score = scores.get("red curly hair", 0.0)
        shirt_score = scores.get("patterned shirt", 0.0)
        max_competitor_score = max(hair_score, shirt_score, max_pattern_score, max_solid_score)
        
        # Delta-Check: Nur wenn Schal stärker als Konkurrenten + Margin
        delta = max_scarf_score - max_competitor_score
        scarf_confirmed = max_scarf_score > 0.03 and delta > 0.01
        
        if scarf_confirmed:
            context["has_scarf"] = True
            # Finde das beste Schal-Label für die Ausgabe
            best_scarf_label = max(scarf_labels, key=lambda l: scores.get(l, 0.0))
            if scores.get(best_scarf_label, 0.0) > 0.01:
                best_label = best_scarf_label
                score = scores.get(best_scarf_label, 0.0)
        else:
            context["has_scarf"] = False
        
        # Präzisions-Logging
        if max_scarf_score > 0.01:
            logger.info(f"Scarf-Precision: Scarf={max_scarf_score:.4f}, Competitor={max_competitor_score:.4f}, Delta={delta:.4f}, Confirmed={scarf_confirmed}")

        # Handschuh-Erkennung (Cluster 6): separate SNR/Delta-Logik
        glove_targets = [
            "black leather gloves",
            "dark leather gloves",
            "colorful knitted gloves",
            "patterned mittens",
            "wool gloves",
            "fingerless gloves",
            "tactical gloves",
            "cut-off gloves",
            "biker gloves",
        ]
        glove_confusers = [
            "folded arms",
            "hands in pockets",
            "dark sleeves",
            "holding a dark object",
        ]
        glove_negatives = [
            "bare hands",
            "uncovered fingers",
            "visible skin on hands",
            "no gloves",
        ]

        max_glove_score = max([scores.get(label, 0.0) for label in glove_targets])
        max_confuser_score = max([scores.get(label, 0.0) for label in glove_confusers])
        max_negative_score = max([scores.get(label, 0.0) for label in glove_negatives])

        glove_delta = max_glove_score - max_confuser_score

        best_glove_label = max(glove_targets, key=lambda l: scores.get(l, 0.0))
        glove_score = scores.get(best_glove_label, 0.0)

        fingerless_labels = [
            "fingerless gloves",
            "tactical gloves",
            "cut-off gloves",
            "biker gloves",
        ]
        best_fingerless_label = max(fingerless_labels, key=lambda l: scores.get(l, 0.0))
        best_fingerless_score = scores.get(best_fingerless_label, 0.0)

        if best_fingerless_score > 0.07 and max_confuser_score > glove_score:
            best_glove_label = best_fingerless_label
            glove_score = best_fingerless_score
        elif best_fingerless_score > 0.02 and (glove_score - best_fingerless_score) < 0.12:
            best_glove_label = best_fingerless_label
            glove_score = best_fingerless_score

        best_glove_label_l = best_glove_label.lower()
        fingerless_like = any(
            k in best_glove_label_l
            for k in ["fingerless", "half finger", "cut-off", "cut off", "biker", "tactical"]
        )

        glove_delta_best = glove_score - max_confuser_score
        glove_confirmed = glove_score > 0.008 and glove_delta > 0.003
        if fingerless_like:
            glove_confirmed = (
                glove_score > 0.07
                or (
                    glove_score > 0.15
                    and glove_score > (max_negative_score + 0.03)
                )
            )
        else:
            glove_confirmed = glove_confirmed and max_negative_score < 0.01

        if glove_confirmed or glove_score > 0.004:
            logger.info(
                f"Glove-Precision: Glove={max_glove_score:.4f}, Confuser={max_confuser_score:.4f}, "
                f"Delta={glove_delta:.4f}, Negative={max_negative_score:.4f}, Label={best_glove_label}"
            )
        
        # Bei Kleidung vertrauen wir dem stärksten Signal, aber mit Mindestschwelle
        # Halluzinations-Stopp: Wenn kein Kleidungs-Label einen Score von > 0.001 erreicht, gib ein leeres Ergebnis zurück
        if score <= 0.001:
            results = [FeatureResult("KLEIDUNG", "keine Kleidung erkannt", "REJECTED", 0.0)]
        elif score > 0.01:  # Mindestschwelle für SICHER-Status
            status = "SICHER"
        elif score > 0.005:
            status = "WAHRSCHEINLICH"
        else:
            status = "HINWEIS"

        if score > 0.001:
            results = [FeatureResult("KLEIDUNG", best_label, status, score)]

        if glove_confirmed and best_glove_label:
            glove_status = "SICHER" if glove_score > 0.01 else "WAHRSCHEINLICH" if glove_score > 0.005 else "HINWEIS"
            results.append(FeatureResult("HANDBEKLEIDUNG", best_glove_label, glove_status, glove_score))

        return results
