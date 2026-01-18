import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    ORACLE_USER = os.getenv("ORACLE_USER")
    ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD")
    ORACLE_DSN = os.getenv("ORACLE_DSN")
    
    LLM_API_KEY = os.getenv("LLM_API_KEY", "no-key-required")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
    LLM_MODEL = os.getenv("LLM_MODEL", "llama3")
    
    USE_SQLITE = os.getenv("USE_SQLITE", "True").lower() == "true"
    SQLITE_PATH = os.getenv("SQLITE_PATH", "demo.db")
