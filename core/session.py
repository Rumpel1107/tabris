import time
from dataclasses import dataclass, field


@dataclass
class Session:
    user_id: int | None = None
    language: str = "en"
    onboarding_step: str | None = None
    conversation_history: list = field(default_factory=list)
    exchange_count: int = 0
    last_trigger_time: float = field(default_factory=time.time)
    last_analyzed_index: int = 0
    last_turn_message_ids: list = field(default_factory=list)
    rate_tokens: float = 0.0
    rate_last_refill: float = 0.0
    channel: str = ""
    key: str = ""
    pending_name: str = ""
    pending_location: str = ""
    pending_city: str = ""
    pending_timezone: str = ""


def get_or_create_session(sessions, channel, key, user_id=None, language="en"):
    session_key = (channel, key)
    if session_key not in sessions:
        sessions[session_key] = Session(user_id=user_id, language=language, channel=channel, key=key)
    return sessions[session_key]