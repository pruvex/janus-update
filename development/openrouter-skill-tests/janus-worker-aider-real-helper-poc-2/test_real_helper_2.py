from lean_backlog_prioritization_eval import validate


def test_validate_accepts_recommended_item_id_from_candidate_assessments():
    parsed = {
        "status": "PASS",
        "review_mode": "DELTA",
        "recommended_item_id": "BACKLOG-777",
        "recommended_title": "Synthetic candidate",
        "recommended_why": "Matches the strongest local candidate.",
        "full_review_recommended": "NO",
        "deep_reviewed_items": ["BACKLOG-777"],
        "compact_reviewed_items": [],
        "candidate_assessments": [
            {
                "backlog_id": "BACKLOG-777",
                "wichtigkeit": "HIGH",
                "umsetzungsrisiko": "LOW",
                "aufwand": "S",
                "umsetzungsreife": "READY",
                "empfehlung": "DO NOW",
                "rationale": "Bounded candidate from the provided set.",
            }
        ],
        "cache_update_suggestions": [],
        "notes": ["Looks consistent."],
    }

    issues = validate(parsed)

    assert "recommended_item_id invalid" not in issues


def test_validate_rejects_recommended_item_id_outside_candidate_assessments():
    parsed = {
        "status": "PASS",
        "review_mode": "DELTA",
        "recommended_item_id": "BACKLOG-999",
        "recommended_title": "Synthetic candidate",
        "recommended_why": "Claims to match the strongest local candidate.",
        "full_review_recommended": "NO",
        "deep_reviewed_items": ["BACKLOG-777"],
        "compact_reviewed_items": [],
        "candidate_assessments": [
            {
                "backlog_id": "BACKLOG-777",
                "wichtigkeit": "HIGH",
                "umsetzungsrisiko": "LOW",
                "aufwand": "S",
                "umsetzungsreife": "READY",
                "empfehlung": "DO NOW",
                "rationale": "Bounded candidate from the provided set.",
            }
        ],
        "cache_update_suggestions": [],
        "notes": ["Looks inconsistent."],
    }

    issues = validate(parsed)

    assert "recommended_item_id invalid" in issues
