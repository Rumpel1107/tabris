import config
from datetime import datetime, timezone as dt_timezone
from zoneinfo import ZoneInfo

from core.strings import MONTHS, WEEKDAYS


def load_persona(path=config.PERSONA_PATH):
    with open(path, "r") as persona_file:
        content = persona_file.read()
    return content.replace("{{AGENT_NAME}}", config.AGENT_NAME)


def format_datetime(dt, language):
    lang = language if language in WEEKDAYS else "en"
    day = WEEKDAYS[lang][dt.weekday()]
    month = MONTHS[lang][dt.month - 1]
    if lang == "es":
        return f"{day}, {dt.day} de {month} de {dt.year} — {dt.strftime('%H:%M')}"
    return f"{day}, {month} {dt.day}, {dt.year} — {dt.strftime('%H:%M')}"


def build_system_prompt(persona, facts, language, name, location="", timezone="UTC", now=None):
    if now is None:
        now = datetime.now(dt_timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=dt_timezone.utc)
    local_now = now.astimezone(ZoneInfo(timezone))
    lang_name = config.LANGUAGE_NAMES.get(language, language)
    directive = f"\nAlways respond in {lang_name}."
    context_block = f"\n\n## Current context\nDate and time: {format_datetime(local_now, language)}"
    location_part = f", located in {location}" if location else ""
    name_block = f"\n\nYou are talking to {name}{location_part}."
    if not facts:
        return persona + name_block + context_block + directive
    facts_block = "\n".join(f"- {fact['content']}" for fact in facts)
    return f"{persona}{name_block}\n\n## What I know about the user\n{facts_block}{context_block}{directive}"
