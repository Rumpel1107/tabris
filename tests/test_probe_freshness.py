import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools import probe_freshness


def test_the_lot_covers_every_class_in_both_languages():
    seen = {(case["kind"], case["language"]) for case in probe_freshness.CASES}
    for kind in ("fresh", "stable", "abuse", "rare"):
        assert (kind, "es") in seen
        assert (kind, "en") in seen


def test_abuse_and_rare_cases_carry_the_verdict_the_fence_needs():
    expected = {case["kind"]: case["expected"] for case in probe_freshness.CASES}
    assert expected["fresh"] == "fresh"
    assert expected["abuse"] == "fresh"
    assert expected["stable"] == "stable"
    assert expected["rare"] == "stable"


def test_the_score_counts_misses_per_class():
    results = [
        {"kind": "fresh", "expected": "fresh", "verdict": "fresh"},
        {"kind": "fresh", "expected": "fresh", "verdict": "stable"},
        {"kind": "abuse", "expected": "fresh", "verdict": "fresh"},
        {"kind": "stable", "expected": "stable", "verdict": None},
    ]
    assert probe_freshness.score(results) == {
        "fresh": (1, 2),
        "abuse": (1, 1),
        "stable": (0, 1),
    }
