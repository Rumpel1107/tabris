import shutil
import ollama
import config


def parse_memory_update(raw_response):
    has_changes = "HAS_CHANGES: yes" in raw_response
    if not has_changes:
        return False, None, None, None
    
    section_lines = [l for l in raw_response.split("\n") if l.startswith("SECTION:")]
    content_blocks = raw_response.split("CONTENT:")
    
    if len(section_lines) > 1:
        return False, None, None, "Respuesta con multiples secciones" #Response with multiple SECTION headers
    
    if len(content_blocks) > 2:
        return False, None, None, "Respuesta con multiples bloques de CONTENT"
    
    if len(content_blocks) < 2:
        return False, None, None, "Respuesta sin bloque de CONTENT"
    
    section = section_lines[0].replace("SECTION:", "").strip() if section_lines else None
    
    if section_lines and not section:
        return False, None, None, "SECTION vacio en la respuesta"
    
    content = content_blocks[-1].strip()
    
    return True, section, content, None


def update_memory(conversation_history, memory_path="memory.md"):
    
    try:
        with open(memory_path, "r") as memory_file:
            current_memory = memory_file.read()
    except FileNotFoundError:
        print(f"{config.AGENT_NAME}: No se encontró el archivo de memoria '{memory_path}'.")
        return
    
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

    print(f"\n{config.AGENT_NAME}: Analizando la conversacion para actualizar la memoria...\n")
    
    try:
        response = ollama.chat(
            model=config.GENERAL_MODEL,
            messages=[{"role": "user", "content": analysis_prompt}]
            )
    except Exception as e:
        print(f"{config.AGENT_NAME}: Error al conectar con el modelo: {e}")
        return

    raw_response = response.message.content.strip()
    has_changes, section, updates, error = parse_memory_update(raw_response)
    if error:
        print(f"{config.AGENT_NAME}: Respuesta del modelo invalida - {error}. No se actualizo la memoria.")
        return

    if has_changes:
        print(f"{config.AGENT_NAME}: Cambios propuestos en '{section}':\n\n{updates}\n")
        confirmation = input("Confirmas estos cambios? (si/no): ").strip().lower()

        if confirmation == "si":
            if section:
                updated_memory = replace_section(current_memory, section, updates)
                try:
                    shutil.copy2(memory_path, memory_path + ".bak")
                    with open(memory_path, "w") as memory_file:
                        memory_file.write(updated_memory)
                except Exception as e:
                    print(f"{config.AGENT_NAME}: Error al guardar la memoria: {e}")
                    return
                print(f"{config.AGENT_NAME}: Memoria actualizada.")
            else:
                print(f"{config.AGENT_NAME}: No se pudo determinar la sección a actualizar.")
        else:
            print(f"{config.AGENT_NAME}: No se realizaron actualizaciones en la memoria.")
    else:
        print(f"{config.AGENT_NAME}: No se realizaron actualizaciones en la memoria.")


# --- Section Replacer ---
def replace_section(content, section_header, new_content):
    lines = content.split("\n")
    result = []
    inside_section = False
    section_level = len(section_header.split()[0])

    for line in lines:
        if line.strip() == section_header.strip():
            inside_section = True
            result.append(line)
            result.append(new_content)
            continue

        if inside_section:
            header_symbols = len(line.split()[0]) if line.startswith("#") else 0
            if line.startswith("#") and header_symbols <= section_level:
                inside_section = False

        if not inside_section:
            result.append(line)

    return "\n".join(result)