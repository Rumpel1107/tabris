import config
import os
import pytest
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.admin import main


def test_export_command_exports_the_given_user(capsys):
    with patch("tools.admin.export_user", return_value="/somewhere/user-3-Ana.json") as export:
        main(["export", "3"])

    export.assert_called_once_with(config.DB_PATH, 3)
    assert "user-3-Ana.json" in capsys.readouterr().out


def _sample_records():
    return {
        "user": {"name": "Ana", "location": "Panama"},
        "channels": ["discord"],
        "facts": [{"content": "likes tea"}],
        "messages": [{"content": "hola"}],
    }


def test_deactivate_command_confirms_and_deactivates(capsys):
    with patch("tools.admin.get_user_records", return_value=_sample_records()), \
         patch("builtins.input", return_value="Ana"), \
         patch("tools.admin.deactivate_account", return_value="/somewhere/user-3-Ana.json") as deactivate:
        main(["deactivate", "3"])

    deactivate.assert_called_once_with(config.DB_PATH, 3)
    out = capsys.readouterr().out
    assert "Ana" in out
    assert "user-3-Ana.json" in out


def test_deactivate_command_aborts_on_mismatched_confirmation(capsys):
    with patch("tools.admin.get_user_records", return_value=_sample_records()), \
         patch("builtins.input", return_value="wrong name"), \
         patch("tools.admin.deactivate_account") as deactivate:
        main(["deactivate", "3"])

    deactivate.assert_not_called()


def test_reactivate_command_shows_who_it_targets_and_restores(capsys):
    with patch("tools.admin.get_user_records", return_value=_sample_records()), \
         patch("builtins.input", return_value="Ana"), \
         patch("tools.admin.reactivate_account", return_value=["/somewhere/user-3-Ana.json"]) as reactivate:
        main(["reactivate", "3"])

    reactivate.assert_called_once_with(config.DB_PATH, 3)
    out = capsys.readouterr().out
    assert "3" in out
    assert "Ana" in out
    assert "Panama" in out
    assert "user-3-Ana.json" in out


def test_reactivate_command_reports_when_there_was_no_export_left(capsys):
    with patch("tools.admin.get_user_records", return_value=_sample_records()), \
         patch("builtins.input", return_value="Ana"), \
         patch("tools.admin.reactivate_account", return_value=[]):
        main(["reactivate", "3"])

    assert "no export" in capsys.readouterr().out.lower()


def test_reactivate_command_aborts_on_mismatched_confirmation(capsys):
    with patch("tools.admin.get_user_records", return_value=_sample_records()), \
         patch("builtins.input", return_value="wrong name"), \
         patch("tools.admin.reactivate_account") as reactivate:
        main(["reactivate", "3"])

    reactivate.assert_not_called()


def test_purge_auto_erases_the_due_accounts_without_asking(capsys):
    with patch("tools.admin.purge_due_accounts", return_value=[3, 5]) as purge, \
         patch("builtins.input") as ask:
        main(["purge-auto"])

    purge.assert_called_once_with(config.DB_PATH)
    ask.assert_not_called()
    assert "3" in capsys.readouterr().out


@pytest.mark.parametrize("argv, skipped", [
    (["purge-force", "3"], False),
    (["purge-force", "3", "--skip-grace"], True),
])
def test_purge_force_confirms_and_erases_one_account(argv, skipped):
    with patch("tools.admin.get_user_records", return_value=_sample_records()), \
         patch("builtins.input", return_value="Ana"), \
         patch("tools.admin.purge_account") as purge:
        main(argv)

    purge.assert_called_once_with(config.DB_PATH, 3, ignore_deadline=skipped)


def test_purge_force_aborts_on_mismatched_confirmation():
    with patch("tools.admin.get_user_records", return_value=_sample_records()), \
         patch("builtins.input", return_value="wrong name"), \
         patch("tools.admin.purge_account") as purge:
        main(["purge-force", "3"])

    purge.assert_not_called()


def test_purge_force_reports_a_refusal_instead_of_crashing(capsys):
    refusal = ValueError("User 3 is still inside their grace window, until 2026-09-01")
    with patch("tools.admin.get_user_records", return_value=_sample_records()), \
         patch("builtins.input", return_value="Ana"), \
         patch("tools.admin.purge_account", side_effect=refusal):
        main(["purge-force", "3"])

    assert "grace window" in capsys.readouterr().out
