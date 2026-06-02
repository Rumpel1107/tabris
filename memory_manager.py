import ollama
import config

# --- Memory Update ---
# Gemma analyzes the conversation and proposes updates to memory.md
def update_memory(conversation_history, memory_path="memory.md"):

    # Read current memory content
    with open(memory_path, "r") as memory_file:
        current_memory = memory_file.read()

    # Build the analysis prompt for Gemma
    conversation_text = "\n".join(
        f"{msg['role'].upper()}: {msg['content']}"
        for msg in conversation_history
        if msg["role"] != "system"
    )

    analysis_prompt = f"""You are analyzing a conversation to update a memory file.
    
Current memory.md content:
{current_memory}

Conversation from this session:
{conversation_text}

Identify what section needs to change, and provide the complete section content with the changes already integrated.

Respond ONLY in this exact format:
HAS_CHANGES: yes
SECTION: ### Section Name
CONTENT:
new content here

Or if there are no changes:
HAS_CHANGES: no

Do not add any explanation outside of this format."""

    print("\nTabris: Analizando la conversacion para actualizar la memoria...\n")

    response = ollama.chat(
        model = config.GENERAL_MODEL,
        messages=[{"role": "user", "content": analysis_prompt}]
    )

    raw_response = response.message.content.strip()
    has_changes = "HAS_CHANGES: yes" in raw_response

    if has_changes:
        updates = raw_response.split("CONTENT:")[-1].strip()
        section_line = [l for l in raw_response.split("\n") if l.startswith("SECTION:")]
        section = section_line[0].replace("SECTION:", "").strip() if section_line else None

        print(f"Tabris: Cambios propuestos en '{section}':\n\n{updates}\n")
        confirmation = input("Confirmas estos cambios? (si/no): ").strip().lower()

        if confirmation == "si" and section:
            updated_memory = replace_section(current_memory, section, updates)
            with open(memory_path, "w") as memory_file:
                memory_file.write(updated_memory)
            print("Tabris: Memoria actualizada.")
        else:
            print("Tabris: No se realizaron actualizaciones en la memoria.")
    else:
        print("Tabris: No se realizaron actualizaciones en la memoria.")


# --- Section Replacer ---
# Finds a section by its header and replaces its content
def replace_section(content, section_header, new_content):
    lines = content.split("\n")
    result = []
    inside_section = False

    for line in lines:
        if line.strip() == section_header.strip():
            inside_section = True
            result.append(line)
            result.append(new_content)
            continue

        if inside_section and line.startswith("#"):
            inside_section = False

        if not inside_section:
            result.append(line)

    return "\n".join(result)