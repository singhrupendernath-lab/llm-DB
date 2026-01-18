from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFacePipeline
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from src.config import Config
import torch

class LLMManager:
    def __init__(self, llm_type=None, model_name=None):
        self.llm_type = llm_type if llm_type else Config.LLM_TYPE
        self.api_key = Config.LLM_API_KEY
        self.base_url = Config.LLM_BASE_URL
        self.model_name = model_name if model_name else (Config.HF_MODEL_ID if self.llm_type == "huggingface" else Config.LLM_MODEL)

    def get_llm(self):
        if self.llm_type == "openai":
            # Using ChatOpenAI as a generic interface for OpenAI-compatible APIs (like Ollama, vLLM, etc.)
            return ChatOpenAI(
                model=self.model_name,
                openai_api_key=self.api_key,
                openai_api_base=self.base_url
            )
        elif self.llm_type == "huggingface":
            print(f"Loading Hugging Face model: {self.model_name}...")
            tokenizer = AutoTokenizer.from_pretrained(self.model_name, token=Config.HF_TOKEN)

            # Simple check for GPU availability
            device = 0 if torch.cuda.is_available() else -1

            pipe = pipeline(
                "text-generation",
                model=self.model_name,
                tokenizer=tokenizer,
                device=device,
                max_new_tokens=512,
                token=Config.HF_TOKEN
            )
            return HuggingFacePipeline(pipeline=pipe)
        else:
            raise ValueError(f"Unsupported LLM type: {self.llm_type}")
