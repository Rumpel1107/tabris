import config
import json
import logging
import time

from core import memory_manager, providers
from core.db import save_message
from core.search import web_search

logger = logging.getLogger(__name__)


def build_messages(conversation_history):
    return conversation_history[:1] + conversation_history[1:][-config.MAX_HISTORY * 2:]

def route_message(user_input):
    roles_list = "\n".join(
        f"- {role}: {cfg['description']}"
        for role, cfg in config.AGENT_ROLES.items()
        if role != "router"
    )
    prompt = [{
        "role": "user",
        "content": f"""Classify this message into exactly one of the available roles or 'exit'.

Available roles:
{roles_list}
- exit: the user wants to end the conversation

Message: {user_input}

Reply with only one word."""
    }]
    try:
        response = providers.chat("router", prompt).content.strip().lower()
    except Exception as e:
        logger.warning(f"route_message failed ({e}); falling back to 'general'") # TODO(item 38): audit broad except-Exception handling project-wide
        return "general"
    valid = [r for r in config.AGENT_ROLES if r != "router"] + ["exit"]
    return response if response in valid else "general"

def should_trigger_memory(exchange_count, last_trigger_time):
    if exchange_count >= config.MEMORY_TRIGGER_EXCHANGES:
        return True
    if time.time() - last_trigger_time >= config.MEMORY_TRIGGER_SECONDS:
        return True
    return False

WEB_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web for live, up-to-date information. Use for current events, news, sports results, weather, prices, and any question about facts after your training data or that the user implies is recent ('today', 'yesterday', 'this week').",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"}
            },
            "required": ["query"],
        },
    },
}

def _execute_tool_call(tool_call):
    args = json.loads(tool_call.function.arguments)
    result = web_search(args["query"])
    return {"role": "tool", "tool_call_id": tool_call.id, "content": result}

def run_with_tools(role, messages, tools):
    while True:
        response = providers.chat(role, messages, tools=tools)
        if not response.tool_calls:
            return response.content
        messages.append({
            "role": "assistant",
            "content": response.content,
            "tool_calls": response.tool_calls,
        })
        for tool_call in response.tool_calls:
            messages.append(_execute_tool_call(tool_call))

def handle_turn(session, user_input, role, db_path):
    session.conversation_history.append({"role": "user", "content": user_input})
    try:
        reply = run_with_tools(role, build_messages(session.conversation_history), tools=[WEB_SEARCH_TOOL])
    except Exception:
        session.conversation_history.pop()
        raise
    session.conversation_history.append({"role": "assistant", "content": reply})
    save_message(db_path, session.user_id, "user", user_input)
    save_message(db_path, session.user_id, "assistant", reply)
    session.exchange_count += 1
    if should_trigger_memory(session.exchange_count, session.last_trigger_time):
        memory_manager.update_memory(
            session.conversation_history,
            db_path,
            session.user_id,
            language=session.language,
            watermark=session.last_analyzed_index,
        )
        session.last_analyzed_index = len(session.conversation_history)
        session.exchange_count = 0
        session.last_trigger_time = time.time()
    return reply