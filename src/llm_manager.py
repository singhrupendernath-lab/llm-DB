from langchain_openai import ChatOpenAI
from src.config import Config

class LLMManager:
    def __init__(self, model_name=None):
        self.api_key = Config.LLM_API_KEY
        self.base_url = Config.LLM_BASE_URL
        self.model_name = model_name if model_name else Config.LLM_MODEL

    def get_llm(self):
        # Using ChatOpenAI as a generic interface for OpenAI-compatible APIs (like Ollama, vLLM, etc.)
        return ChatOpenAI(
            model=self.model_name,
            openai_api_key=self.api_key,
            openai_api_base=self.base_url
        )
