"""House style: no em dashes anywhere Rigor renders, including model-written prose."""
from rigor.llm import strip_dashes


def test_em_dash_becomes_comma():
    out = strip_dashes("it tested three groups—not just control—and does not confirm")
    assert "—" not in out
    assert "three groups, not just control, and" in out


def test_en_dash_in_range_becomes_hyphen():
    assert strip_dashes("a 1–5 scale") == "a 1-5 scale"


def test_spaced_em_dash():
    assert "—" not in strip_dashes("spaced — dash")


def test_clean_text_untouched():
    s = "A clean sentence, with commas, and no dashes."
    assert strip_dashes(s) == s


def test_empty_is_safe():
    assert strip_dashes("") == ""
    assert strip_dashes(None) is None
