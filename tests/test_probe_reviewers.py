import os
import pytest
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools import probe_reviewers


def test_every_case_names_at_least_one_finding_with_its_defect():
    for case in probe_reviewers.CASES:
        assert case["findings"], case["commit"]
        assert all(f["defect"] and f["description"] for f in case["findings"])


def test_the_lot_carries_the_defect_the_probe_found():
    consolidation = next(c for c in probe_reviewers.CASES if c["commit"] == "3cc2a9e")
    assert {f["defect"] for f in consolidation["findings"]} >= {"DEF-1", "DEF-6", "DEF-12"}


@pytest.mark.parametrize("answer, named", [
    ("apply_memory_changes catches the IntegrityError and still deactivates the retired ids", ["DEF-12"]),
    ("The known facts are shown as [id] content, so the model writes the prefix back", ["DEF-1"]),
    ("Looks fine to me.", []),
])
def test_score_points_at_the_findings_an_answer_seems_to_name(answer, named):
    consolidation = next(c for c in probe_reviewers.CASES if c["commit"] == "3cc2a9e")
    assert probe_reviewers.score(answer, consolidation["findings"]) == named


def test_case_input_carries_the_diff_the_rules_of_that_day_and_the_changed_core_files():
    case_input = probe_reviewers.build_case_input("83b2fd2")
    assert "diff --git" in case_input["diff"]
    assert "# Contributing" in case_input["contract"]
    assert "--- core/memory_manager.py ---" in case_input["files"]
    assert ".md" not in case_input["diff"].split("diff --git")[1].splitlines()[0]
