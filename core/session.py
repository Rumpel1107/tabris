import time
from dataclasses import dataclass, field


@dataclass
class Session:
    user_id: int
    language: str
    conversation_history: list = field(default_factory=list)
    exchange_count: int = 0
    last_trigger_time: float = field(default_factory=time.time)
    last_analyzed_index: int = 0

def get_or_create_session(sessions, channel, key, user_id, language):
    session_key = (channel, key)
    if session_key not in sessions:
        sessions[session_key] = Session(user_id=user_id, language=language)
    return sessions[session_key]