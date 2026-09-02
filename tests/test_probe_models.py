import os
import pytest
import struct
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.providers import PROVIDER_CONFIG
from tools import probe_models


CATALOG_PAYLOAD = {
    "data": [
        {"id": "vendor/sees:free", "context_length": 128000,
         "architecture": {"input_modalities": ["text", "image"]}},
        {"id": "vendor/text-only", "context_length": 64000,
         "architecture": {"input_modalities": ["text"]}},
    ]
}


def test_the_catalog_says_which_models_accept_images():
    entries = probe_models.parse_catalog(CATALOG_PAYLOAD)
    assert {e["id"]: e["accepts_images"] for e in entries} == {
        "vendor/sees:free": True,
        "vendor/text-only": False,
    }


def test_a_catalog_that_does_not_state_modalities_says_so_instead_of_guessing():
    entries = probe_models.parse_catalog({"data": [{"id": "vendor/some-model"}]})
    assert [entry["accepts_images"] for entry in entries] == [None]


def test_every_configured_provider_is_probeable_without_a_second_list():
    for name, settings in PROVIDER_CONFIG.items():
        assert probe_models.catalog_url(name).startswith(settings["base_url"].rstrip("/"))


@pytest.mark.parametrize("message, expected", [
    ("Error code: 413 - Request too large ... tokens per minute (TPM): Limit 8000", "413"),
    ("Error code: 429 - rate-limited upstream", "429"),
    ("Error code: 404 - No endpoints found that support image input", "404"),
    ("Request timed out.", "timeout"),
    ("something nobody has seen before", "RuntimeError"),
])
def test_an_error_is_reported_by_what_it_was_not_by_its_class(message, expected):
    assert probe_models.classify_error(RuntimeError(message)) == expected


@pytest.mark.parametrize("answer, read", [
    ("7412", True),
    ("El número es 7412.", True),
    ("The number is 7412", True),
    ("No puedo leer la imagen", False),
    ("", False),
])
def test_a_reading_counts_only_when_the_code_is_in_the_answer(answer, read):
    assert probe_models.reads_code(answer, "7412") is read


def test_listing_a_catalog_reports_the_models_that_accept_images(capsys):
    with patch("tools.probe_models.fetch_catalog", return_value=probe_models.parse_catalog(CATALOG_PAYLOAD)):
        assert probe_models.main(["list", "openrouter", "--images-only"]) == 0
    printed = capsys.readouterr().out
    assert "vendor/sees:free" in printed
    assert "vendor/text-only" not in printed


def test_a_probe_carries_an_image_by_default():
    assert isinstance(probe_models.probe_messages(1_000)[-1]["content"], list)


def test_a_probe_can_carry_several_images_to_find_where_a_model_refuses():
    parts = probe_models.probe_messages(1_000, image_count=4)[-1]["content"]
    assert [part["type"] for part in parts] == ["text", "image_url", "image_url", "image_url", "image_url"]


@pytest.mark.parametrize("scale", [70, 3])
def test_the_probe_image_can_be_drawn_at_the_size_a_screenshot_would_use(scale):
    png = probe_models.make_image(scale=scale)
    assert png.startswith(b"\x89PNG\r\n\x1a\n")
    width, height = struct.unpack(">II", png[16:24])
    assert (width, height) == (probe_models.WIDTH, probe_models.HEIGHT)


def test_a_text_probe_sends_no_image_so_a_text_role_can_be_measured():
    content = probe_models.probe_messages(1_000, with_image=False)[-1]["content"]
    assert isinstance(content, str)
    assert probe_models.CODE in content


def test_the_grid_is_identical_every_run_so_models_face_the_same_input():
    first_png, first_codes = probe_models.make_grid()
    second_png, second_codes = probe_models.make_grid()
    assert first_codes == second_codes
    assert first_png == second_png


def test_the_grid_question_names_cells_without_ever_giving_the_answer():
    messages, expected = probe_models.build_probe(1_000, mode="grid")
    question = messages[-1]["content"][0]["text"]
    assert len(expected) == 3
    assert len(set(expected)) == 3
    for code in expected:
        assert code not in question


@pytest.mark.parametrize("mode", ["text", "image"])
def test_the_simple_probes_expect_the_one_code_they_drew(mode):
    _, expected = probe_models.build_probe(1_000, mode=mode)
    assert expected == [probe_models.CODE]


def test_probing_a_model_reports_how_long_it_took_and_whether_it_read(capsys):
    with patch("tools.probe_models.call_model", return_value=(1.5, "7412")):
        assert probe_models.main(["probe", "openrouter", "vendor/sees:free", "--rounds", "2"]) == 0
    printed = capsys.readouterr().out
    assert "vendor/sees:free" in printed
    assert "2/2" in printed


def test_a_model_that_never_answers_is_reported_without_crashing(capsys):
    with patch("tools.probe_models.call_model", side_effect=RuntimeError("Error code: 413 - too large")):
        assert probe_models.main(["probe", "groq", "vendor/nope", "--rounds", "2"]) == 1
    printed = capsys.readouterr().out
    assert "0/2" in printed
    assert "413" in printed
