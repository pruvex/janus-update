import logging
from .base import BaseVisionPlugin, FeatureResult

logger = logging.getLogger("janus_backend")


class OuterwearPlugin(BaseVisionPlugin):
    @property
    def name(self):
        return "Outerwear"

    @property
    def clip_labels(self):
        return [
            # Outerwear targets
            "trench coat",
            "long coat",
            "wool coat",
            "brown coat",
            "brown trench coat",
            "puffer jacket",
            "quilted jacket",
            "down jacket",
            "blazer",
            "suit jacket",
            "sport coat",
            "cardigan",
            "knit cardigan",
            "open front cardigan",
            # Inner layer targets
            "turtleneck sweater",
            "roll neck sweater",
            "dark pullover",
            "dark sweater",
            "black sweater",
            "dress shirt",
            "button-up shirt",
            "patterned top",
            "floral dress",
            # Print / pattern targets
            "floral pattern",
            "graphic print",
            "text print",
            # Confusers
            "plain shirt",
            "plain sweater",
            "fabric folds",
            "shadow on clothing",
            "wrinkled fabric",
            # Negatives
            "no coat",
            "no jacket",
            "no cardigan",
            "no layering",
            "no print",
        ]

    def evaluate(self, scores, context):
        results = []

        outerwear_targets = {
            "braunen Mantel": ["trench coat", "long coat", "wool coat", "brown coat", "brown trench coat"],
            "Steppjacke": ["puffer jacket", "quilted jacket", "down jacket"],
            "Sakko": ["blazer", "suit jacket", "sport coat"],
            "Strickjacke": ["cardigan", "knit cardigan", "open front cardigan"],
        }

        inner_targets = {
            "Rollkragenpullover": ["turtleneck sweater", "roll neck sweater"],
            "dunklen Pullover": ["dark pullover", "dark sweater", "black sweater", "plain sweater"],
            "Hemd": ["dress shirt", "button-up shirt"],
            "gemusterten Oberteil": ["patterned top", "floral dress"],
        }

        print_targets = ["floral pattern", "graphic print", "text print"]

        confusers = ["plain shirt", "plain sweater", "fabric folds", "shadow on clothing", "wrinkled fabric"]
        negatives_outer = ["no coat", "no jacket", "no cardigan", "no layering"]
        negatives_print = ["no print"]

        max_confuser = max(scores.get(l, 0.0) for l in confusers)
        max_neg_outer = max(scores.get(l, 0.0) for l in negatives_outer)
        max_neg_print = max(scores.get(l, 0.0) for l in negatives_print)

        # --- OUTERWEAR ---
        best_outerwear = None
        best_outer_score = 0.0
        best_outer_label = None

        for name, labels in outerwear_targets.items():
            label = max(labels, key=lambda l: scores.get(l, 0.0))
            score = scores.get(label, 0.0)
            if score > best_outer_score:
                best_outer_score = score
                best_outerwear = name
                best_outer_label = label

        outer_delta = best_outer_score - max_confuser

        outer_confirmed = (
            best_outer_score > 0.016
            and outer_delta > 0.003
            and best_outer_score > (max_neg_outer + 0.003)
        )

        # Make long coats a bit stricter (often confused with dresses)
        if best_outerwear == "braunen Mantel":
            outer_confirmed = (
                best_outer_score > 0.018
                and outer_delta > 0.004
                and best_outer_score > (max_neg_outer + 0.004)
            )

        # Make Sakko stricter to avoid coat->blazer swaps
        if best_outerwear == "Sakko":
            outer_confirmed = (
                best_outer_score > 0.02
                and outer_delta > 0.004
                and best_outer_score > (max_neg_outer + 0.004)
            )

        if outer_confirmed:
            context["outerwear"] = best_outerwear
            results.append(FeatureResult("OUTERWEAR", best_outerwear, "WAHRSCHEINLICH", best_outer_score))
            logger.info(
                f"Outerwear-Precision: {best_outerwear} ({best_outer_label}) Score={best_outer_score:.4f}, Conf={max_confuser:.4f}, "
                f"Delta={outer_delta:.4f}, Neg={max_neg_outer:.4f}"
            )

        # --- INNER LAYER ---
        best_inner = None
        best_inner_score = 0.0
        best_inner_label = None

        for name, labels in inner_targets.items():
            label = max(labels, key=lambda l: scores.get(l, 0.0))
            score = scores.get(label, 0.0)
            if score > best_inner_score:
                best_inner_score = score
                best_inner = name
                best_inner_label = label

        # If roll-neck and dark-pullover evidence are close, prefer dark pullover to reduce turtleneck false positives
        roll_labels = inner_targets.get("Rollkragenpullover", [])
        dark_labels = inner_targets.get("dunklen Pullover", [])
        roll_score = max([scores.get(l, 0.0) for l in roll_labels]) if roll_labels else 0.0
        dark_score = max([scores.get(l, 0.0) for l in dark_labels]) if dark_labels else 0.0
        if best_outerwear == "braunen Mantel" and dark_score > 0.004:
            best_inner = "dunklen Pullover"
            best_inner_label = max(dark_labels, key=lambda l: scores.get(l, 0.0)) if dark_labels else best_inner_label
            best_inner_score = dark_score
        if best_inner == "Rollkragenpullover" and dark_score >= (roll_score * 0.85) and dark_score > 0.005:
            best_inner = "dunklen Pullover"
            best_inner_label = max(dark_labels, key=lambda l: scores.get(l, 0.0)) if dark_labels else best_inner_label
            best_inner_score = dark_score

        inner_delta = best_inner_score - max_confuser

        inner_confirmed = (
            best_inner_score > 0.014
            and inner_delta > 0.0025
            and best_inner_score > (max_neg_outer + 0.001)
        )

        # Softer path for trenchcoat + turtleneck scenarios (Cluster 10.1)
        if not inner_confirmed and outer_confirmed and best_outerwear == "braunen Mantel" and best_inner == "Rollkragenpullover":
            inner_confirmed = best_inner_score > 0.004 and inner_delta > 0.0005

        if inner_confirmed:
            context["inner_layer"] = best_inner
            results.append(FeatureResult("INNER_LAYER", best_inner, "WAHRSCHEINLICH", best_inner_score))
            logger.info(
                f"InnerLayer-Precision: {best_inner} ({best_inner_label}) Score={best_inner_score:.4f}, Conf={max_confuser:.4f}, "
                f"Delta={inner_delta:.4f}"
            )

        # --- PRINT (pattern / graphic) ---
        best_print_label = max(print_targets, key=lambda l: scores.get(l, 0.0))
        best_print_score = scores.get(best_print_label, 0.0)
        print_delta = best_print_score - max_confuser

        plain_score = max(scores.get("plain shirt", 0.0), scores.get("plain sweater", 0.0))

        print_confirmed = (
            best_print_score > 0.018
            and print_delta > 0.003
            and best_print_score > (max_neg_print + 0.004)
            and not (plain_score > (best_print_score * 0.95) and plain_score > 0.02)
        )

        # Softer path for floral patterns (often subtle in CLIP softmax groups)
        if not print_confirmed and best_print_label == "floral pattern":
            print_confirmed = best_print_score > 0.008 and print_delta > 0.001 and not (plain_score > 0.04)

        # Layering-aware print fallback: only allow very soft print confirmation when we already have
        # a strong layering context (reduces cross-cluster hallucinations)
        if (
            not print_confirmed
            and outer_confirmed
            and inner_confirmed
            and best_outerwear == "Strickjacke"
            and best_inner == "gemusterten Oberteil"
        ):
            print_confirmed = (
                best_print_score > 0.002
                and best_print_score > max_neg_print
                and not (plain_score > 0.05)
            )

        if print_confirmed:
            context["has_print"] = True
            results.append(FeatureResult("PRINT", "Grafik-Print", "WAHRSCHEINLICH", best_print_score))
            logger.info(
                f"Print-Precision: {best_print_label} Score={best_print_score:.4f}, Conf={max_confuser:.4f}, "
                f"Delta={print_delta:.4f}, Plain={plain_score:.4f}, Neg={max_neg_print:.4f}"
            )

        return results
