import config

from core import providers
from core.db import get_facts, save_fact, deactivate_fact
from core.strings import msg

def parse_facts_response(raw_response):
    if "HAS_CHANGES: yes" not in raw_response:
        return False, [], [], None
    
    new_facts = []
    retire_ids = []
    
    if "NEW_FACTS:" in raw_response:
        facts_block = raw_response.split("NEW_FACTS:", 1)[1].split("RETIRE_IDS:")[0]
        new_facts = [
            line.strip().lstrip("-").strip()
            for line in facts_block.split("\n")
            if line.strip().startswith("-")
    ]
    
    if "RETIRE_IDS:" in raw_response:
        ids_line = raw_response.split("RETIRE_IDS:", 1)[1].split("\n")[0]
        retire_ids = [
            int(i.strip())
            for i in ids_line.split(",")
            if i.strip().isdigit()
        ]
    if not new_facts and not retire_ids:
        return False, [], [], "HAS_NEW_CHANGES is yes but no NEW_FACTS or RETIRE_IDS were provided"
    
    return True, new_facts, retire_ids, None

def filter_valid_retire_ids(retire_ids, known_facts):
    known_ids = {fact["id"] for fact in known_facts}
    return [fid for fid in retire_ids if fid in known_ids]

def update_memory(conversation_history, db_path, user_id, watermark=1):
    conversation_text = "\n".join(
        f"{turn['role'].upper()}: {turn['content']}"
        for turn in conversation_history[watermark:]
        if turn["role"] == "user"
    )
    
    known_facts = get_facts(db_path, user_id)
    known_text = "\n".join(f"- [{fact['id']}] {fact['content']}" for fact in known_facts)
    
    analysis_prompt = f"""You are analyzing a conversation to extract memory changes about the user.

Known facts (with IDs):
{known_text}

Conversation from this session (user turns only):
{conversation_text}

Extract only durable facts ABOUT THE USER as a person: their preferences, personal data, projects, and goals.
Do NOT extract anything about the assistant, its capabilities, its limitations, or the rules of the conversation.
Produce all NEW_FACTS in {config.LANGUAGE_NAMES.get(config.LANGUAGE, "English")}.

Identify NEW durable facts to remember AND existing facts to retire (because they became false or were corrected).

Respond ONLY in this exact format:
HAS_CHANGES: yes
NEW_FACTS:
- new fact one
- new fact two
RETIRE_IDS: 3, 7

Or if there is nothing to change:
HAS_CHANGES: no

Omit NEW_FACTS if none. Omit RETIRE_IDS if none. No explanation outside this format."""

    print(msg("analyzing_memory", agent=config.AGENT_NAME))
    
    try:
        raw_response = providers.chat(
            "general",
            [{"role": "user", "content": analysis_prompt}]
        ).strip()
    except Exception as e:
        print(msg("model_error", agent=config.AGENT_NAME, error=e))
        return
    
    has_changes, new_facts, retire_ids, error = parse_facts_response(raw_response)
    retire_ids = filter_valid_retire_ids(retire_ids, known_facts)
    if error:
        print(msg("invalid_model_response", agent=config.AGENT_NAME, error=error))
        return
    
    if not has_changes:
        print(msg("no_changes", agent=config.AGENT_NAME))
        return
    
    retire_text = "\n".join(f"- ID {fid}" for fid in retire_ids)
    display = "\n".join(f"- {fact}" for fact in new_facts)
    if retire_ids:
        display += f"\n\n{msg('retire_facts_header', agent=config.AGENT_NAME)}\n{retire_text}"
    print(msg("proposed_facts", agent=config.AGENT_NAME, facts=display))
    confirmation = input(msg("confirm_changes", agent=config.AGENT_NAME)).strip().lower()
    
    if confirmation == msg("confirm_yes"):
        for fact in new_facts:
            save_fact(db_path, user_id, fact)
        for fact_id in retire_ids:
            deactivate_fact(db_path, user_id, fact_id)
        print(msg("memory_updated", agent=config.AGENT_NAME))
    else:
        print(msg("no_changes", agent=config.AGENT_NAME))