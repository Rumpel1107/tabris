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
