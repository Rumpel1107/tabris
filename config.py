from dotenv import load_dotenv
import os

load_dotenv()

# --- Agent Configuration ---
AGENT_NAME = "Tabris"
LANGUAGE = "es"

# --- Role → Provider mapping ---
AGENT_ROLES = {
    "general": [
        {"provider": "gemini", "model": "gemini-2.5-flash"},
        {"provider": "groq",   "model": "llama-3.3-70b-versatile"},
        {"provider": "ollama", "model": "llama3.1:8b"},
    ],
    "code": [
        {"provider": "deepseek",   "model": "deepseek-chat"},
        {"provider": "openrouter", "model": "z-ai/glm-5.2"},
        {"provider": "groq",       "model": "moonshotai/kimi-k2-instruct"},
        {"provider": "ollama",     "model": "llama3.1:8b"},
    ],
    "router": [
        {"provider": "groq",   "model": "llama-3.1-8b-instant"},
        {"provider": "gemini", "model": "gemini-2.5-flash"},
        {"provider": "ollama", "model": "llama3.1:8b"},
    ],
}

# --- Memory Configuration ---
MEMORY_PATH = "memory.md"
DB_PATH = f"{AGENT_NAME.lower()}.db"

# --- Conversation Configuration ---
MAX_HISTORY = 10    # number of recent exchanges (user+assistant) sent to the model
NUM_CTX = 8192      # token context window Ollama should use (overrides its small default)

# --- API Keys ---
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")