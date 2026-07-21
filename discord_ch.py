import config
import discord
import logging

from core.conversation import handle_turn, route_message
from core.db import create_user, find_user_by_key, get_facts, get_messages, get_user, init_db, register_user_channel
from core.prompt import build_system_prompt, load_persona
from core.session import get_or_create_session


intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"{config.AGENT_NAME} connected as {client.user}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    reply = handle_message(db_path, sessions, str(message.author.id), message.author.display_name, message.content, persona)
    await message.channel.send(reply)


def handle_message(db_path, sessions, key, name, user_input, persona):
    user = find_user_by_key(db_path, "discord", key)
    if user:
        user_id = user["id"]
        language = user["language"]
    else:
        language = "en"
        user_id = create_user(db_path, name, language)
        register_user_channel(db_path, user_id, "discord", key)

    session = get_or_create_session(sessions, "discord", key, user_id, language)

    if not session.conversation_history:
        user_row = get_user(db_path, user_id)
        facts = get_facts(db_path, user_id)
        system_prompt = build_system_prompt(
            persona, facts, language=session.language,
            name=user_row["name"], location=user_row["location"], timezone=user_row["timezone"],
        )
        session.conversation_history = [{"role": "system", "content": system_prompt}]
        past_messages = get_messages(db_path, user_id, limit=config.MAX_HISTORY * 2)
        session.conversation_history += [
            {"role": message["role"], "content": message["content"]}
            for message in past_messages
        ]
        session.last_analyzed_index = len(session.conversation_history)

    role = route_message(user_input)
    if role == "exit":
        role = "general"
    return handle_turn(session, user_input, role, db_path, persona)


if __name__ == "__main__":
    logging.basicConfig(
        level=config.LOG_LEVEL,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    db_path = config.DB_PATH
    sessions = {}
    persona = load_persona()
    init_db(db_path)
    client.run(config.DISCORD_BOT_TOKEN)