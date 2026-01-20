import unittest
from unittest.mock import patch, MagicMock
from src.db_manager import DBManager
from llm_manager import LLMManager
from oracle_bot import OracleBot
from config import Config

class TestManagers(unittest.TestCase):

    @patch('src.db_manager.create_engine')
    @patch('src.db_manager.SQLDatabase')
    def test_db_manager_mysql(self, mock_sql_db, mock_create_engine):
        # Set config for MySQL
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

    @patch('src.llm_manager.AutoTokenizer')
    @patch('src.llm_manager.AutoModelForCausalLM')
    @patch('src.llm_manager.pipeline')
    @patch('src.llm_manager.HuggingFacePipeline')
    def test_llm_manager_huggingface(self, mock_hf_pipeline, mock_pipeline, mock_model, mock_tokenizer):
        Config.LLM_TYPE = "huggingface"
        Config.HF_MODEL_ID = "gpt2"

        llm_manager = LLMManager(llm_type="huggingface")
        llm_manager.get_llm()

        mock_tokenizer.from_pretrained.assert_called()
        mock_pipeline.assert_called_with(
            "text-generation",
            model="gpt2",
            tokenizer=mock_tokenizer.from_pretrained.return_value,
            device=-1,
            max_new_tokens=1024,
            token=Config.HF_TOKEN,
            trust_remote_code=True,
            repetition_penalty=1.1
        )

    @patch('src.oracle_bot.create_sql_agent')
    def test_oracle_bot(self, mock_create_sql_agent):
        mock_db_manager = MagicMock()
        mock_llm_manager = MagicMock()

        bot = OracleBot(mock_db_manager, mock_llm_manager)

        mock_create_sql_agent.assert_called()

        bot.ask("What is the total sales?")
        mock_create_sql_agent.return_value.invoke.assert_called()

if __name__ == '__main__':
    unittest.main()
