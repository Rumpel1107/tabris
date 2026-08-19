import config
import importlib
import os
import pytest


@pytest.fixture
def reloaded_config(monkeypatch):
    def load(data_dir=None):
        if data_dir is None:
            monkeypatch.delenv("TABRIS_DATA_DIR", raising=False)
        else:
            monkeypatch.setenv("TABRIS_DATA_DIR", str(data_dir))
        return importlib.reload(config)

    yield load
    monkeypatch.delenv("TABRIS_DATA_DIR", raising=False)
    importlib.reload(config)


def test_data_paths_follow_the_environment(reloaded_config, tmp_path):
    loaded = reloaded_config(tmp_path)
    assert loaded.DB_PATH == os.path.join(str(tmp_path), "tabris.db")
    assert loaded.CLIENT_ID_PATH == os.path.join(str(tmp_path), "tabris_client_id")
    assert loaded.EXPORTS_DIR == os.path.join(str(tmp_path), "exports")


def test_data_paths_default_inside_the_project(reloaded_config):
    loaded = reloaded_config()
    assert loaded.DB_PATH == os.path.join(loaded.BASE_DIR, "data", "tabris.db")
