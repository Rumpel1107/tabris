import re

from urllib.parse import urlsplit

_URL = re.compile(r"https?://[^\s<>\"')\]]+", re.IGNORECASE)
_ITEM = re.compile(r"^[ \t]*([-*•]|\d+[.)])\s", re.MULTILINE)
_BLANK_LINE = re.compile(r"\n[ \t]*\n")


def find_urls(text: str) -> set[str]:
    """Every http(s) address written in the text."""
    return set(_URL.findall(text))


def _normalize(url: str) -> str:
    """The same page written two ways compares equal: host case, a trailing slash and a fragment do not identify it."""
    parts = urlsplit(url.rstrip(".,;:!?"))
    query = f"?{parts.query}" if parts.query else ""
    return f"{parts.scheme.lower()}://{parts.netloc.lower()}{parts.path.rstrip('/')}{query}"


def _block_span(text: str, position: int) -> tuple[int, int]:
    """The list item or paragraph the character at `position` belongs to."""
    starts = [0] + [m.start() for m in _ITEM.finditer(text)] + [m.end() for m in _BLANK_LINE.finditer(text)]
    ends = [len(text)] + [m.start() for m in _ITEM.finditer(text)] + [m.start() for m in _BLANK_LINE.finditer(text)]
    return max(s for s in starts if s <= position), min(e for e in ends if e > position)


def drop_unverifiable_links(reply: str, allowed_urls: set[str]) -> tuple[str, int]:
    """Remove every block carrying a link that is in none of `allowed_urls`, and say how many went.

    The block goes whole, not just its link: the description around an invented address was
    invented with it, and that is the half that misleads (item 35b).
    """
    allowed = {_normalize(url) for url in allowed_urls}
    spans = [
        _block_span(reply, m.start())
        for m in _URL.finditer(reply)
        if _normalize(m.group()) not in allowed
    ]
    if not spans:
        return reply, 0
    merged: list[list[int]] = []
    for start, end in sorted(spans):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    kept, last = "", 0
    for start, end in merged:
        kept += reply[last:start]
        last = end
    kept += reply[last:]
    return re.sub(r"\n{3,}", "\n\n", kept).strip(), len(merged)


def split_message(text: str, limit: int) -> list[str]:
    """Split text into pieces of at most `limit` characters, cutting at a line break or a space when possible."""
    pieces = []
    remaining = text
    while len(remaining) > limit:
        window = remaining[:limit + 1]
        cut = window.rfind("\n")
        if cut == -1:
            cut = window.rfind(" ")
        if cut == -1:
            piece, remaining = remaining[:limit], remaining[limit:]
        else:
            piece, remaining = remaining[:cut], remaining[cut + 1:]
        piece = piece.strip()
        if piece:
            pieces.append(piece)
    remaining = remaining.strip()
    if remaining:
        pieces.append(remaining)
    return pieces
