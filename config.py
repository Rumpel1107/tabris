from dotenv import load_dotenv
import os

load_dotenv()

# --- Agent Configuration ---
AGENT_NAME = "Tabris"
LANGUAGE_NAMES = {"es": "Spanish", "en": "English"}

# --- Role → Provider mapping ---
AGENT_ROLES = {
    "general": {
        "description": "general questions, conversation, explanations, anything not code",
        "temperature": 0.7,
        "providers": [
            {"provider": "deepseek", "model": "deepseek-chat"},
            {"provider": "gemini",   "model": "gemini-3.5-flash-lite"},
            {"provider": "groq",     "model": "openai/gpt-oss-120b"},
        ],
    },
    "code": {
        "description": "programming, debugging, scripts, technical code, functions",
        "temperature": 0.2,
        "providers": [
            {"provider": "openrouter", "model": "z-ai/glm-5.2:free"},
            {"provider": "deepseek",   "model": "deepseek-chat"},
            {"provider": "groq",       "model": "openai/gpt-oss-120b"},
        ],
    },
    "memory": {
        "description": "background memory distillation, not user-facing",
        "internal": True,   # the system calls this role directly; a user message is never routed to it
        "temperature": 0.0,
        "providers": [
            {"provider": "deepseek", "model": "deepseek-chat"},
            {"provider": "gemini",   "model": "gemini-3.5-flash-lite"},
            {"provider": "groq",     "model": "openai/gpt-oss-120b"},
        ],
    },
    "router": {
        "description": "classifies user intent into one of the available roles",
        "temperature": 0.0,
        "providers": [
            {"provider": "groq",     "model": "openai/gpt-oss-20b"},
            {"provider": "gemini",   "model": "gemini-3.5-flash-lite"},
            {"provider": "deepseek", "model": "deepseek-chat"},
        ],
    },
}

# --- Memory Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PERSONA_PATH = os.path.join(BASE_DIR, "prompts", "persona.md")
DATA_DIR = os.getenv("TABRIS_DATA_DIR", os.path.join(BASE_DIR, "data"))
DB_PATH = os.path.join(DATA_DIR, f"{AGENT_NAME.lower()}.db")
CLIENT_ID_PATH = os.path.join(DATA_DIR, f"{AGENT_NAME.lower()}_client_id")
EXPORTS_DIR = os.path.join(DATA_DIR, "exports")
MEMORY_TRIGGER_EXCHANGES = 15
MEMORY_TRIGGER_SECONDS = 1200
MEMORY_MAX_NEW_FACTS = 5
MEMORY_MAX_RETIRE_IDS = 15  # retiring is reversible and bounded to facts already shown to the model; adding is the injection-relevant half

# --- Database Configuration ---
DB_BUSY_TIMEOUT_MS = 5000   # ms a connection waits for a locked DB before failing (0 = fail instantly)
BACKUPS_KEPT = 7            # how many dated copies the backup script keeps before deleting the oldest

# --- Account Linking Configuration ---
LINK_CODE_TTL_SECONDS = 300   # how long a channel-linking code stays valid before expiring (5 min)
ACCOUNT_GRACE_DAYS = 14       # days between deactivating an account and deleting its data for good

# --- Conversation Configuration ---
MAX_HISTORY = 10    # number of recent exchanges (user+assistant) sent to the model
PROVIDER_TIMEOUT = 15   # seconds to wait for a provider before giving up and trying the next fallback
MAX_TOOL_ROUNDS = 10       # safety net: give up if a turn keeps asking for tools instead of answering
MESSAGE_MAX_CHARS = 4000   # reject incoming user messages longer than this (channel-agnostic guard)
MESSAGE_RATE_MAX = 10       # token-bucket capacity: max messages a user can burst
MESSAGE_RATE_SECONDS = 60   # window the bucket refills over (MAX tokens per this many seconds)

# --- Channel Limits ---
DISCORD_MESSAGE_LIMIT = 2000   # hard limit Discord enforces per outgoing message; longer replies are split

# --- Search Configuration ---
SEARCH_PROVIDERS = ["tavily", "duckduckgo"]   # ordered; search() tries each in turn, falls through on failure

# --- API Keys ---
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# --- Logging Configuration ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
