from text_utils import normalize_heading


def test_normalize_heading_trims_and_title_cases_words():
    assert normalize_heading("  janus worker proof of concept  ") == "Janus Worker Proof Of Concept"
