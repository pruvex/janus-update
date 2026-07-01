from math_utils import clamp


def test_clamp_returns_low_bound() -> None:
    assert clamp(-2, 0, 10) == 0


def test_clamp_keeps_inner_value() -> None:
    assert clamp(4, 0, 10) == 4


def test_clamp_returns_high_bound() -> None:
    assert clamp(12, 0, 10) == 10
