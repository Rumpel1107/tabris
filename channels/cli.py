import config
import logging
import os
import uuid

from core.strings import msg

from core import memory_manager
from core.conversation import route_message, safe_handle_turn
from core.db import find_user_by_key, get_messages, init_db
from core.onboarding import advance_onboarding
from core.prompt import load_persona
from core.session import get_or_create_session


# --- Channel identity ---
def get_client_key(path=config.CLIENT_ID_PATH):
    if os.path.exists(path):
        with open(path, "r") as key_file:
            return key_file.read().strip()
    key = str(uuid.uuid4())
    with open(path, "w") as key_file:
        key_file.write(key)
    os.chmod(path, 0o600)
    return key

# --- Main conversation loop ---
def chat():
    db_path = config.DB_PATH
    init_db(db_path)

    key = get_client_key()
    user = find_user_by_key(db_path, "cli", key)

    sessions = {}
    session = get_or_create_session(
        sessions,
        "cli",
        key,
        user["id"] if user else None,
        user["language"] if user else "en",
    )

    print(msg("startup", session.language, agent=config.AGENT_NAME, exit_cmd=msg("exit_command", session.language)))

    while session.user_id is None:
        user_input = input(msg("user_prompt", session.language))
        if not user_input.strip():
            continue
        print(advance_onboarding(session, user_input, db_path))

    persona = load_persona()
    past_messages = get_messages(db_path, session.user_id, limit=config.MAX_HISTORY * 2)
    session.conversation_history = [
        {"role": message["role"], "content": message["content"]}
        for message in past_messages
    ]

    session.last_analyzed_index = len(session.conversation_history)

    while True:
        user_input = input(msg("user_prompt", session.language))

        if not user_input.strip():
            continue

        role = route_message(user_input)

        if role == "exit":
            if session.last_analyzed_index < len(session.conversation_history):
                changes = memory_manager.analyze_memory(session.conversation_history, db_path, session.user_id, language=session.language, watermark=session.last_analyzed_index)
                memory_manager.apply_memory_changes(db_path, session.user_id, changes)
            break

        reply = safe_handle_turn(session, user_input, role, db_path, persona)

        print(msg("agent_reply", session.language, agent=config.AGENT_NAME, role=role, reply=reply))


if __name__ == "__main__":
    logging.basicConfig(
        level=config.LOG_LEVEL,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    chat()