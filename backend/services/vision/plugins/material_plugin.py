import logging
from .base import BaseVisionPlugin, FeatureResult

logger = logging.getLogger("janus_backend")


class MaterialPlugin(BaseVisionPlugin):
    @property
    def name(self):
        return "Material"

    @property
    def clip_labels(self):
        return [
            # Materials (targets)
            "shiny black leather",
            "leather jacket",
            "chunky wool knit",
            "wool cardigan",
            "blue denim fabric",
            "denim jacket",
            # Prints / graphics (targets)
            "graphic print on t-shirt",
            "shirt with bold text",
            "adventure typography",
            # Confusers
            "fabric creases",
            "specular highlights on skin",
            "plain blank t-shirt",
            "plain shirt",
            "smooth fabric",
            # Negatives
            "no print",
            "no graphic",
            "no text on shirt",
            "no leather",
            "no denim",
            "no wool",
        ]

    def evaluate(self, scores, context):
        results = []

        material_targets = {
            "leather": ["shiny black leather", "leather jacket"],
            "wool": ["chunky wool knit", "wool cardigan"],
            "denim": ["blue denim fabric", "denim jacket"],
        }
        print_targets = [
            "graphic print on t-shirt",
            "shirt with bold text",
            "adventure typography",
        ]

        confusers = [
            "fabric creases",
            "specular highlights on skin",
            "plain blank t-shirt",
            "plain shirt",
            "smooth fabric",
        ]
        negatives_print = ["no print", "no graphic", "no text on shirt"]
        negatives_material = ["no leather", "no denim", "no wool"]

        max_confuser = max(scores.get(l, 0.0) for l in confusers)
        max_neg_print = max(scores.get(l, 0.0) for l in negatives_print)
        max_neg_material = max(scores.get(l, 0.0) for l in negatives_material)

        # --- MATERIAL ---
        material_best_type = None
        material_best_label = None
        material_best_score = 0.0
        for mat_type, labels in material_targets.items():
            label = max(labels, key=lambda l: scores.get(l, 0.0))
            score = scores.get(label, 0.0)
            if score > material_best_score:
                material_best_score = score
                material_best_label = label
                material_best_type = mat_type

        material_delta = material_best_score - max_confuser

        material_confirmed = (
            material_best_score > 0.014
            and material_delta > 0.003
            and material_best_score > (max_neg_material + 0.002)
        )

        # Strong leather guard (specular highlights can fake leather)
        if material_best_type == "leather":
            material_confirmed = (
                material_best_score > 0.018
                and material_delta > 0.004
                and material_best_score > (max_neg_material + 0.003)
            )

        if material_confirmed:
            context["material_type"] = material_best_type
            if material_best_score > 0.05:
                status = "SICHER"
            elif material_best_score > 0.03:
                status = "WAHRSCHEINLICH"
            else:
                status = "HINWEIS"

            logger.info(
                f"Material-Precision: Type={material_best_type}, Score={material_best_score:.4f}, Confuser={max_confuser:.4f}, "
                f"Delta={material_delta:.4f}, Neg={max_neg_material:.4f}, Label={material_best_label}"
            )
            results.append(FeatureResult("MATERIAL", material_best_label, status, material_best_score))

        # --- PRINT ---
        print_best_label = max(print_targets, key=lambda l: scores.get(l, 0.0))
        print_best_score = scores.get(print_best_label, 0.0)
        print_delta = print_best_score - max_confuser

        print_confirmed = (
            print_best_score > 0.016
            and print_delta > 0.003
            and print_best_score > (max_neg_print + 0.003)
        )

        # Extra guard: avoid print hallucination on plain shirts
        plain_score = max(scores.get("plain blank t-shirt", 0.0), scores.get("plain shirt", 0.0))
        if plain_score > (print_best_score * 0.95) and plain_score > 0.02:
            print_confirmed = False

        if print_confirmed:
            context["has_print"] = True
            context["print_type"] = print_best_label

            if print_best_score > 0.06:
                status = "SICHER"
            elif print_best_score > 0.035:
                status = "WAHRSCHEINLICH"
            else:
                status = "HINWEIS"

            logger.info(
                f"Print-Precision: Score={print_best_score:.4f}, Confuser={max_confuser:.4f}, Delta={print_delta:.4f}, "
                f"Neg={max_neg_print:.4f}, Plain={plain_score:.4f}, Label={print_best_label}"
            )
            results.append(FeatureResult("PRINT", print_best_label, status, print_best_score))

        return results
