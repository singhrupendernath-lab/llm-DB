import unittest
from unittest.mock import patch, MagicMock
from src.db_manager import DBManager
from src.llm_manager import LLMManager
from src.oracle_bot import OracleBot
from src.config import Config

class TestManagers(unittest.TestCase):

    @patch('src.db_manager.create_engine')
    @patch('src.db_manager.SQLDatabase')
    def test_db_manager_mysql(self, mock_sql_db, mock_create_engine):
        Config.DB_TYPE = "mysql"
        Config.MYSQL_USER = "testuser"
        Config.MYSQL_PASSWORD = "testpassword"
        Config.MYSQL_HOST = "testhost"
        Config.MYSQL_PORT = "3306"
        Config.MYSQL_DB = "testdb"

        db_manager = DBManager(db_type="mysql")
        expected_url = "mysql+pymysql://testuser:testpassword@testhost:3306/testdb"
        mock_create_engine.assert_called_with(expected_url)

    @patch('src.llm_manager.ChatOpenAI')
    def test_llm_manager_openai(self, mock_chat_openai):
        Config.LLM_TYPE = "openai"
        Config.LLM_MODEL = "gpt-3.5-turbo"
        Config.LLM_API_KEY = "testkey"
        Config.LLM_BASE_URL = "https://api.openai.com/v1"

        llm_manager = LLMManager(llm_type="openai")
        llm_manager.get_llm()

        mock_chat_openai.assert_called_with(
            model="gpt-3.5-turbo",
            openai_api_key="testkey",
            openai_api_base="https://api.openai.com/v1",
            temperature=0
        )

    @patch('src.llm_manager.AutoConfig')
    @patch('src.llm_manager.AutoModelForCausalLM')
    @patch('src.llm_manager.AutoTokenizer')
    @patch('src.llm_manager.pipeline')
    @patch('src.llm_manager.HuggingFacePipeline')
    def test_llm_manager_huggingface(self, mock_hf_pipeline, mock_pipeline, mock_tokenizer, mock_causal, mock_autoconfig):
        Config.LLM_TYPE = "huggingface"
        Config.HF_MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"

        mock_config = MagicMock()
        mock_config.model_type = "qwen2"
        mock_autoconfig.from_pretrained.return_value = mock_config

        llm_manager = LLMManager(llm_type="huggingface")
        llm_manager.get_llm()

        mock_tokenizer.from_pretrained.assert_called()
        mock_pipeline.assert_called_with(
            "text-generation",
            model=mock_causal.from_pretrained.return_value,
            tokenizer=mock_tokenizer.from_pretrained.return_value,
            device=-1,
            max_new_tokens=512,
            repetition_penalty=1.1,
            truncation=True
        )

    @patch('src.llm_manager.HuggingFaceEndpoint')
    def test_llm_manager_huggingface_api(self, mock_hf_endpoint):
        Config.LLM_TYPE = "huggingface_api"
        Config.HF_MODEL_ID = "meta-llama/Llama-3.1-8B-Instruct"
        Config.HF_TOKEN = "test-token"
        Config.HF_TASK = None

        llm_manager = LLMManager(llm_type="huggingface_api")
        llm_manager.get_llm()

        # Should use 'conversational' task for 'Instruct' models
        mock_hf_endpoint.assert_called_with(
            repo_id="meta-llama/Llama-3.1-8B-Instruct",
            huggingfacehub_api_token="test-token",
            temperature=0.1,
            max_new_tokens=1024,
            task="conversational",
            timeout=300
        )

    @patch('src.llm_manager.LlamaCpp')
    @patch('src.llm_manager.hf_hub_download')
    def test_llm_manager_llamacpp(self, mock_download, mock_llamacpp):
        Config.LLM_TYPE = "llamacpp"
        Config.HF_GGUF_REPO = "repo"
        Config.HF_GGUF_FILE = "file.gguf"
        Config.LOCAL_MODEL_PATH = None

        mock_download.return_value = "/path/to/file.gguf"

        llm_manager = LLMManager(llm_type="llamacpp")
        llm_manager.get_llm()

        mock_download.assert_called_with(
            repo_id="repo",
            filename="file.gguf",
            token=Config.HF_TOKEN
        )
        mock_llamacpp.assert_called()

    @patch('src.oracle_bot.create_sql_agent')
    def test_oracle_bot(self, mock_create_sql_agent):
        mock_db_manager = MagicMock()
        mock_llm_manager = MagicMock()
        mock_db_manager.db_type = "sqlite"

        bot = OracleBot(mock_db_manager, mock_llm_manager)

        mock_create_sql_agent.assert_called()

        # Mocking result
        mock_create_sql_agent.return_value.invoke.return_value = {
            "output": "Result",
            "intermediate_steps": []
        }

        result = bot.ask("how many students?")
        self.assertEqual(result["answer"], "Result")

if __name__ == '__main__':
    unittest.main()
