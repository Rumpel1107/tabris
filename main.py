import config
import logging
import os
import uuid

from core.strings import msg

from core import memory_manager, providers
from core.conversation import handle_turn, route_message
from core.db import create_user, find_user_by_key, get_facts, get_messages, get_user, init_db, register_user_channel
from core.prompt import build_system_prompt, load_persona
from core.session import get_or_create_session
from zoneinfo import ZoneInfo


# --- Channel identity ---
def get_client_key(path=config.CLIENT_ID_PATH):
    if os.path.exists(path):
        with open(path, "r") as key_file:
            return key_file.read().strip()
    key = str(uuid.uuid4())
    with open(path, "w") as key_file:
        key_file.write(key)
    return key

def onboard_user(db_path, channel, key, language):
    raw_name = input(msg("ask_name", language, agent=config.AGENT_NAME))
    name = extract_name(raw_name)
    location = input(msg("ask_location", language, agent=config.AGENT_NAME)).strip()
    if is_timezone_ambiguous(location):
        clarification = input(msg("ask_location_clarify", language, agent=config.AGENT_NAME)).strip()
        location = f"{location}, {clarification}"
    timezone = resolve_timezone(location)
    city = extract_location(location)
    user_id = create_user(db_path, name, language, city, timezone)
    register_user_channel(db_path, user_id, channel, key)
    return user_id

# --- Router ---
def detect_language(text):
    prompt = [{
        "role": "user",
        "content": f"""Detect the language of this message. Reply with only 'es' for Spanish or 'en' for English.

Message: {text}

Reply with only one word: 'es' or 'en'."""
    }]
    try:
        response = providers.chat("router", prompt).content.strip().lower()
    except Exception:
        return "en"
    return response if response in ("es", "en") else "en"

def extract_name(text):
    prompt = [{
        "role": "user",
        "content": f"""Extract the person's name from this message. Reply with only the name, nothing else.

Message: {text}

Reply with only the name."""
    }]
    try:
        response = providers.chat("router", prompt).content.strip()
    except Exception:
        return text.strip()
    return response if response else text.strip()

def resolve_timezone(location):
    prompt = [{
        "role": "user",
        "content": f"""What is the IANA timezone identifier for this location? Reply with only the identifier (e.g. 'America/Panama'), nothing else.

Location: {location}

Reply with only the IANA timezone identifier."""
    }]
    try:
        response = providers.chat("router", prompt).content.strip()
        ZoneInfo(response)
        return response
    except Exception:
        return "UTC"

def is_timezone_ambiguous(location):
    prompt = [{
        "role": "user",
        "content": f"""Could this location refer to places in different time zones (e.g. 'Madrid' could be in Spain or Colombia)? Answer with only 'yes' or 'no'.

Location: {location}

Answer with only one word: 'yes' or 'no'."""
    }]
    try:
        response = providers.chat("router", prompt).content.strip().lower()
    except Exception:
        return False
    return response.startswith("yes")

def extract_location(text):
    prompt = [{
        "role": "user",
        "content": f"""Extract the location from the message. Reply with ONLY the location and nothing else — no explanations. Use only what the user mentioned; do not invent a country or region.

Message: Claro, vivo en Madrid Cundinamarca en Colombia
Location: Madrid, Cundinamarca, Colombia
Message: Vivo en Madrid
Location: Madrid

Message: {text}
Location:"""
    }]
    try:
        response = providers.chat("router", prompt).content.strip()
    except Exception:
        return text.strip()
    return response if response else text.strip()

def interpret_yes_no(text):
    prompt = [{
        "role": "user",
        "content": f"""Does the following reply mean yes? Answer with only 'yes' or 'no'.

Reply: {text}

Answer with only one word: 'yes' or 'no'."""
    }]
    try:
        response = providers.chat("router", prompt).content.strip().lower()
    except Exception:
        return False
    return response.startswith("yes")

def resolve_language(detected, confirm_fn, ask_fn, interpret_fn=interpret_yes_no, detect_fn=detect_language):
    if interpret_fn(confirm_fn()):
        return detected
    return detect_fn(ask_fn())

# --- Main conversation loop ---
def chat():
    db_path = config.DB_PATH
    init_db(db_path)

    key = get_client_key()
    user = find_user_by_key(db_path, "cli", key)

    if user:
        user_id = user["id"]
        language = user["language"]
    else:
        language = "en"
        print(msg("startup", language, agent=config.AGENT_NAME, exit_cmd=msg("exit_command", language)))
        first_input = input(msg("user_prompt", language))
        detected = detect_language(first_input)
        language = resolve_language(
            detected,
            confirm_fn=lambda: input(msg("language_detected", detected, agent=config.AGENT_NAME)),
            ask_fn=lambda: input(msg("language_ask", detected, agent=config.AGENT_NAME)),
        )
        print(msg("language_confirmed", language, agent=config.AGENT_NAME))
        user_id = onboard_user(db_path, "cli", key, language)

    user_row = get_user(db_path, user_id)
    name = user_row["name"]
    location = user_row["location"]
    timezone = user_row["timezone"]

    sessions = {}
    session = get_or_create_session(sessions, "cli", key, user_id, language)

    persona = load_persona()
    facts = get_facts(db_path, user_id)
    system_prompt = build_system_prompt(persona, facts, language=session.language, name=name, location=location, timezone=timezone)

    session.conversation_history = [{"role": "system", "content": system_prompt}]
    past_messages = get_messages(db_path, user_id, limit=config.MAX_HISTORY * 2)
    session.conversation_history += [
        {"role": message["role"], "content": message["content"]}
        for message in past_messages
    ]

    session.last_analyzed_index = len(session.conversation_history)

    if user:
        print(msg("startup", session.language, agent=config.AGENT_NAME, exit_cmd=msg("exit_command", session.language)))
    else:
        print(msg("onboarding_done", session.language, agent=config.AGENT_NAME, name=name))

    while True:
        user_input = input(msg("user_prompt", session.language))

        if not user_input.strip():
            continue

        role = route_message(user_input)

        if role == "exit":
            changes = memory_manager.analyze_memory(session.conversation_history, db_path, session.user_id, language=session.language, watermark=session.last_analyzed_index)
            memory_manager.apply_memory_changes(db_path, session.user_id, changes)
            break

        try:
            reply = handle_turn(session, user_input, role, db_path, persona)
        except Exception as e:
            print(msg("model_error", session.language, agent=config.AGENT_NAME, error=e))
            continue

        print(msg("agent_reply", session.language, agent=config.AGENT_NAME, role=role, reply=reply))


if __name__ == "__main__":
    logging.basicConfig(
        level=config.LOG_LEVEL,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    chat()