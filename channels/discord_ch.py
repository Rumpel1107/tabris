import asyncio
import base64
import config
import discord
import logging

from core.conversation import choose_role, safe_handle_turn, undo_last_turn
from core.db import find_user_by_key, get_messages, init_db
from core.onboarding import advance_onboarding
from core.prompt import history_entry, load_persona
from core.session import get_or_create_session
from core.strings import msg
from core.text import split_message
from core.transcribe import transcribe
from core.version import describe


logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

_locks = {}


async def _run_locked(key, func, *args, **kwargs):
    """Run a blocking call in a worker thread, serialized per key so the same person's turns never overlap."""
    if key not in _locks:
        _locks[key] = asyncio.Lock()
    async with _locks[key]:
        return await asyncio.to_thread(func, *args, **kwargs)


@client.event
async def on_ready():
    print(f"{config.AGENT_NAME} connected as {client.user}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    key = str(message.author.id)
    voice = message.attachments[0] if message.flags.voice and message.attachments else None
    audio = None
    if voice is not None and (voice.duration or 0) <= config.AUDIO_MAX_SECONDS:
        audio = await voice.read()
    images, images_seen = [], 0
    if voice is None:
        pictures = [a for a in message.attachments if (a.content_type or "").startswith("image/")]
        images_seen = len(pictures)
        if any(picture.size > config.IMAGE_MAX_BYTES for picture in pictures):
            images = None   # the size the platform reports is enough to refuse: nothing is downloaded
        else:
            for picture in pictures[:config.IMAGE_MAX_COUNT]:
                encoded = base64.b64encode(await picture.read()).decode()
                images.append(f"data:{picture.content_type};base64,{encoded}")
    async with message.channel.typing():  # a turn with a web search takes long enough that silence reads as being ignored
        if voice is not None:
            reply = await _run_locked(key, handle_voice, db_path, sessions, key, audio, voice.filename, voice.duration, persona)
        else:
            reply = await _run_locked(
                key, handle_message, db_path, sessions, key, message.content, persona,
                images=images, images_seen=images_seen,
            )
    session = sessions[("discord", key)]
    if not await send_reply(message.channel, reply, session):
        undo_last_turn(session, db_path)


async def send_reply(channel, reply, session):
    """Send the reply split into pieces Discord will accept. Return whether the whole reply was delivered."""
    for piece in split_message(reply, config.DISCORD_MESSAGE_LIMIT):
        try:
            await channel.send(piece)
        except Exception:
            logger.exception("Failed to deliver a reply piece on discord")
            try:
                await channel.send(msg("send_failed", session.language))
            except Exception:
                logger.exception("Failed to deliver the send-failure notice on discord")
            return False
    return True


def handle_voice(db_path, sessions, key, audio, filename, duration, persona):
    """Answer a voice message; `audio` is None when it was refused for being too long."""
    user = find_user_by_key(db_path, "discord", key)
    session = get_or_create_session(
        sessions,
        "discord",
        key,
        user["id"] if user else None,
        user["language"] if user else "en",
    )

    if audio is None:
        return msg("audio_too_long", session.language, minutes=config.AUDIO_MAX_SECONDS // 60)

    text = transcribe(audio, filename, session.language if user else None, duration)
    if text is None:
        return msg("audio_failed", session.language)
    if not text:
        return msg("audio_no_speech", session.language)

    reply = handle_message(db_path, sessions, key, text, persona)
    return msg("audio_transcript", session.language, text=text) + "\n\n" + reply


def handle_message(db_path, sessions, key, user_input, persona, images=(), images_seen=0):
    """Answer a typed message; `images` is None when one was refused for being too large."""
    user = find_user_by_key(db_path, "discord", key)
    session = get_or_create_session(
        sessions,
        "discord",
        key,
        user["id"] if user else None,
        user["language"] if user else "en",
    )

    if images is None:
        return msg("image_too_large", session.language, megabytes=config.IMAGE_MAX_BYTES // (1024 * 1024))

    if session.user_id is None:
        return advance_onboarding(session, user_input, db_path)

    if not session.conversation_history:
        past_messages = get_messages(db_path, session.user_id, limit=config.MAX_HISTORY * 2)
        user_timezone = user["timezone"] if user else "UTC"
        session.conversation_history = [
            history_entry(message["role"], message["content"], message["created_at"], user_timezone)
            for message in past_messages
        ]
        session.last_analyzed_index = len(session.conversation_history)

    role = choose_role(session, user_input, images)
    if role == "exit":
        role = "general"
    reply = safe_handle_turn(session, user_input, role, db_path, persona, images=images)
    if images_seen > len(images):
        return msg("images_capped", session.language, shown=len(images), sent=images_seen) + "\n\n" + reply
    return reply


if __name__ == "__main__":
    logging.basicConfig(
        level=config.LOG_LEVEL,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    logger.info("starting Tabris %s on discord", describe(config.BASE_DIR))
    db_path = config.DB_PATH
    sessions = {}
    persona = load_persona()
    init_db(db_path)
    client.run(config.DISCORD_BOT_TOKEN, log_handler=None)  # logging is configured above; without this discord.py adds a second handler and every line is logged twice