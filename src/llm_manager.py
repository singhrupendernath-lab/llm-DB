from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFacePipeline
from transformers import AutoModelForCausalLM, AutoModelForSeq2SeqLM, AutoTokenizer, pipeline, AutoConfig
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
            return ChatOpenAI(
                model=self.model_name,
                openai_api_key=self.api_key,
                openai_api_base=self.base_url,
                temperature=0
            )
        elif self.llm_type == "huggingface":
            print(f"Loading Hugging Face model: {self.model_name}...")

            # Load model config to determine the task
            hf_config = AutoConfig.from_pretrained(self.model_name, token=Config.HF_TOKEN, trust_remote_code=True)

            # Determine task
            task = Config.HF_TASK
            if not task:
                if hf_config.model_type in ["t5", "flan-t5", "bart", "marian"]:
                    task = "text2text-generation"
                else:
                    task = "text-generation"

            print(f"Detected task: {task}")

            # Simple check for GPU availability
            device = 0 if torch.cuda.is_available() else -1

            # Explicitly load model and tokenizer to avoid auto-detection issues in LangChain
            model_kwargs = {
                "token": Config.HF_TOKEN,
                "trust_remote_code": True,
            }

            tokenizer = AutoTokenizer.from_pretrained(self.model_name, **model_kwargs)
            if task == "text2text-generation":
                model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name, **model_kwargs)
            else:
                model = AutoModelForCausalLM.from_pretrained(self.model_name, **model_kwargs)

            pipe = pipeline(
                task,
                model=model,
                tokenizer=tokenizer,
                device=device,
                max_new_tokens=1024,
                repetition_penalty=1.1,
                truncation=True
            )

            # Use HuggingFacePipeline with the explicit pipeline object
            return HuggingFacePipeline(pipeline=pipe)
        else:
            raise ValueError(f"Unsupported LLM type: {self.llm_type}")
