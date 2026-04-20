import logging
from typing import Any, Dict, List, Tuple

from .base import BaseVisionPlugin, FeatureResult

logger = logging.getLogger("janus_backend")


class EnvironmentPlugin(BaseVisionPlugin):
    @property
    def name(self) -> str:
        return "Environment"

    def __init__(self) -> None:
        self.visibility_labels = {
            "positive": [
                "outdoor scene",
                "wide shot with visible background",
                "person in contextual environment",
                "street scene",
                "interior environment visible",
            ],
            "negative": [
                "tight face portrait",
                "headshot only",
                "passport style photo",
                "close-up selfie",
                "face closeup crop",
            ],
        }

        self.environment_definitions: Dict[str, Dict[str, List[str]]] = {
            "ENV_URBAN_GOLDEN": {
                "targets": [
                    "golden hour in city",
                    "warm sunset street light",
                    "urban street at sunset",
                    "city golden hour",
                ],
                "anchors": ["overcast city street", "neon night city", "studio background"],
            },
            "ENV_URBAN_NEON_NIGHT": {
                "targets": [
                    "urban street at night with neon lights",
                    "city nightlife neon signs",
                    "neon reflections on wet asphalt",
                    "night city portrait",
                ],
                "anchors": ["golden hour city", "office daylight", "forest daylight"],
            },
            "ENV_BEACH_HARSH_NOON": {
                "targets": [
                    "bright beach at noon",
                    "harsh midday sunlight on sand",
                    "sunlit beach scene",
                    "person on beach under strong sun",
                ],
                "anchors": ["cloudy park", "studio lighting", "office interior"],
            },
            "ENV_OFFICE_COOL_DAYLIGHT": {
                "targets": [
                    "modern office with cool daylight",
                    "corporate office interior",
                    "desk workspace with laptop",
                    "bright office window light",
                ],
                "anchors": ["cafe warm light", "night neon street", "forest outdoors"],
            },
            "ENV_CAFE_WARM_DIM": {
                "targets": [
                    "cozy cafe interior warm lighting",
                    "coffee shop ambient light",
                    "indoor cafe with warm tones",
                    "person holding cup in cafe",
                ],
                "anchors": ["office daylight", "studio neutral backdrop", "urban rain street"],
            },
            "ENV_STUDIO_SOFT_NEUTRAL": {
                "targets": [
                    "neutral studio background",
                    "soft studio portrait lighting",
                    "controlled studio light",
                    "plain backdrop portrait",
                ],
                "anchors": ["busy street background", "forest scene", "cafe interior"],
            },
            "ENV_PARK_OVERCAST_DIFFUSE": {
                "targets": [
                    "green park under cloudy sky",
                    "diffuse daylight outdoors",
                    "overcast park scene",
                    "walking in park",
                ],
                "anchors": ["harsh noon beach", "night neon city", "studio background"],
            },
            "ENV_URBAN_RAIN_REFLECTION": {
                "targets": [
                    "rainy city street",
                    "wet pavement reflections",
                    "person with umbrella in city rain",
                    "faint rainy daylight",
                ],
                "anchors": ["sunny beach", "golden hour dry street", "office interior"],
            },
            "ENV_FOREST_SUNRAYS": {
                "targets": [
                    "forest with sun rays through leaves",
                    "woodland scene with dappled light",
                    "person near tree trunk",
                    "sunbeams in forest",
                ],
                "anchors": ["concrete architecture", "office interior", "night neon city"],
            },
            "ENV_CONCRETE_GEOMETRIC_SHADOWS": {
                "targets": [
                    "modern concrete architecture",
                    "geometric shadow patterns",
                    "hard architectural contrast",
                    "urban brutalist building",
                ],
                "anchors": ["forest foliage", "cafe warm interior", "studio neutral background"],
            },
        }

    @property
    def clip_labels(self) -> List[str]:
        labels: List[str] = []
        labels.extend(self.visibility_labels["positive"])
        labels.extend(self.visibility_labels["negative"])
        for env in self.environment_definitions.values():
            labels.extend(env["targets"])
            labels.extend(env["anchors"])
        return list(dict.fromkeys(labels))

    def _calc_delta(self, scores: Dict[str, float], targets: List[str], anchors: List[str]) -> Tuple[float, float, float]:
        max_target = max(scores.get(label, 0.0) for label in targets) if targets else 0.0
        max_anchor = max(scores.get(label, 0.0) for label in anchors) if anchors else 0.0
        return max_target - max_anchor, max_target, max_anchor

    def evaluate(self, scores: Dict[str, float], context: Dict[str, Any]) -> List[FeatureResult]:
        visibility_delta, vis_pos, vis_neg = self._calc_delta(
            scores,
            self.visibility_labels["positive"],
            self.visibility_labels["negative"],
        )

        if visibility_delta <= 0.01:
            logger.info(
                "Environment-Visibility-Guard: REJECTED (pos=%.4f, neg=%.4f, delta=%.4f)",
                vis_pos,
                vis_neg,
                visibility_delta,
            )
            return []

        candidates = []
        for env_key, env in self.environment_definitions.items():
            delta, target_score, anchor_score = self._calc_delta(scores, env["targets"], env["anchors"])
            if delta > 0.01:
                candidates.append((env_key, delta, target_score, anchor_score))

        if not candidates:
            return []

        priority = [
            "ENV_URBAN_RAIN_REFLECTION",
            "ENV_URBAN_NEON_NIGHT",
            "ENV_URBAN_GOLDEN",
            "ENV_BEACH_HARSH_NOON",
            "ENV_OFFICE_COOL_DAYLIGHT",
            "ENV_CAFE_WARM_DIM",
            "ENV_STUDIO_SOFT_NEUTRAL",
            "ENV_PARK_OVERCAST_DIFFUSE",
            "ENV_FOREST_SUNRAYS",
            "ENV_CONCRETE_GEOMETRIC_SHADOWS",
        ]
        priority_index = {key: idx for idx, key in enumerate(priority)}

        best_key, best_delta, target_score, anchor_score = sorted(
            candidates,
            key=lambda item: (-item[1], priority_index.get(item[0], 999)),
        )[0]

        logger.info(
            "Environment-Detected: key=%s target=%.4f anchor=%.4f delta=%.4f visibility_delta=%.4f",
            best_key,
            target_score,
            anchor_score,
            best_delta,
            visibility_delta,
        )

        return [FeatureResult("AMBIENTE", best_key, "SICHER", float(best_delta))]
