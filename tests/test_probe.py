import httpx
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools import probe


def test_a_reachable_endpoint_is_logged_and_reports_success(caplog):
    with patch("tools.probe.httpx.get") as get:
        get.return_value = httpx.Response(200, request=httpx.Request("GET", "https://example.test"))
        with caplog.at_level("INFO", logger="tools.probe"):
            assert probe.main([]) == 0
    assert "reachable" in caplog.text
    assert caplog.records[-1].levelname == "INFO"


def test_an_unreachable_endpoint_reports_failure_as_a_warning(caplog):
    with patch("tools.probe.httpx.get", side_effect=httpx.ConnectError("no route")):
        with caplog.at_level("INFO", logger="tools.probe"):
            assert probe.main([]) == 1
    assert "unreachable" in caplog.text
    assert caplog.records[-1].levelname == "WARNING"


def test_an_error_status_counts_as_unreachable(caplog):
    with patch("tools.probe.httpx.get") as get:
        get.return_value = httpx.Response(503, request=httpx.Request("GET", "https://example.test"))
        with caplog.at_level("INFO", logger="tools.probe"):
            assert probe.main([]) == 1
    assert caplog.records[-1].levelname == "WARNING"
