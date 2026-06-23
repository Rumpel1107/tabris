import config

from core.strings import msg

from core import memory_manager, providers

# --- Memory ---
def load_memory(path=config.MEMORY_PATH):
    try:
        with open(path, "r") as memory_file:
            content = memory_file.read()
            content = content.replace("{{AGENT_NAME}}", config.AGENT_NAME)
            return content
    except FileNotFoundError:
        return msg("no_memory_file")

# --- Router ---
def route_message(user_input):
    code_keywords = ["código", "code", "error", "bug", "función", "script", "python"]
    if any(word in user_input.lower() for word in code_keywords):
        return "code"
    return "general"

# --- Context window ---
def build_messages(conversation_history):
    return conversation_history[:1] + conversation_history[1:][-config.MAX_HISTORY * 2:]

# --- Main conversation loop ---
def chat():
    memory = load_memory()
    conversation_history = [
        {
            "role": "system",
            "content": memory
        }
    ]

    print(msg("startup", agent=config.AGENT_NAME, exit_cmd=msg("exit_command")))

    while True:
        user_input = input(msg("user_prompt"))

        # Ignore empty messages
        if not user_input.strip():
            continue
        
        if user_input.lower() == msg("exit_command"):
            memory_manager.update_memory(conversation_history)
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
        print(msg("agent_reply", agent=config.AGENT_NAME, role=role, reply=reply))
        

if __name__ == "__main__":
    chat()