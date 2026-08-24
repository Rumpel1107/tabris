import subprocess
from unittest.mock import patch

from core.version import describe


def _answered_with(text):
    return subprocess.CompletedProcess(args=[], returncode=0, stdout=text, stderr="")


def test_reports_the_tag_the_checkout_is_on():
    with patch("core.version.subprocess.run", return_value=_answered_with("v0.1.6\n")):
        assert describe("/deployment") == "v0.1.6"


def test_reports_unknown_when_git_cannot_answer():
    with patch("core.version.subprocess.run", side_effect=FileNotFoundError):
        assert describe("/deployment") == "unknown"


def test_reports_unknown_when_git_answers_with_nothing():
    with patch("core.version.subprocess.run", return_value=_answered_with("\n")):
        assert describe("/deployment") == "unknown"


def test_asks_git_about_the_directory_it_was_given():
    with patch("core.version.subprocess.run", return_value=_answered_with("v0.1.6\n")) as run:
        describe("/deployment")
    assert "/deployment" in run.call_args.args[0]
