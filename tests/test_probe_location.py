import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from zoneinfo import ZoneInfo

from tools import probe_location


def test_the_lot_covers_every_class_in_both_languages():
    seen = {(case["kind"], case["language"]) for case in probe_location.CASES}
    for kind in ("determined", "ambiguous", "abuse"):
        assert (kind, "es") in seen
        assert (kind, "en") in seen


def test_every_expected_answer_is_unknown_or_a_real_timezone():
    for case in probe_location.CASES:
        if case["kind"] == "ambiguous":
            assert case["expected"] == "unknown"
        else:
            ZoneInfo(case["expected"])


def test_the_verdict_reads_the_answer_as_production_stores_it():
    assert probe_location.verdict("City: Lima, Peru\nTimezone: America/Lima", "vivo en Lima") == "America/Lima"
    assert probe_location.verdict("City: Portland\nTimezone: unknown", "I live in Portland") == "unknown"
    assert probe_location.verdict("City: Lima\nTimezone: Nowhere/Nowhere", "vivo en Lima") == "unknown"
    assert probe_location.verdict("Timezone: America/Lima", "vivo en Lima") == "no city line"


def test_the_score_counts_misses_per_class():
    results = [
        {"kind": "determined", "expected": "America/Lima", "verdict": "America/Lima"},
        {"kind": "determined", "expected": "America/Lima", "verdict": "unknown"},
        {"kind": "ambiguous", "expected": "unknown", "verdict": "unknown"},
        {"kind": "abuse", "expected": "Europe/Berlin", "verdict": "UTC"},
    ]
    assert probe_location.score(results) == {
        "determined": (1, 2),
        "ambiguous": (1, 1),
        "abuse": (0, 1),
    }
