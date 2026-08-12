import pytest

from core.text import split_message


def test_short_text_stays_whole():
    assert split_message("hola", 2000) == ["hola"]


def test_cuts_at_the_last_line_break():
    assert split_message("primera línea\nsegunda línea", 20) == ["primera línea", "segunda línea"]


def test_cuts_at_the_last_space_when_there_is_no_line_break():
    assert split_message("uno dos tres cuatro", 12) == ["uno dos tres", "cuatro"]


def test_cuts_hard_when_there_is_no_separator():
    assert split_message("a" * 25, 10) == ["a" * 10, "a" * 10, "a" * 5]


@pytest.mark.parametrize("limit", [50, 200, 2000])
def test_no_piece_exceeds_the_limit(limit):
    text = "\n\n".join(f"Párrafo {n} con varias palabras dentro." * 20 for n in range(10))
    assert all(len(piece) <= limit for piece in split_message(text, limit))
