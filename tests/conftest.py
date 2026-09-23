import pytest
from unittest.mock import patch


def pytest_configure(config):
    config.addinivalue_line("markers", "real_verdict: the test exercises the freshness classifier itself")


@pytest.fixture(autouse=True)
def stable_verdict(request):
    """Every turn classifies as stable unless the test opts into the real classifier (item 35j)."""
    if request.node.get_closest_marker("real_verdict"):
        yield
        return
    with patch("core.freshness.classify", new=lambda user_input: "stable"):
        yield
