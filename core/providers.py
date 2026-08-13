import config
import logging
import ollama
from dataclasses import dataclass
from openai import OpenAI


logger = logging.getLogger(__name__)

@dataclass
class ChatResponse:
    content: str | None
    tool_calls: list | None = None

PROVIDER_CONFIG = {
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "api_key": config.DEEPSEEK_API_KEY,
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "api_key": config.GROQ_API_KEY,
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key": config.GEMINI_API_KEY,
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": config.OPENROUTER_API_KEY,
    },
}

_clients = {}

def _get_client(provider):
    if provider not in _clients:
        settings = PROVIDER_CONFIG[provider]
        _clients[provider] = OpenAI(
            base_url=settings["base_url"],
            api_key=settings["api_key"],
            timeout=config.PROVIDER_TIMEOUT,
            max_retries=0,  # our own fallback chain already handles a failed provider
        )
    return _clients[provider]

def _call_provider(provider, model, messages, tools=None, temperature=None):
    # Omitted rather than sent as null, so a caller without a temperature keeps the provider default.
    sampling = {} if temperature is None else {"temperature": temperature}
    if provider == "ollama":
        response = ollama.chat(
            model=model,
            messages=messages,
            options={"num_ctx": config.NUM_CTX, **sampling},
        )
        return ChatResponse(content=response.message.content, tool_calls=None)

    client = _get_client(provider)
    response = client.chat.completions.create(model=model, messages=messages, tools=tools, **sampling)
    message = response.choices[0].message
    return ChatResponse(content=message.content, tool_calls=message.tool_calls)

def chat(role, messages, tools=None):
    attempts = config.AGENT_ROLES[role]["providers"]
    temperature = config.AGENT_ROLES[role].get("temperature")
    last_error = None
    for attempt in attempts:
        provider = attempt["provider"]
        model = attempt["model"]
        try:
            return _call_provider(provider, model, messages, tools=tools, temperature=temperature)
        except Exception as e:
            last_error = e
            logger.warning(f"{provider} failed ({e}); trying next fallback...")
    raise RuntimeError(f"All providers failed for role '{role}'. Last error: {last_error}")