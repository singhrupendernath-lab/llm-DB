from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFacePipeline
from transformers import AutoModelForCausalLM, AutoModelForSeq2SeqLM, AutoTokenizer, pipeline, AutoConfig
from config import Config
import torch
import os

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

            try:
                # Load model config
                hf_config = AutoConfig.from_pretrained(self.model_name, token=Config.HF_TOKEN, trust_remote_code=True)
                model_type = hf_config.model_type
            except Exception as e:
                print(f"Warning: Could not load config for {self.model_name}: {e}")
                model_type = "unknown"

            # Determine task
            task = Config.HF_TASK
            if not task:
                if model_type in ["t5", "flan-t5", "bart", "marian"]:
                    task = "text2text-generation"
                else:
                    task = "text-generation"

            print(f"Detected task: {task}")

            # Device selection
            device = 0 if torch.cuda.is_available() else -1

            # Explicitly load tokenizer and model
            model_kwargs = {
                "token": Config.HF_TOKEN,
                "trust_remote_code": True
            }

            if Config.HF_GGUF_FILE:
                print(f"Loading GGUF file: {Config.HF_GGUF_FILE}")
                model_kwargs["gguf_file"] = Config.HF_GGUF_FILE

            try:
                tokenizer = AutoTokenizer.from_pretrained(
                    self.model_name,
                    token=Config.HF_TOKEN,
                    trust_remote_code=True,
                    model_max_length=Config.HF_MAX_LENGTH
                )

                if task == "text2text-generation":
                    model = AutoModelForSeq2SeqLM.from_pretrained(
                        self.model_name,
                        **model_kwargs
                    )
                else:
                    model = AutoModelForCausalLM.from_pretrained(
                        self.model_name,
                        **model_kwargs
                    )

                # Force disable cache to avoid 'DynamicCache' object has no attribute 'seen_tokens'
                if hasattr(model, 'config'):
                    model.config.use_cache = False

            except Exception as e:
                raise RuntimeError(
                    f"Failed to load model '{self.model_name}'. "
                    f"Error: {e}. \n"
                    "Tip: If using Llama-3, ensure you have accepted the license on Hugging Face "
                    "and provided a valid HF_TOKEN in your .env file."
                )

            # Create pipeline
            pipe = pipeline(
                task,
                model=model,
                tokenizer=tokenizer,
                device=device,
                max_new_tokens=512,
                repetition_penalty=1.1,
                truncation=True
            )

            return HuggingFacePipeline(pipeline=pipe)
        else:
            raise ValueError(f"Unsupported LLM type: {self.llm_type}")
