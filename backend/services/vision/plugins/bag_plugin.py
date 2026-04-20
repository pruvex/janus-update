import logging
from .base import BaseVisionPlugin, FeatureResult

logger = logging.getLogger("janus_backend")


class BagPlugin(BaseVisionPlugin):
    @property
    def name(self):
        return "Bag"

    @property
    def clip_labels(self):
        return [
            # Targets
            "gold clutch bag",
            "golden evening bag",
            "small handbag",
            "black leather shoulder bag",
            "black handbag with a strap",
            "black fanny pack",
            "crossbody bag",
            "belt bag worn on chest",
            "bum bag",
            # Confusers
            "holding a book",
            "dark clothing fold",
            "backpack strap",
            "camera bag",
            "shadow on clothing",
            # Negatives
            "no bag",
            "empty hands",
            "unobstructed torso",
            "no accessories",
        ]

    def evaluate(self, scores, context):
        clutch_targets = [
            "gold clutch bag",
            "golden evening bag",
            "small handbag",
        ]
        shoulder_targets = [
            "black leather shoulder bag",
            "black handbag with a strap",
        ]
        fanny_targets = [
            "black fanny pack",
            "crossbody bag",
            "belt bag worn on chest",
            "bum bag",
        ]

        bag_confusers = [
            "holding a book",
            "dark clothing fold",
            "backpack strap",
            "camera bag",
            "shadow on clothing",
        ]
        bag_negatives = [
            "no bag",
            "empty hands",
            "unobstructed torso",
            "no accessories",
        ]

        max_clutch_score = max([scores.get(l, 0.0) for l in clutch_targets])
        max_shoulder_score = max([scores.get(l, 0.0) for l in shoulder_targets])
        max_fanny_score = max([scores.get(l, 0.0) for l in fanny_targets])

        max_confuser_score = max([scores.get(l, 0.0) for l in bag_confusers])
        max_negative_score = max([scores.get(l, 0.0) for l in bag_negatives])

        type_scores = {
            "clutch": max_clutch_score,
            "shoulder": max_shoulder_score,
            "fanny": max_fanny_score,
        }
        best_type = max(type_scores, key=type_scores.get)
        best_type_score = type_scores[best_type]

        if best_type == "clutch":
            best_label = max(clutch_targets, key=lambda l: scores.get(l, 0.0))
        elif best_type == "shoulder":
            best_label = max(shoulder_targets, key=lambda l: scores.get(l, 0.0))
        else:
            best_label = max(fanny_targets, key=lambda l: scores.get(l, 0.0))
        best_score = scores.get(best_label, 0.0)

        delta = best_score - max_confuser_score

        bag_confirmed = best_score > 0.012 and delta > 0.0025 and max_negative_score < 0.35
        if best_type == "clutch":
            bag_confirmed = best_score > 0.010 and delta > 0.002
        elif best_type == "fanny":
            bag_confirmed = (
                (best_score > 0.012 and delta > 0.0025 and max_negative_score < 0.35)
                or (best_score > 0.06 and best_score > (max_negative_score + 0.02))
            )

        if bag_confirmed or best_score > 0.008:
            logger.info(
                f"Bag-Precision: Type={best_type}, Bag={best_score:.4f}, Confuser={max_confuser_score:.4f}, "
                f"Delta={delta:.4f}, Negative={max_negative_score:.4f}, Label={best_label}"
            )

        if not bag_confirmed:
            return []

        if best_score > 0.04:
            status = "SICHER"
        elif best_score > 0.02:
            status = "WAHRSCHEINLICH"
        else:
            status = "HINWEIS"

        return [FeatureResult("TASCHE", best_label, status, best_score)]
