from backend.tools import media_tools


def test_normalize_image_quality_maps_openai_standard_to_low():
    assert media_tools._normalize_image_quality("standard", "openai") == "low"


def test_force_quality_for_gpt_image_1_5_always_low_for_openai():
    assert media_tools._force_quality_for_model("gpt-image-1.5", "openai", "high") == "low"
    assert media_tools._force_quality_for_model("gpt-image-1.5", "openai", "low") == "low"
    assert media_tools._force_quality_for_model("dall-e-3", "openai", "high") == "high"
