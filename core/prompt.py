import config
import re
from datetime import datetime, timezone as dt_timezone
from zoneinfo import ZoneInfo

from core.strings import MONTHS, WEEKDAYS


def load_persona(path=config.PERSONA_PATH):
    with open(path, "r") as persona_file:
        content = persona_file.read()
    return content.replace("{{AGENT_NAME}}", config.AGENT_NAME)


def format_date(dt, language):
    lang = language if language in WEEKDAYS else "en"
    day = WEEKDAYS[lang][dt.weekday()]
    month = MONTHS[lang][dt.month - 1]
    if lang == "es":
        return f"{day}, {dt.day} de {month} de {dt.year}"
    return f"{day}, {month} {dt.day}, {dt.year}"


def format_datetime(dt, language):
    return f"{format_date(dt, language)} — {dt.strftime('%H:%M')}"


def _starts_a_new_day(last_message_at, local_now, timezone):
    if not last_message_at:
        return False
    last_utc = datetime.fromisoformat(last_message_at).replace(tzinfo=dt_timezone.utc)
    return last_utc.astimezone(ZoneInfo(timezone)).date() < local_now.date()


def build_system_prompt(persona, facts, language, name, location="", timezone="UTC", channels=(), now=None, last_message_at=None):
    if now is None:
        now = datetime.now(dt_timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=dt_timezone.utc)
    local_now = now.astimezone(ZoneInfo(timezone))
    lang_name = config.LANGUAGE_NAMES.get(language, language)
    directive = f"\nAlways respond in {lang_name}."
    context_block = f"\n\n## Current context\nDate and time: {format_datetime(local_now, language)}"
    if _starts_a_new_day(last_message_at, local_now, timezone):
        context_block += "\nThis is the user's first message of the day."
    location_part = f", located in {location}" if location else ""
    channels_part = f" You talk to them over {', '.join(channels)}." if channels else ""
    name_block = f"\n\n## Profile\nYou are talking to {name}{location_part}.{channels_part}"
    if not facts:
        return persona + name_block + context_block + directive
    facts_block = "\n".join(f"- [{fact['id']}] {fact['content']}" for fact in facts)
    return f"{persona}{name_block}\n\n## What I know about the user\n{facts_block}{context_block}{directive}"

def fence_user_input(text: str) -> str:
    """Wrap untrusted user text so prompts treat it as data, never as instructions."""
    cleaned = re.sub(r"</?user_message>", "[tag removed]", text, flags=re.IGNORECASE)
    return f"<user_message>\n{cleaned}\n</user_message>"