import config
import httpx
import logging

logger = logging.getLogger(__name__)


def _transcribe_groq(audio: bytes, filename: str, language: str | None) -> str:
    data = {"model": config.TRANSCRIBE_MODEL}
    if language:
        data["language"] = language
    response = httpx.post(
        "https://api.groq.com/openai/v1/audio/transcriptions",
        headers={"Authorization": f"Bearer {config.GROQ_API_KEY}"},
        files={"file": (filename, audio, "application/octet-stream")},
        data=data,
        timeout=config.PROVIDER_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["text"]


def transcribe(audio: bytes, filename: str, language: str | None = None) -> str | None:
    """Turn recorded audio into text, empty when nothing was said, or None when no provider could answer."""
    adapters = {"groq": _transcribe_groq}
    for name in config.TRANSCRIBE_PROVIDERS:
        try:
            text = adapters[name](audio, filename, language).strip()
            return text if any(character.isalpha() for character in text) else ""
        except Exception as e:
            logger.warning(f"transcription provider '{name}' failed ({e}); trying next...")
    return None
