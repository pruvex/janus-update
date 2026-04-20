import logging
from .base import BaseVisionPlugin, FeatureResult

logger = logging.getLogger("janus_backend")


class BeardPlugin(BaseVisionPlugin):
    @property
    def name(self):
        return "Beard"

    @property
    def clip_labels(self):
        return [
            # Targets
            "handlebar moustache",
            "styled moustache",
            "curled moustache",
            "mutton chops",
            "sideburns",
            "friendly mutton chops",
            "stubble beard",
            "three-day beard",
            "heavy stubble",
            "shaved beard",
            # Confusers
            "shadow on face",
            "dirty face",
            "dimples",
            "strong jawline shadow",
            # Negatives
            "clean shaven",
            "smooth skin",
            "no facial hair",
            "bare chin",
        ]

    def evaluate(self, scores, context):
        results = []

        moustache_targets = ["handlebar moustache", "styled moustache", "curled moustache"]
        chops_targets = ["mutton chops", "sideburns", "friendly mutton chops"]
        stubble_targets = ["stubble beard", "three-day beard", "heavy stubble"]
        other_targets = ["shaved beard"]

        confusers = ["shadow on face", "dirty face", "dimples", "strong jawline shadow"]
        negatives = ["clean shaven", "smooth skin", "no facial hair", "bare chin"]

        max_moustache = max(scores.get(l, 0.0) for l in moustache_targets)
        max_chops = max(scores.get(l, 0.0) for l in chops_targets)
        max_stubble = max(scores.get(l, 0.0) for l in stubble_targets)
        max_other = max(scores.get(l, 0.0) for l in other_targets)

        type_scores = {
            "moustache": max_moustache,
            "chops": max_chops,
            "stubble": max_stubble,
            "other": max_other,
        }
        best_type = max(type_scores, key=type_scores.get)

        if best_type == "moustache":
            target_labels = moustache_targets
        elif best_type == "chops":
            target_labels = chops_targets
        elif best_type == "stubble":
            target_labels = stubble_targets
        else:
            target_labels = other_targets

        best_label = max(target_labels, key=lambda l: scores.get(l, 0.0))
        best_score = scores.get(best_label, 0.0)

        max_confuser = max(scores.get(l, 0.0) for l in confusers)
        max_negative = max(scores.get(l, 0.0) for l in negatives)

        delta = best_score - max_confuser

        # Tie-break: compare chops vs stubble explicitly (muttonchops images can be misread as stubble)
        chops_best_label = max(chops_targets, key=lambda l: scores.get(l, 0.0))
        chops_score = scores.get(chops_best_label, 0.0)
        chops_delta = chops_score - max_confuser

        stubble_best_label = max(stubble_targets, key=lambda l: scores.get(l, 0.0))
        stubble_score = scores.get(stubble_best_label, 0.0)
        stubble_delta = stubble_score - max_confuser

        gender = str(context.get("gender", "")).lower()

        chops_candidate = chops_score > 0.003 and chops_score > (max_negative + 0.0005)
        if chops_candidate and gender == "man":
            # prefer chops if it is reasonably close to stubble or has better separation
            if chops_score >= stubble_score * 0.30 or chops_delta >= (stubble_delta - 0.0015):
                best_type = "chops"
                best_label = chops_best_label
                best_score = chops_score
                delta = chops_delta

        # Stronger male-only override for muttonchops/sideburns: accept even when stubble dominates,
        # as long as chops has a real (non-shadow) signal above negatives and confusers.
        if gender == "man" and best_type == "stubble":
            chops_override = chops_score > 0.002 and chops_delta > 0.0005 and chops_score > (max_negative + 0.0005)
            if chops_override:
                best_type = "chops"
                best_label = chops_best_label
                best_score = chops_score
                delta = chops_delta

        # Base thresholds
        confirmed = best_score > 0.012 and delta > 0.003 and best_score > (max_negative + 0.002)
        if best_type == "chops":
            confirmed = best_score > 0.010 and delta > 0.0025 and best_score > (max_negative + 0.0015)

        if not confirmed and gender == "man":
            # Softer confirmation path for men only (reduces risk of FP on women clusters)
            confirmed = best_score > 0.008 and delta > 0.0015 and best_score > (max_negative + 0.001)
            if best_type == "chops":
                confirmed = best_score > 0.006 and delta > 0.001 and best_score > (max_negative + 0.0005)

        # If negatives dominate, reject
        if max_negative > best_score and max_negative > 0.02:
            confirmed = False

        # Stricter rule in female context (false-positive protection)
        if gender == "woman" and best_score < 0.05:
            confirmed = False

        if confirmed or best_score > 0.005:
            logger.info(
                f"Beard-Precision: Type={best_type}, Beard={best_score:.4f}, Confuser={max_confuser:.4f}, "
                f"Delta={delta:.4f}, Negative={max_negative:.4f}, Label={best_label}"
            )

        if confirmed:
            context["has_beard"] = True
            context["beard_style"] = best_label

            if best_score > 0.05:
                status = "SICHER"
            elif best_score > 0.025:
                status = "WAHRSCHEINLICH"
            else:
                status = "HINWEIS"

            results.append(FeatureResult("BART_STIL", best_label, status, best_score))
        else:
            # Male-only low-signal fallback: set context so downstream mapping becomes deterministic
            # while keeping female false-positive protection intact.
            distinctive = any(k in best_label for k in ["handlebar", "curled", "mutton", "sideburn"])
            if gender == "man" and distinctive and best_score > 0.004 and best_score > (max_negative + 0.0005):
                context["has_beard"] = True
                context["beard_style"] = best_label
                results.append(FeatureResult("BART_STIL", best_label, "HINWEIS", best_score))
            # Preserve explicit non-beard signal if plugin sees strong clean-shaven
            clean_score = scores.get("clean shaven", 0.0)
            if clean_score > 0.03 and clean_score > best_score:
                context["has_beard"] = False
                context["beard_style"] = "clean shaven"

        return results
