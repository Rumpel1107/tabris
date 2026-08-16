import config
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.admin import main


def test_export_command_exports_the_given_user(capsys):
    with patch("tools.admin.export_user", return_value="/somewhere/user-3-Ana.json") as export:
        main(["export", "3"])

    export.assert_called_once_with(config.DB_PATH, 3)
    assert "user-3-Ana.json" in capsys.readouterr().out
