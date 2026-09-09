import pytest

from core.text import drop_unverifiable_links, split_message


def test_short_text_stays_whole():
    assert split_message("hola", 2000) == ["hola"]


def test_cuts_at_the_last_line_break():
    assert split_message("primera línea\nsegunda línea", 20) == ["primera línea", "segunda línea"]


def test_cuts_at_the_last_space_when_there_is_no_line_break():
    assert split_message("uno dos tres cuatro", 12) == ["uno dos tres", "cuatro"]


def test_cuts_hard_when_there_is_no_separator():
    assert split_message("a" * 25, 10) == ["a" * 10, "a" * 10, "a" * 5]


READ = "https://example.com/uno"
INVENTED = "https://news.ycombinator.com/item?id="


@pytest.mark.parametrize("reply, gone", [
    # a bullet list, the shape a reply full of sources actually takes
    (f"Aquí tienes dos:\n\n- Lo que sí leí {READ}\n- Lo que no {INVENTED}\n", "Lo que no"),
    # a numbered list
    (f"Here are two:\n\n1. What I read {READ}\n2. What I did not {INVENTED}\n", "What I did not"),
    # loose paragraphs: the whole paragraph goes, since a sentence has no reliable end
    (f"Un artículo real, en {READ}\n\nY este otro, en {INVENTED}, que describo de memoria.", "de memoria"),
])
def test_a_block_whose_link_cannot_be_traced_is_dropped_whole(reply, gone):
    cleaned, dropped = drop_unverifiable_links(reply, {READ})
    assert dropped == 1
    assert gone not in cleaned
    assert INVENTED not in cleaned
    assert READ in cleaned


@pytest.mark.parametrize("written", [
    "https://EXAMPLE.com/uno",      # the host is not case-sensitive
    "https://example.com/uno/",     # a trailing slash is the same page
    "https://example.com/uno#hoy",  # a fragment never reaches the server
])
def test_a_link_that_was_read_survives_being_written_differently(written):
    cleaned, dropped = drop_unverifiable_links(f"- Mira esto {written}", {READ})
    assert dropped == 0
    assert written in cleaned


def test_an_invented_variant_of_a_real_link_is_not_taken_for_it():
    # the case that started this: the shape of a real address with the part that identifies it missing
    real = "https://news.ycombinator.com/item?id=41293884"
    cleaned, dropped = drop_unverifiable_links(f"- Un artículo {INVENTED}", {real})
    assert dropped == 1
    assert cleaned.strip() == ""


def test_a_reply_without_links_is_returned_untouched():
    reply = "Son las 3 de la tarde en Bogotá."
    assert drop_unverifiable_links(reply, set()) == (reply, 0)


@pytest.mark.parametrize("limit", [50, 200, 2000])
def test_no_piece_exceeds_the_limit(limit):
    text = "\n\n".join(f"Párrafo {n} con varias palabras dentro." * 20 for n in range(10))
    assert all(len(piece) <= limit for piece in split_message(text, limit))
