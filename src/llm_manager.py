from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFacePipeline
from langchain_community.llms import LlamaCpp
from transformers import AutoModelForCausalLM, AutoModelForSeq2SeqLM, AutoTokenizer, pipeline, AutoConfig
from huggingface_hub import hf_hub_download
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

            # Load model config
            try:
                hf_config = AutoConfig.from_pretrained(self.model_name, token=Config.HF_TOKEN, trust_remote_code=True)
                model_type = hf_config.model_type
            except Exception:
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
            tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                token=Config.HF_TOKEN,
                trust_remote_code=True,
                model_max_length=Config.HF_MAX_LENGTH
            )

            model_kwargs = {
                "token": Config.HF_TOKEN,
                "trust_remote_code": True
            }

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

            # Force disable cache
            if hasattr(model, 'config'):
                model.config.use_cache = False

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

        elif self.llm_type == "llamacpp":
            model_path = Config.LOCAL_MODEL_PATH

            if not model_path:
                print(f"Downloading GGUF model from {Config.HF_GGUF_REPO}...")
                model_path = hf_hub_download(
                    repo_id=Config.HF_GGUF_REPO,
                    filename=Config.HF_GGUF_FILE,
                    token=Config.HF_TOKEN
                )
                print(f"Model downloaded to: {model_path}")

            print(f"Loading LlamaCpp model from: {model_path}")

            # Parameters for LlamaCpp
            return LlamaCpp(
                model_path=model_path,
                n_ctx=4096,
                n_threads=os.cpu_count() or 4,
                temperature=0,
                verbose=True
            )
        else:
            raise ValueError(f"Unsupported LLM type: {self.llm_type}")
