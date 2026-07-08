import config
import logging
import os
import uuid

from core.strings import MONTHS, msg, WEEKDAYS

from core import memory_manager, providers
from core.conversation import handle_turn, route_message
from core.db import create_user, find_user_by_key, get_facts, get_messages, init_db, register_user_channel, update_user_language
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

def onboard_user(db_path, channel, key):
    raw_name = input(msg("ask_name", "en", agent=config.AGENT_NAME))
    name = extract_name(raw_name)
    user_id = create_user(db_path, name)
    register_user_channel(db_path, user_id, channel, key)
    return user_id

# --- Memory ---
def load_persona(path=config.PERSONA_PATH):
    with open(path, "r") as persona_file:
        content = persona_file.read()
    return content.replace("{{AGENT_NAME}}", config.AGENT_NAME)

# --- Router ---
def detect_language(text):
    prompt = [{
        "role": "user",
        "content": f"""Detect the language of this message. Reply with only 'es' for Spanish or 'en' for English.

Message: {text}

Reply with only one word: 'es' or 'en'."""
    }]
    try:
        response = providers.chat("router", prompt).strip().lower()
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
        response = providers.chat("router", prompt).strip()
    except Exception:
        return text.strip()
    return response if response else text.strip()

def resolve_language(detected, confirm_fn, ask_fn):
    confirmation = confirm_fn()
    if confirmation.strip().lower() == msg("confirm_yes", detected):
        return detected
    chosen = ask_fn().strip().lower()
    return chosen if chosen in ("es", "en") else "en"

# --- Context window ---
def format_datetime(dt, language):
    lang = language if language in WEEKDAYS else "en"
    day = WEEKDAYS[lang][dt.weekday()]
    month = MONTHS[lang][dt.month - 1]
    if lang == "es":
        return f"{day}, {dt.day} de {month} de {dt.year} — {dt.strftime('%H:%M')}"
    return f"{day}, {month} {dt.day}, {dt.year} — {dt.strftime('%H:%M')}"

def build_system_prompt(persona, facts, language, now=None):
    from datetime import datetime as _datetime
    if now is None:
        now = _datetime.now()
    lang_name = config.LANGUAGE_NAMES.get(language, language)
    directive = f"\nAlways respond in {lang_name}."
    context_block = f"\n\n## Current context\nDate and time: {format_datetime(now, language)}"
    if not facts:
        return persona + context_block + directive
    facts_block = "\n".join(f"- {fact['content']}" for fact in facts)
    return f"{persona}\n\n## What I know about the user\n{facts_block}{context_block}{directive}"

# --- Main conversation loop ---
def chat():
    db_path = config.DB_PATH
    init_db(db_path)
    
    key = get_client_key()
    user = find_user_by_key(db_path, "cli", key)
    
    if user:
        user_id = user["id"]
        language = user["language"]
        language_detected = True
    else:
        user_id = onboard_user(db_path, "cli", key)
        language = "en"
        language_detected = False
    
    sessions = {}
    session = get_or_create_session(sessions, "cli", key, user_id, language)
    
    persona = load_persona()
    facts = get_facts(db_path, user_id)
    system_prompt = build_system_prompt(persona, facts, language=session.language)
    
    session.conversation_history = [{"role": "system", "content": system_prompt}]
    past_messages = get_messages(db_path, user_id, limit=config.MAX_HISTORY * 2)
    session.conversation_history += [
        {"role": message["role"], "content": message["content"]}
        for message in past_messages
    ]
    
    session.last_analyzed_index = len(session.conversation_history)
    
    print(msg("startup", session.language, agent=config.AGENT_NAME, exit_cmd=msg("exit_command", session.language)))
    
    while True:
        user_input = input(msg("user_prompt", session.language))
        
        if not user_input.strip():
            continue
        
        if not language_detected:
            detected = detect_language(user_input)
            chosen = resolve_language(
                detected,
                confirm_fn=lambda: input(msg("language_detected", detected, agent=config.AGENT_NAME)),
                ask_fn=lambda: input(msg("language_ask", detected, agent=config.AGENT_NAME)),
            )
            update_user_language(db_path, user_id, chosen)
            session.language = chosen
            print(msg("language_confirmed", session.language, agent=config.AGENT_NAME))
            system_prompt = build_system_prompt(persona, facts, language=session.language)
            session.conversation_history[0] = {"role": "system", "content": system_prompt}
            language_detected = True
        
        role = route_message(user_input)
        
        if role == "exit":
            memory_manager.update_memory(session.conversation_history, db_path, session.user_id, language=session.language, watermark=session.last_analyzed_index)
            break
        
        try:
            reply = handle_turn(session, user_input, role, db_path)
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