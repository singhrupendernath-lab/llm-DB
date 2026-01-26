import os
from dotenv import load_dotenv

load_dotenv(override=True)

class Config:
    # Database selection: 'sqlite', 'oracle', or 'mysql'
    DB_TYPE = os.getenv("DB_TYPE", "sqlite").lower()

    # Oracle connection details
    ORACLE_USER = os.getenv("ORACLE_USER")
    ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD")
    ORACLE_DSN = os.getenv("ORACLE_DSN")
    
    # MySQL connection details
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
    MYSQL_DB = os.getenv("MYSQL_DB", "demo")

    # SQLite connection details
    SQLITE_PATH = os.getenv("SQLITE_PATH", "demo.db")

    # Optional: comma-separated list of tables to include
    INCLUDE_TABLES = [t.strip() for t in os.getenv("INCLUDE_TABLES").split(",")] if os.getenv("INCLUDE_TABLES") else None

    # Legacy support for USE_SQLITE
    USE_SQLITE = os.getenv("USE_SQLITE", "True").lower() == "true"
    if DB_TYPE == "sqlite" and not USE_SQLITE:
        # If legacy USE_SQLITE is False, and DB_TYPE is still default sqlite,
        # assume they want Oracle (previous behavior)
        DB_TYPE = "oracle"

    # LLM selection: 'openai', 'huggingface', 'llamacpp', or 'huggingface_api'
    LLM_TYPE = os.getenv("LLM_TYPE", "openai").lower()

    # OpenAI/Generic API config
    LLM_API_KEY = os.getenv("LLM_API_KEY", "no-key-required")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
    LLM_MODEL = os.getenv("LLM_MODEL", "llama3")
    
    # Hugging Face config
    HF_MODEL_ID = os.getenv("HF_MODEL_ID", "Qwen/Qwen2.5-1.5B-Instruct")
    HF_TOKEN = os.getenv("HF_TOKEN")
    HF_MAX_LENGTH = int(os.getenv("HF_MAX_LENGTH", "2048"))
    HF_TASK = os.getenv("HF_TASK") # e.g., 'text-generation' or 'text2text-generation'

    # GGUF / LlamaCpp config
    HF_GGUF_REPO = os.getenv("HF_GGUF_REPO", "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF")
    HF_GGUF_FILE = os.getenv("HF_GGUF_FILE", "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf")
    LOCAL_MODEL_PATH = os.getenv("LOCAL_MODEL_PATH") # If set, skip download and use this path
