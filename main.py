import config

from core import memory_manager, providers

# --- Memory ---
def load_memory(path=config.MEMORY_PATH):
    try:
        with open(path, "r") as memory_file:
            content = memory_file.read()
            content = content.replace("{{AGENT_NAME}}", config.AGENT_NAME)
            return content
    except FileNotFoundError:
        return "No memory file found."

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

    print(config.AGENT_NAME + " activo. Escribe 'salir' para terminar.\n")

    while True:
        user_input = input("Tú: ")

        # Ignore empty messages
        if not user_input.strip():
            continue
        
        if user_input.lower() == "salir":
            memory_manager.update_memory(conversation_history)
            break

        role = route_message(user_input)
        conversation_history.append({"role": "user", "content": user_input})

        try:
            bounded_messages = build_messages(conversation_history)
            reply = providers.chat(role, bounded_messages)
        except Exception as e:
            print(f"Error al obtener respuesta del modelo: {e}\n")
            conversation_history.pop()
            continue

        conversation_history.append({"role": "assistant", "content": reply})
        print(f"\n{config.AGENT_NAME} ({role}): {reply}\n")
        

if __name__ == "__main__":
    chat()