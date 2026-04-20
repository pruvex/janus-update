import logging
from typing import Dict, List, Tuple

from .base import BaseVisionPlugin, FeatureResult

logger = logging.getLogger("janus_backend")


class PoseInteractionPlugin(BaseVisionPlugin):
    @property
    def name(self):
        return "PoseInteraction"

    @property
    def clip_labels(self):
        labels: List[str] = []
        for pose in self.pose_definitions.values():
            labels.extend(pose["targets"])
            labels.extend(pose["anchors"])
        labels.extend(self.visibility_labels["positive"])
        labels.extend(self.visibility_labels["negative"])
        return list(dict.fromkeys(labels))

    def __init__(self):
        self.visibility_labels = {
            "positive": [
                "full body photo",
                "upper body with hands visible",
                "person sitting in a chair",
                "person standing indoors",
            ],
            "negative": [
                "tight face portrait",
                "headshot only",
                "passport style photo",
                "close-up selfie",
            ],
        }

        self.pose_definitions: Dict[str, Dict[str, List[str]]] = {
            "POSE_ARMS_CROSSED": {
                "targets": ["arms crossed over chest"],
                "anchors": ["arms at side", "hands relaxed at sides"],
            },
            "POSE_HANDS_IN_POCKETS": {
                "targets": ["hands inside pockets", "both hands in pockets"],
                "anchors": ["hands visible", "hands outside pockets"],
            },
            "POSE_TYPING_LAPTOP": {
                "targets": ["typing on laptop", "hands on laptop keyboard"],
                "anchors": ["holding laptop", "laptop closed in hands"],
            },
            "POSE_SMARTPHONE_GAZE": {
                "targets": ["looking down at phone", "holding smartphone with both hands"],
                "anchors": ["talking on phone", "phone at ear"],
            },
            "POSE_LEGS_CROSSED": {
                "targets": ["legs crossed at knee", "seated with crossed legs"],
                "anchors": ["legs straight", "standing posture"],
            },
            "POSE_HOLDING_CUP": {
                "targets": ["holding coffee cup with both hands", "hands wrapped around mug"],
                "anchors": ["drinking", "cup near mouth"],
            },
            "POSE_HOLDING_BAG_STRAP": {
                "targets": ["hand gripping bag strap", "holding shoulder bag strap"],
                "anchors": ["bag strap hanging loose", "hands away from bag strap"],
            },
            "POSE_LEANING_WALL": {
                "targets": ["leaning back against wall", "foot propped against wall"],
                "anchors": ["standing away from wall", "neutral standing posture"],
            },
            "POSE_HAND_ON_CHIN": {
                "targets": ["hand resting on chin", "thinking pose hand on chin"],
                "anchors": ["hands down", "hands away from face"],
            },
            "POSE_WALKING": {
                "targets": ["walking forward", "dynamic walking motion"],
                "anchors": ["standing still", "static pose"],
            },
        }

    def _calc_delta(self, scores: Dict[str, float], targets: List[str], anchors: List[str]) -> Tuple[float, float, float]:
        max_target = max(scores.get(label, 0.0) for label in targets) if targets else 0.0
        max_anchor = max(scores.get(label, 0.0) for label in anchors) if anchors else 0.0
        return max_target - max_anchor, max_target, max_anchor

    def evaluate(self, scores, context):
        visibility_delta, vis_pos, vis_neg = self._calc_delta(
            scores,
            self.visibility_labels["positive"],
            self.visibility_labels["negative"],
        )

        if visibility_delta <= 0.0:
            logger.info(
                "Pose-Visibility-Guard: REJECTED (pos=%.4f, neg=%.4f, delta=%.4f)",
                vis_pos,
                vis_neg,
                visibility_delta,
            )
            return []

        candidates = []
        for pose_key, pose in self.pose_definitions.items():
            delta, target_score, anchor_score = self._calc_delta(
                scores,
                pose["targets"],
                pose["anchors"],
            )

            if delta > 0.01:
                candidates.append((pose_key, delta, target_score, anchor_score))

        if not candidates:
            return []

        priority = [
            "POSE_HOLDING_BAG_STRAP",
            "POSE_LEANING_WALL",
            "POSE_TYPING_LAPTOP",
            "POSE_SMARTPHONE_GAZE",
            "POSE_HOLDING_CUP",
            "POSE_ARMS_CROSSED",
            "POSE_HANDS_IN_POCKETS",
            "POSE_HAND_ON_CHIN",
            "POSE_LEGS_CROSSED",
            "POSE_WALKING",
        ]
        priority_index = {key: idx for idx, key in enumerate(priority)}

        best_key, best_delta, target_score, anchor_score = sorted(
            candidates,
            key=lambda item: (-item[1], priority_index.get(item[0], 999)),
        )[0]

        logger.info(
            "Pose-Detected: key=%s target=%.4f anchor=%.4f delta=%.4f visibility_delta=%.4f",
            best_key,
            target_score,
            anchor_score,
            best_delta,
            visibility_delta,
        )

        return [FeatureResult("POSE", best_key, "SICHER", float(best_delta))]
