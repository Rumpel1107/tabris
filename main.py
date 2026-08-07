import config
import logging
import os
import uuid

from core.strings import msg

from core import memory_manager
from core.conversation import route_message, safe_handle_turn
from core.db import create_user, find_user_by_key, get_facts, get_messages, get_user, init_db, register_user_channel
from core.onboarding import detect_language, extract_location, extract_name, interpret_yes_no, is_timezone_ambiguous, resolve_timezone
from core.prompt import build_system_prompt, load_persona
from core.session import get_or_create_session


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
            if session.last_analyzed_index < len(session.conversation_history):
                changes = memory_manager.analyze_memory(session.conversation_history, db_path, session.user_id, language=session.language, watermark=session.last_analyzed_index)
                memory_manager.apply_memory_changes(db_path, session.user_id, changes)
            break

        reply = safe_handle_turn(session, user_input, role, db_path, persona)

        print(msg("agent_reply", session.language, agent=config.AGENT_NAME, role=role, reply=reply))


if __name__ == "__main__":
    logging.basicConfig(
        level=config.LOG_LEVEL,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    chat()