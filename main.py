import config
import time

from core.strings import msg

from core import memory_manager, providers
from core.db import init_db, get_or_create_user, get_facts, get_messages, save_message

# --- Memory ---
def load_persona(path=config.PERSONA_PATH):
    with open(path, "r") as persona_file:
        content = persona_file.read()
    return content.replace("{{AGENT_NAME}}", config.AGENT_NAME)

# --- Router ---
def route_message(user_input):
    code_keywords = ["código", "code", "error", "bug", "función", "script", "python"]
    if any(word in user_input.lower() for word in code_keywords):
        return "code"
    return "general"

# --- Context window ---
def build_messages(conversation_history):
    return conversation_history[:1] + conversation_history[1:][-config.MAX_HISTORY * 2:]

def build_system_prompt(persona, facts):
    if not facts:
        return persona
    facts_block = "\n".join(f"- {fact['content']}" for fact in facts)
    return f"{persona}\n\n## What I know about the user\n{facts_block}"

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
    user_id = get_or_create_user(db_path, config.USER_NAME, config.LANGUAGE)
    
    persona = load_persona()
    facts = get_facts(db_path, user_id)
    system_prompt = build_system_prompt(persona, facts)
    
    conversation_history = [{"role": "system", "content": system_prompt}]
    past_messages = get_messages(db_path, user_id, limit=config.MAX_HISTORY * 2)
    conversation_history += [
        {"role": message["role"], "content": message["content"]}
        for message in past_messages
    ]
    
    exchange_count = 0
    last_trigger_time = time.time()
    
    print(msg("startup", agent=config.AGENT_NAME, exit_cmd=msg("exit_command")))
    
    while True:
        user_input = input(msg("user_prompt"))
        
        if not user_input.strip():
            continue
        
        if user_input.lower() == msg("exit_command"):
            memory_manager.update_memory(conversation_history, db_path, user_id)
            break
        
        role = route_message(user_input)
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
            memory_manager.update_memory(conversation_history, db_path, user_id)
            exchange_count = 0
            last_trigger_time = time.time()


if __name__ == "__main__":
    chat()