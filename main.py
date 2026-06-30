import config
import os
import uuid
import time

from core.strings import msg

from core import memory_manager, providers
from core.db import init_db, get_facts, get_messages, save_message, create_user, find_user_by_key, register_user_channel, update_user_language

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
    raw_name = input(msg("ask_name", agent=config.AGENT_NAME))
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
def route_message(user_input):
    roles_list = "\n".join(
        f"- {role}: {cfg['description']}"
        for role, cfg in config.AGENT_ROLES.items()
        if role != "router"
    )
    prompt = [{
        "role": "user",
        "content": f"""Classify this message into exactly one of the available roles or 'exit'.

Available roles:
{roles_list}
- exit: the user wants to end the conversation

Message: {user_input}

Reply with only one word."""
    }]
    try:
        response = providers.chat("router", prompt).strip().lower()
    except Exception:
        return "general"
    valid = [r for r in config.AGENT_ROLES if r != "router"] + ["exit"]
    return response if response in valid else "general"

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
    config.LANGUAGE = detected
    confirmation = confirm_fn()
    if confirmation.strip().lower() == msg("confirm_yes"):
        return detected
    chosen = ask_fn().strip().lower()
    return chosen if chosen in ("es", "en") else "en"

# --- Context window ---
def build_messages(conversation_history):
    return conversation_history[:1] + conversation_history[1:][-config.MAX_HISTORY * 2:]

def build_system_prompt(persona, facts, language):
    lang_name = config.LANGUAGE_NAMES.get(language, language)
    directive = f"\nAlways respond in {lang_name}."
    if not facts:
        return persona + directive
    facts_block = "\n".join(f"- {fact['content']}" for fact in facts)
    return f"{persona}\n\n## What I know about the user\n{facts_block}{directive}"

def should_trigger_memory(exchange_count, last_trigger_time):
    if exchange_count >= config.MEMORY_TRIGGER_EXCHANGES:
        return True
    if time.time() - last_trigger_time >= config.MEMORY_TRIGGER_SECONDS:
        return True
    return False

# --- Main conversation loop ---
def chat():
    db_path = config.DB_PATH
    init_db(db_path)
    
    key = get_client_key()
    user = find_user_by_key(db_path, "cli", key)
    
    if user:
        user_id = user["id"]
        config.LANGUAGE = user["language"]
        language_detected = True
    else:
        user_id = onboard_user(db_path, "cli", key)
        language_detected = False
    
    persona = load_persona()
    facts = get_facts(db_path, user_id)
    system_prompt = build_system_prompt(persona, facts, language=config.LANGUAGE)
    
    conversation_history = [{"role": "system", "content": system_prompt}]
    past_messages = get_messages(db_path, user_id, limit=config.MAX_HISTORY * 2)
    conversation_history += [
        {"role": message["role"], "content": message["content"]}
        for message in past_messages
    ]
    
    exchange_count = 0
    last_trigger_time = time.time()
    last_analyzed_index = len(conversation_history)
    
    print(msg("startup", agent=config.AGENT_NAME, exit_cmd=msg("exit_command")))
    
    while True:
        user_input = input(msg("user_prompt"))
        
        if not user_input.strip():
            continue
        
        if not language_detected:
            detected = detect_language(user_input)
            chosen = resolve_language(
                detected,
                confirm_fn=lambda: input(msg("language_detected", agent=config.AGENT_NAME)),
                ask_fn=lambda: input(msg("language_ask", agent=config.AGENT_NAME)),
            )
            update_user_language(db_path, user_id, chosen)
            config.LANGUAGE = chosen
            print(msg("language_confirmed", agent=config.AGENT_NAME))
            system_prompt = build_system_prompt(persona, facts, language=config.LANGUAGE)
            conversation_history[0] = {"role": "system", "content": system_prompt}
            language_detected = True
        
        role = route_message(user_input)
        
        if role == "exit":
            memory_manager.update_memory(conversation_history, db_path, user_id, watermark=last_analyzed_index)
            break
        
        conversation_history.append({"role": "user", "content": user_input})
        
        try:
            bounded_messages = build_messages(conversation_history)
            reply = providers.chat(role, bounded_messages)
        except Exception as e:
            print(msg("model_error", agent=config.AGENT_NAME, error=e))
            conversation_history.pop()
            continue
        
        conversation_history.append({"role": "assistant", "content": reply})
        save_message(db_path, user_id, "user", user_input)
        save_message(db_path, user_id, "assistant", reply)
        print(msg("agent_reply", agent=config.AGENT_NAME, role=role, reply=reply))
        
        exchange_count += 1
        if should_trigger_memory(exchange_count, last_trigger_time):
            memory_manager.update_memory(conversation_history, db_path, user_id, watermark=last_analyzed_index)
            last_analyzed_index = len(conversation_history)
            exchange_count = 0
            last_trigger_time = time.time()


if __name__ == "__main__":
    chat()