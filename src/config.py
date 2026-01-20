import os
from dotenv import load_dotenv

load_dotenv()

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

    # Legacy support for USE_SQLITE
    USE_SQLITE = os.getenv("USE_SQLITE", "True").lower() == "true"
    if DB_TYPE == "sqlite" and not USE_SQLITE:
        # If legacy USE_SQLITE is False, and DB_TYPE is still default sqlite,
        # assume they want Oracle (previous behavior)
        DB_TYPE = "oracle"

    # LLM selection: 'openai' or 'huggingface'
    LLM_TYPE = os.getenv("LLM_TYPE", "openai").lower()

    # OpenAI/Generic API config
    LLM_API_KEY = os.getenv("LLM_API_KEY", "no-key-required")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
    LLM_MODEL = os.getenv("LLM_MODEL", "llama3")
    
    # Hugging Face config
    HF_MODEL_ID = os.getenv("HF_MODEL_ID", "google/flan-t5-large")
    HF_TOKEN = os.getenv("HF_TOKEN")
