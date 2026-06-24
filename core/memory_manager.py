import config

from core import providers
from core.db import get_facts, save_fact
from core.strings import msg

def parse_facts_response(raw_response):
    if "HAS_NEW_FACTS: yes" not in raw_response:
        return False, [], None
    
    if "FACTS:" not in raw_response:
        return False, [], "Missing FACTS block in response"
    
    facts_block = raw_response.split("FACTS:", 1)[1]
    facts = [
        line.strip().lstrip("-").strip()
        for line in facts_block.split("\n")
        if line.strip().startswith("-")
    ]
    
    if not facts:
        return False, [], "HAS_NEW_FACTS is yes but no facts were listed"
    
    return True, facts, None

def update_memory(conversation_history, db_path, user_id):
    conversation_text = "\n".join(
        f"{turn['role'].upper()}: {turn['content']}"
        for turn in conversation_history
        if turn["role"] != "system"
    )
    
    known_facts = get_facts(db_path, user_id)
    known_text = "\n".join(f"- {fact['content']}" for fact in known_facts)
    
    analysis_prompt = f"""You are analyzing a conversation to extract NEW facts to remember about the user.

Facts already known:
{known_text}

Conversation from this session:
{conversation_text}

Identify only NEW, durable facts about the user that are not already known. Ignore one-off or trivial details.

Respond ONLY in this exact format:
HAS_NEW_FACTS: yes
FACTS:
- new fact one
- new fact two

Or if there is nothing new:
HAS_NEW_FACTS: no

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

    has_facts, facts, error = parse_facts_response(raw_response)
    if error:
        print(msg("invalid_model_response", agent=config.AGENT_NAME, error=error))
        return

    if not has_facts:
        print(msg("no_changes", agent=config.AGENT_NAME))
        return

    print(msg("proposed_facts", agent=config.AGENT_NAME, facts="\n".join(f"- {fact}" for fact in facts)))
    confirmation = input(msg("confirm_changes")).strip().lower()

    if confirmation == msg("confirm_yes"):
        for fact in facts:
            save_fact(db_path, user_id, fact)
        print(msg("memory_updated", agent=config.AGENT_NAME))
    else:
        print(msg("no_changes", agent=config.AGENT_NAME))