import config
import logging
import ollama
from openai import OpenAI


logger = logging.getLogger(__name__)

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
        )
    return _clients[provider]

def _call_provider(provider, model, messages):
    if provider == "ollama":
        response = ollama.chat(
            model=model,
            messages=messages,
            options={"num_ctx": config.NUM_CTX},
        )
        return response.message.content
    
    client = _get_client(provider)
    response = client.chat.completions.create(model=model, messages=messages)
    return response.choices[0].message.content

def chat(role, messages):
    attempts = config.AGENT_ROLES[role]["providers"]
    last_error = None
    for attempt in attempts:
        provider = attempt["provider"]
        model = attempt["model"]
        try:
            return _call_provider(provider, model, messages)
        except Exception as e:
            last_error = e
            logger.warning(f"{provider} failed ({e}); trying next fallback...")
    raise RuntimeError(f"All providers failed for role '{role}'. Last error: {last_error}")