import ollama
import memory_manager
import config

# --- Memory ---
# Opens memory.md and loads its full content as Tabris context
def load_memory(path="memory.md"):
    try:
        with open(path, "r") as memory_file:
            content = memory_file.read()
            content = content.replace("{{AGENT_NAME}}", config.AGENT_NAME)
            return content
    except FileNotFoundError:
        return "No memory file found."


# --- Router ---
# Decides which model responds based on keywords in the message
# Note: this will be replaced by an LLM-based router in a future step
def route_message(user_input):
    code_keywords = ["código", "code", "error", "bug", "función", "script", "python"]
    if any(word in user_input.lower() for word in code_keywords):
        return config.CODE_MODEL
    return config.GENERAL_MODEL


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

        model = route_message(user_input)
        conversation_history.append({"role": "user", "content": user_input})

        try:
            response = ollama.chat(model=model, messages=conversation_history)
            reply = response.message.content
        except Exception as e:
            print(f"Error al obtener respuesta del modelo: {e}\n")
            conversation_history.pop()
            continue

        conversation_history.append({"role": "assistant", "content": reply})
        print(f"\n" + config.AGENT_NAME + " ({model}): {reply}\n")
        

if __name__ == "__main__":
    chat()