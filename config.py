from dotenv import load_dotenv
import os

load_dotenv()

# --- Agent Configuration ---
AGENT_NAME = "Tabris"

# --- Model Configuration ---
GENERAL_MODEL = "llama3.1:8b"
CODE_MODEL = "qwen2.5-coder:7b"

# --- Role → Provider mapping ---
AGENT_ROLES = {
    "general": {"provider": "ollama", "model": "llama3.1:8b"},
    "code":    {"provider": "deepseek", "model": "deepseek-chat"},
    "router":  {"provider": "groq",     "model": "llama-3.1-8b-instant"},
}

# --- Memory Configuration ---
MEMORY_PATH = "memory.md"

# --- Conversation Configuration ---
MAX_HISTORY = 10    # number of recent exchanges (user+assistant) sent to the model
NUM_CTX = 8192      # token context window Ollama should use (overrides its small default)

# --- API Keys ---
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")