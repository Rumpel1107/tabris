import shutil
import config

from core import providers
from core.strings import msg

def parse_memory_update(raw_response):
    has_changes = "HAS_CHANGES: yes" in raw_response
    if not has_changes:
        return False, None, None, None
    
    section_lines = [l for l in raw_response.split("\n") if l.startswith("SECTION:")]
    content_blocks = raw_response.split("CONTENT:")
    
    if len(section_lines) > 1:
        return False, None, None, "Multiple SECTION headers in response"
    
    if len(content_blocks) > 2:
        return False, None, None, "Multiple CONTENT blocks in response"
    
    if len(content_blocks) < 2:
        return False, None, None, "Missing CONTENT block in response"
    
    section = section_lines[0].replace("SECTION:", "").strip() if section_lines else None
    
    if section_lines and not section:
        return False, None, None, "Empty SECTION header in response"
    
    content = content_blocks[-1].strip()
    
    return True, section, content, None

def update_memory(conversation_history, memory_path="memory.md"):
    
    try:
        with open(memory_path, "r") as memory_file:
            current_memory = memory_file.read()
    except FileNotFoundError:
        print(msg("memory_file_not_found", agent=config.AGENT_NAME, path=memory_path))
        return
    
    conversation_text = "\n".join(
        f"{turn['role'].upper()}: {turn['content']}"
        for turn in conversation_history
        if turn["role"] != "system"
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

    print(msg("analyzing_memory", agent=config.AGENT_NAME))
    
    try:
        raw_response = providers.chat(
            "general",
            [{"role": "user", "content": analysis_prompt}]
        ).strip()
    except Exception as e:
        print(msg("model_error", agent=config.AGENT_NAME, error=e))
        return
    
    has_changes, section, updates, error = parse_memory_update(raw_response)
    if error:
        print(msg("invalid_model_response", agent=config.AGENT_NAME, error=error))
        return
    
    if has_changes:
        print(msg("proposed_changes", agent=config.AGENT_NAME, section=section, updates=updates))
        confirmation = input(msg("confirm_changes")).strip().lower()
        
        if confirmation == msg("confirm_yes"):
            if section:
                updated_memory = replace_section(current_memory, section, updates)
                try:
                    shutil.copy2(memory_path, memory_path + ".bak")
                    with open(memory_path, "w") as memory_file:
                        memory_file.write(updated_memory)
                except Exception as e:
                    print(msg("save_error", agent=config.AGENT_NAME, error=e))
                    return
                print(msg("memory_updated", agent=config.AGENT_NAME))
            else:
                print(msg("no_section", agent=config.AGENT_NAME))
        else:
            print(msg("no_changes", agent=config.AGENT_NAME))
    else:
        print(msg("no_changes", agent=config.AGENT_NAME))


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