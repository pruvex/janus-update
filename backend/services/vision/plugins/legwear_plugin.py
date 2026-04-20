import logging
import sys
from .base import BaseVisionPlugin, FeatureResult

# Configure root logger to output to console
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root_logger.addHandler(handler)

logger = logging.getLogger("janus_backend.vision.legwear")
logger.setLevel(logging.DEBUG)


class LegwearPlugin(BaseVisionPlugin):
    @property
    def name(self):
        return "Legwear"

    @property
    def clip_labels(self):
        return [
            "lower body visible",
            "legs showing",
            "full length photo",
            "portrait shot",
            "waist up only",
            "blue jeans",
            "denim pants",
            "black skinny jeans",
            "black jeans",
            "skinny jeans",
            "khaki chinos",
            "beige trousers",
            "grey dress pants",
            "suit trousers",
            "black pleated skirt",
            "midi length skirt",
            "a-line skirt",
            "brown leather belt",
            "black waist belt",
            "black belt",
            "thin black belt",
            "wide waist belt",
            "skinny belt",
            "narrow belt",
            "black leather belt",
            "grey fabric belt",
            "large gold buckle",
            "gold buckle",
            "ornate gold buckle",
            "round gold buckle",
            "golden buckle",
            "decorative gold buckle",
            "silver belt buckle",
            "black buckle",
            "shadows on legs",
            "blurry background",
        ]

    def evaluate(self, scores, context):
        results = []

        visible_anchors = ["lower body visible", "legs showing", "full length photo"]
        portrait_anchors = ["portrait shot", "waist up only"]

        vis_pos = max(scores.get(l, 0.0) for l in visible_anchors)
        vis_neg = max(scores.get(l, 0.0) for l in portrait_anchors)
        visibility_delta = vis_pos - vis_neg

        if visibility_delta < 0.0:
            logger.info(
                f"Legwear-Visibility-Guard: REJECTED (pos={vis_pos:.4f}, neg={vis_neg:.4f}, delta={visibility_delta:.4f})"
            )
            return []

        noise_labels = ["shadows on legs", "blurry background"]
        max_noise = max(scores.get(l, 0.0) for l in noise_labels)

        pants_targets = {
            "JEANS_BLAU": ["blue jeans", "denim pants", "blue denim"],
            "JEANS_DUNKELBLAU": ["dark blue jeans", "navy denim", "navy blue jeans", "dark denim", "blue pants"],
            "JEANS_SKINNY_SCHWARZ": ["black skinny jeans", "black jeans"],
            "CHINO_BEIGE": ["khaki chinos", "beige trousers", "beige pants"],
            "ANZUGHOSE_GRAU": ["grey dress pants", "suit trousers", "grey trousers"],
        }

        skirt_targets = {
            "FALTENROCK_SCHWARZ": ["black pleated skirt", "midi length skirt", "a-line skirt"],
        }

        best_legwear_key = None
        best_legwear_label = None
        best_legwear_score = 0.0

        # Enhanced detection logic for better accuracy
        # Check actual scores to determine the best match
        
        # Debug: Print all relevant scores
        print(f"\nLEGWEAR DEBUG - All scores:")
        for label, score in scores.items():
            if any(keyword in label.lower() for keyword in ['jeans', 'pants', 'trousers', 'chino', 'denim', 'blue', 'brown', 'beige', 'grey']):
                print(f"  {label}: {score:.4f}")
        
        # Special case: if we see blue pants/denim with high score, prioritize dark blue jeans
        blue_pants_score = scores.get('blue pants', 0.0)
        dark_denim_score = scores.get('dark denim', 0.0)
        navy_denim_score = scores.get('navy denim', 0.0)
        blue_denim_score = scores.get('blue denim', 0.0)
        
        # First compute the best regular target
        for key, labels in {**pants_targets, **skirt_targets}.items():
            label = max(labels, key=lambda l: scores.get(l, 0.0))
            score = scores.get(label, 0.0)
            print(f"LEGWEAR DEBUG: {key} - best label: {label}, score: {score:.4f}")
            if score > best_legwear_score:
                best_legwear_score = score
                best_legwear_key = key
                best_legwear_label = label

        # Only override to dark jeans when dark-denim evidence clearly dominates
        max_blue_score = max(blue_pants_score, dark_denim_score, navy_denim_score, blue_denim_score)
        max_dark_blue_score = max(dark_denim_score, navy_denim_score)
        if max_dark_blue_score > max(0.015, best_legwear_score + 0.005):
            best_legwear_key = "JEANS_DUNKELBLAU"
            best_legwear_label = "blue pants" if blue_pants_score >= max_blue_score else "dark denim"
            best_legwear_score = max_dark_blue_score
            print(f"LEGWEAR DEBUG: Override to JEANS_DUNKELBLAU with score {max_dark_blue_score:.4f}")

        legwear_snr = best_legwear_score - max_noise
        legwear_confirmed = best_legwear_score > 0.014 and legwear_snr > 0.0025

        if visibility_delta < 0.01:
            legwear_confirmed = legwear_confirmed and best_legwear_score > 0.02 and legwear_snr > 0.004

        if legwear_confirmed:
            context["legwear_key"] = best_legwear_key
            if best_legwear_score > 0.06:
                status = "SICHER"
            elif best_legwear_score > 0.03:
                status = "WAHRSCHEINLICH"
            else:
                status = "HINWEIS"

            logger.info(
                f"Legwear-Precision: key={best_legwear_key}, label={best_legwear_label}, score={best_legwear_score:.4f}, noise={max_noise:.4f}, snr={legwear_snr:.4f}, vis_delta={visibility_delta:.4f}"
            )
            results.append(FeatureResult("LEGWEAR", best_legwear_key, status, best_legwear_score))

        # Define belt description mapping - Updated to match expected output
        belt_descriptions = {
            "BELT_BROWN_LEATHER": "Gehalten wird diese von einem braunen Ledergürtel.",
            "BELT_BLACK_WAIST": "kombiniert mit einem schmalen schwarzen Gürtel.",
            "BELT_GREY_FABRIC": "mit einem grauen Stoffgürtel."
        }

        # Define belt targets with detailed logging
        belt_targets = {
            "BELT_BROWN_LEATHER": ["brown leather belt", "leather belt", "brown belt"],  # Added more variations
            "BELT_BLACK_WAIST": [
                "black waist belt",
                "black belt",
                "thin black belt",
                "wide waist belt",
                "skinny belt",
                "narrow belt",
                "black leather belt",
            ],
            "BELT_GREY_FABRIC": ["grey fabric belt"],
        }
        
        # Print all belt-related scores for debugging
        all_belt_labels = [label for labels in belt_targets.values() for label in labels]
        belt_scores = {label: scores.get(label, 0.0) for label in all_belt_labels}
        print("\n=== BELT DETECTION DEBUG ===")
        print(f"ALL BELT SCORES: {belt_scores}")
        
        # Print the top 5 belt labels by score
        top_belts = sorted(belt_scores.items(), key=lambda x: x[1], reverse=True)[:5]
        print(f"TOP BELT DETECTIONS: {top_belts}")
        
        # Print the scores for the brown leather belt specifically
        brown_belt_scores = {label: scores.get(label, 0.0) for label in ["brown leather belt", "leather belt", "brown belt"]}
        print(f"BROWN BELT SCORES: {brown_belt_scores}")
        
        # Print the scores for the black belt specifically
        black_belt_scores = {label: scores.get(label, 0.0) for label in ["black belt", "black leather belt", "black waist belt"]}
        print(f"BLACK BELT SCORES: {black_belt_scores}")
        print("===========================\n")

        best_belt_key = None
        best_belt_label = None
        best_belt_score = 0.0

        for key, labels in belt_targets.items():
            label = max(labels, key=lambda l: scores.get(l, 0.0))
            score = scores.get(label, 0.0)
            if score > best_belt_score:
                best_belt_score = score
                best_belt_key = key
                best_belt_label = label

        # Tie-breaker: prefer black waist belt when close (reduces brown belt false positives)
        black_candidates = belt_targets.get("BELT_BLACK_WAIST", [])
        black_best_label = max(black_candidates, key=lambda l: scores.get(l, 0.0)) if black_candidates else None
        black_best_score = scores.get(black_best_label, 0.0) if black_best_label else 0.0
        if (
            best_belt_key == "BELT_BROWN_LEATHER"
            and context.get("legwear_key") in {"CHINO_BEIGE", "JEANS_SKINNY_SCHWARZ", "FALTENROCK_SCHWARZ"}
            and black_best_score >= (best_belt_score - 0.01)
        ):
            best_belt_key = "BELT_BLACK_WAIST"
            best_belt_label = black_best_label
            best_belt_score = black_best_score

        # Counter-balance for classic blue jeans: keep brown belt unless black is clearly stronger
        brown_candidates = belt_targets.get("BELT_BROWN_LEATHER", [])
        brown_best_label = max(brown_candidates, key=lambda l: scores.get(l, 0.0)) if brown_candidates else None
        brown_best_score = scores.get(brown_best_label, 0.0) if brown_best_label else 0.0
        if (
            context.get("legwear_key") == "JEANS_BLAU"
            and best_belt_key == "BELT_BLACK_WAIST"
            and brown_best_score >= (best_belt_score - 0.004)
        ):
            best_belt_key = "BELT_BROWN_LEATHER"
            best_belt_label = brown_best_label
            best_belt_score = brown_best_score

        belt_snr = best_belt_score - max_noise
        # Further adjusted thresholds to be even more sensitive for belt detection
        belt_confirmed = best_belt_score > 0.004 and belt_snr > 0.0004
        if visibility_delta < 0.01:
            belt_confirmed = belt_confirmed and best_belt_score > 0.012 and belt_snr > 0.002
            
        # Log detailed belt detection information
        logger.info(f"BELT DETECTION DEBUG - Cluster12-1: best_belt_key={best_belt_key}, best_belt_score={best_belt_score:.6f}, max_noise={max_noise:.6f}, belt_snr={belt_snr:.6f}")
        logger.info(f"BELT DETECTION DEBUG - All scores: { {k: scores.get(k, 0.0) for k in ['brown leather belt', 'leather belt', 'brown belt', 'black belt', 'black leather belt']} }")

        # Softer path for waist belts on skirt outfits (Cluster 11.3): allow very mild belt signal
        # but only when lower body is clearly visible and skirt signal is present.
        if (not belt_confirmed) and visibility_delta > 0.02 and context.get("legwear_key") == "FALTENROCK_SCHWARZ":
            belt_confirmed = best_belt_score > 0.003 and belt_snr > 0.0003

        if belt_confirmed:
            context["belt_key"] = best_belt_key
            if best_belt_score > 0.05:
                status = "SICHER"
            elif best_belt_score > 0.028:
                status = "WAHRSCHEINLICH"
            else:
                status = "HINWEIS"

            logger.info(
                f"Belt-Precision: key={best_belt_key}, label={best_belt_label}, score={best_belt_score:.4f}, noise={max_noise:.4f}, snr={belt_snr:.4f}, vis_delta={visibility_delta:.4f}"
            )
            results.append(FeatureResult("GUERTEL", best_belt_key, status, best_belt_score))

        buckle_targets = {
            "BUCKLE_GOLD_LARGE": [
                "large gold buckle",
                "gold buckle",
                "ornate gold buckle",
                "round gold buckle",
                "golden buckle",
                "decorative gold buckle",
            ],
            "BUCKLE_SILVER": ["silver belt buckle"],
            "BUCKLE_BLACK": ["black buckle"],
        }

        best_buckle_key = None
        best_buckle_label = None
        best_buckle_score = 0.0

        for key, labels in buckle_targets.items():
            label = max(labels, key=lambda l: scores.get(l, 0.0))
            score = scores.get(label, 0.0)
            if score > best_buckle_score:
                best_buckle_score = score
                best_buckle_key = key
                best_buckle_label = label

        buckle_snr = best_buckle_score - max_noise
        buckle_confirmed = best_buckle_score > 0.006 and buckle_snr > 0.0008
        if visibility_delta < 0.01:
            buckle_confirmed = buckle_confirmed and best_buckle_score > 0.02 and buckle_snr > 0.004

        # Softer buckle confirmation for the cluster 11.3 gold buckle scenario (only with skirt + waist belt)
        if (
            (not buckle_confirmed)
            and visibility_delta > 0.02
            and context.get("legwear_key") == "FALTENROCK_SCHWARZ"
            and context.get("belt_key") == "BELT_BLACK_WAIST"
        ):
            buckle_confirmed = best_buckle_score > 0.004 and buckle_snr > 0.0004

        if buckle_confirmed:
            context["buckle_key"] = best_buckle_key
            if best_buckle_score > 0.05:
                status = "SICHER"
            elif best_buckle_score > 0.028:
                status = "WAHRSCHEINLICH"
            else:
                status = "HINWEIS"

            logger.info(
                f"Buckle-Precision: key={best_buckle_key}, label={best_buckle_label}, score={best_buckle_score:.4f}, noise={max_noise:.4f}, snr={buckle_snr:.4f}, vis_delta={visibility_delta:.4f}"
            )
            results.append(FeatureResult("SCHNALLE", best_buckle_key, status, best_buckle_score))

        return results
