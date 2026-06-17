# --- Agent Configuration ---
AGENT_NAME = "Tabris"

# --- Model Configuration ---
GENERAL_MODEL = "llama3.1:8b"
CODE_MODEL = "qwen2.5-coder:7b"

# --- Memory Configuration ---
MEMORY_PATH = "memory.md"

# --- Conversation Configuration ---
MAX_HISTORY = 10    # number of recent exchanges (user+assistant) sent to the model
NUM_CTX = 8192      # token context window Ollama should use (overrides its small default)