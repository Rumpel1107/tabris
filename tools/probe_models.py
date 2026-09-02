import argparse
import base64
import config
import httpx
import logging
import statistics
import struct
import sys
import time
import zlib

from core.providers import PROVIDER_CONFIG
from openai import OpenAI

logger = logging.getLogger(__name__)

CODE = "7412"
STATUS_CODES = ("400", "401", "403", "404", "413", "429", "500", "502", "503")

DIGITS = {
    "0": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11111", "00010", "00100", "00010", "00001", "10001", "01110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
}


def catalog_url(provider: str) -> str:
    """Every provider here speaks the OpenAI shape, so its catalog hangs off the base url already configured."""
    return PROVIDER_CONFIG[provider]["base_url"].rstrip("/") + "/models"


def parse_catalog(payload: dict) -> list[dict]:
    """Normalize a model list; accepts_images stays None when the catalog does not say."""
    entries = []
    for row in payload.get("data", []):
        modalities = (row.get("architecture") or {}).get("input_modalities")
        entries.append({
            "id": row["id"],
            "accepts_images": ("image" in modalities) if modalities else None,
            "context": row.get("context_length"),
        })
    return entries


def fetch_catalog(provider: str) -> list[dict]:
    """Ask the provider which models it has right now, rather than trusting documentation."""
    key = PROVIDER_CONFIG[provider]["api_key"]
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    response = httpx.get(catalog_url(provider), headers=headers, timeout=30)
    response.raise_for_status()
    return parse_catalog(response.json())


def classify_error(error: Exception) -> str:
    """Report a failure by the status the provider returned, not by the exception class it arrived in."""
    text = str(error)
    if "timed out" in text.lower():
        return "timeout"
    for status in STATUS_CODES:
        if f"code: {status}" in text or f"code={status}" in text:
            return status
    return type(error).__name__


def reads_code(answer: str, code: str) -> bool:
    """Whether the model actually read the number drawn in the probe image."""
    return code in (answer or "")


def make_image(code: str = CODE, width: int = 1920, height: int = 1080) -> bytes:
    """A screenshot-sized PNG with `code` drawn large, so a reading can be checked without a fixture file."""
    scale, gap = 70, 20
    rows = [[(245, 245, 245)] * width for _ in range(height)]
    glyph = 5 * scale + gap
    left = (width - (len(code) * glyph - gap)) // 2
    top = (height - 7 * scale) // 2
    for index, digit in enumerate(code):
        for row, bits in enumerate(DIGITS[digit]):
            for col, bit in enumerate(bits):
                if bit == "1":
                    for y in range(top + row * scale, top + (row + 1) * scale):
                        for x in range(left + index * glyph + col * scale,
                                       left + index * glyph + (col + 1) * scale):
                            rows[y][x] = (20, 20, 20)
    raw = bytearray()
    for row in rows:
        raw.append(0)
        for red, green, blue in row:
            raw += bytes((red, green, blue))

    def chunk(tag, payload):
        body = tag + payload
        return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body))

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(raw), 6))
        + chunk(b"IEND", b"")
    )


def probe_messages(history_chars: int, code: str = CODE, with_image: bool = True) -> list[dict]:
    """A call shaped like a real turn: a system prompt, a history of that many characters, and the code to read back."""
    filler = (
        "El servidor quedo configurado con fibra optica y el router conectado por cable. "
        "La velocidad medida ronda los 280 megabits frente a los 900 contratados. "
    )
    def text(size):
        return (filler * (size // len(filler) + 1))[:size]

    messages = [{"role": "system", "content": text(16_000)}]
    written = 0
    while written < history_chars:
        messages.append({"role": "user", "content": text(118)})
        messages.append({"role": "assistant", "content": text(931)})
        written += 1_049
    if not with_image:
        messages.append({"role": "user", "content": f"Repite exactamente este número y nada más: {code}"})
        return messages
    url = "data:image/png;base64," + base64.b64encode(make_image(code)).decode()
    messages.append({"role": "user", "content": [
        {"type": "text", "text": "¿Qué número de cuatro dígitos aparece en la imagen? Responde solo con el número."},
        {"type": "image_url", "image_url": {"url": url}},
    ]})
    return messages


def call_model(client, model: str, messages: list[dict]) -> tuple[float, str]:
    """Make one real call, returning how long it took and what came back."""
    started = time.monotonic()
    response = client.chat.completions.create(model=model, messages=messages, temperature=0.7)
    return time.monotonic() - started, (response.choices[0].message.content or "").strip()


def _client(provider: str):
    settings = PROVIDER_CONFIG[provider]
    return OpenAI(
        base_url=settings["base_url"],
        api_key=settings["api_key"] or "missing",
        timeout=90,
        max_retries=0,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ask a provider what it has, then find out what it will actually serve.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    listing = commands.add_parser("list", help="Enumerate the models a provider offers right now.")
    listing.add_argument("provider", choices=sorted(PROVIDER_CONFIG))
    listing.add_argument("--images-only", action="store_true", help="Only models the catalog says accept images")

    probing = commands.add_parser("probe", help="Call models with a turn-shaped payload and report what happened.")
    probing.add_argument("provider", choices=sorted(PROVIDER_CONFIG))
    probing.add_argument("models", nargs="+", help="Model ids as the provider spells them")
    probing.add_argument("--rounds", type=int, default=3, help="Calls per model (default 3)")
    probing.add_argument("--history", type=int, default=31_000,
                         help="Characters of conversation to send, as a real turn would (default 31000)")
    probing.add_argument("--no-image", action="store_true",
                         help="Probe a text-only role: the payload carries no image")
    return parser


def _list(args) -> int:
    entries = fetch_catalog(args.provider)
    if args.images_only:
        entries = [entry for entry in entries if entry["accepts_images"]]
    for entry in sorted(entries, key=lambda entry: entry["id"]):
        mark = {True: "image", False: "text ", None: "?    "}[entry["accepts_images"]]
        print(f"  {mark}  {entry['id']}")
    print(f"\n{len(entries)} models. A catalog says what exists, never whether it will serve you.")
    return 0


def _probe(args) -> int:
    client = _client(args.provider)
    messages = probe_messages(args.history, with_image=not args.no_image)
    carrying = "text only" if args.no_image else "plus one image"
    print(f"{args.rounds} rounds, {args.history:,} characters of history, {carrying}\n")
    print(f"{'model':<48} {'served':>7} {'read':>7} {'median':>8} {'worst':>8}  errors")
    dead = False
    for model in args.models:
        times, reads, errors = [], 0, []
        for _ in range(args.rounds):
            try:
                seconds, answer = call_model(client, model, messages)
            except Exception as error:
                errors.append(classify_error(error))
                continue
            times.append(seconds)
            reads += reads_code(answer, CODE)
        served = f"{len(times)}/{args.rounds}"
        if times:
            shape = f"{statistics.median(times):7.1f}s {max(times):7.1f}s"
        else:
            shape = f"{'-':>8} {'-':>8}"
            dead = True
        print(f"{model:<48} {served:>7} {reads:>4}/{len(times):<2} {shape}  {', '.join(sorted(set(errors))) or '-'}")
    return 1 if dead else 0


def main(argv=None) -> int:
    """Enumerate or probe, reporting an exit code so a model that never answers is visible to a script."""
    args = build_parser().parse_args(argv)
    if args.command == "list":
        return _list(args)
    return _probe(args)


if __name__ == "__main__":
    logging.basicConfig(
        level=config.LOG_LEVEL,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    sys.exit(main())
