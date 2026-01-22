from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFacePipeline, HuggingFaceEndpoint
from langchain_community.llms import LlamaCpp
from transformers import AutoModelForCausalLM, AutoModelForSeq2SeqLM, AutoTokenizer, pipeline, AutoConfig
from huggingface_hub import hf_hub_download
from src.config import Config
import torch
import os

class LLMManager:
    def __init__(self, llm_type=None, model_name=None):
        self.llm_type = llm_type if llm_type else Config.LLM_TYPE
        self.api_key = Config.LLM_API_KEY
        self.base_url = Config.LLM_BASE_URL
        self.model_name = model_name if model_name else (Config.HF_MODEL_ID if self.llm_type in ["huggingface", "huggingface_api"] else Config.LLM_MODEL)

    def get_llm(self):
        if self.llm_type == "openai":
            return ChatOpenAI(
                model=self.model_name,
                openai_api_key=self.api_key,
                openai_api_base=self.base_url,
                temperature=0
            )
        elif self.llm_type == "huggingface":
            print(f"Loading Hugging Face model locally: {self.model_name}...")

            try:
                hf_config = AutoConfig.from_pretrained(self.model_name, token=Config.HF_TOKEN, trust_remote_code=True)
                model_type = hf_config.model_type
            except Exception:
                model_type = "unknown"

            task = Config.HF_TASK
            if not task:
                if model_type in ["t5", "flan-t5", "bart", "marian"]:
                    task = "text2text-generation"
                else:
                    task = "text-generation"

            print(f"Detected task: {task}")
            device = 0 if torch.cuda.is_available() else -1

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

            if hasattr(model, 'config'):
                model.config.use_cache = False

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

        elif self.llm_type == "huggingface_api":
            print(f"Using Hugging Face Inference API for model: {self.model_name}...")

            if not Config.HF_TOKEN:
                print("Warning: HF_TOKEN not provided. API calls will likely fail.")

            # Use conversational task by default for Chat/Instruct models if not specified
            task = Config.HF_TASK
            if not task:
                if "instruct" in self.model_name.lower() or "chat" in self.model_name.lower():
                    task = "text-generation" # Endpoint usually prefers this or conversational
                else:
                    task = "text-generation"

            return HuggingFaceEndpoint(
                repo_id=self.model_name,
                huggingfacehub_api_token=Config.HF_TOKEN,
                temperature=0.1,
                max_new_tokens=1024,
                task=task,
                timeout=300
            )

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

            return LlamaCpp(
                model_path=model_path,
                n_ctx=4096,
                n_threads=os.cpu_count() or 4,
                temperature=0,
                verbose=True
            )
        else:
            raise ValueError(f"Unsupported LLM type: {self.llm_type}")
