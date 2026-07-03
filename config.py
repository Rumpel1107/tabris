from dotenv import load_dotenv
import os

load_dotenv()

# --- Agent Configuration ---
AGENT_NAME = "Tabris"
USER_NAME = "Rumpel"
LANGUAGE = "en"
LANGUAGE_NAMES = {"es": "Spanish", "en": "English"}

# --- Role → Provider mapping ---
AGENT_ROLES = {
    "general": {
        "description": "general questions, conversation, explanations, anything not code",
        "providers": [
            {"provider": "gemini", "model": "gemini-2.5-flash"},
            {"provider": "groq",   "model": "llama-3.3-70b-versatile"},
            {"provider": "ollama", "model": "llama3.1:8b"},
        ],
    },
    "code": {
        "description": "programming, debugging, scripts, technical code, functions",
        "providers": [
            {"provider": "deepseek",   "model": "deepseek-chat"},
            {"provider": "openrouter", "model": "z-ai/glm-5.2"},
            {"provider": "groq",       "model": "moonshotai/kimi-k2-instruct"},
            {"provider": "ollama",     "model": "llama3.1:8b"},
        ],
    },
    "router": {
        "description": "classifies user intent into one of the available roles",
        "providers": [
            {"provider": "groq",   "model": "llama-3.1-8b-instant"},
            {"provider": "gemini", "model": "gemini-2.5-flash"},
            {"provider": "ollama", "model": "llama3.1:8b"},
        ],
    },
}

# --- Memory Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PERSONA_PATH = os.path.join(BASE_DIR, "persona.md")
DB_PATH = os.path.join(BASE_DIR, f"{AGENT_NAME.lower()}.db")
CLIENT_ID_PATH = os.path.join(BASE_DIR, f"{AGENT_NAME.lower()}_client_id")
MEMORY_TRIGGER_EXCHANGES = 5
MEMORY_TRIGGER_SECONDS = 300

# --- Conversation Configuration ---
MAX_HISTORY = 10    # number of recent exchanges (user+assistant) sent to the model
NUM_CTX = 8192      # token context window Ollama should use (overrides its small default)
PROVIDER_TIMEOUT = 15   # seconds to wait for a provider before giving up and trying the next fallback

# --- API Keys ---
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# --- Logging Configuration ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
