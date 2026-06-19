import config
from openai import OpenAI

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
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",
    },
}

def chat(role, messages):
    role_config = config.AGENT_ROLES[role]
    provider = role_config["provider"]
    model = role_config["model"]

    settings = PROVIDER_CONFIG[provider]
    client = OpenAI(base_url=settings["base_url"], api_key=settings["api_key"])

    response = client.chat.completions.create(model=model, messages=messages)
    return response.choices[0].message.content