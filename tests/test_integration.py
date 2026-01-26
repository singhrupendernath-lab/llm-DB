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
            "conversational",
            model=mock_causal.from_pretrained.return_value,
            tokenizer=mock_tokenizer.from_pretrained.return_value,
            device=-1,
            max_new_tokens=256,
            repetition_penalty=1.1,
            truncation=True
        )

    @patch('src.llm_manager.HuggingFaceEndpoint')
    @patch('src.llm_manager.ChatHuggingFace')
    def test_llm_manager_huggingface_api(self, mock_chat_hf, mock_hf_endpoint):
        Config.LLM_TYPE = "huggingface_api"
        Config.HF_MODEL_ID = "meta-llama/Llama-3.1-8B-Instruct"
        Config.HF_TOKEN = "test-token"
        Config.HF_TASK = None

        mock_endpoint_instance = MagicMock()
        # We need the mock to look like a HuggingFaceEndpoint to pass validation if it were real,
        # but since we mock ChatHuggingFace too, we just need to ensure it's called.
        mock_hf_endpoint.return_value = mock_endpoint_instance

        llm_manager = LLMManager(llm_type="huggingface_api")
        llm_manager.get_llm()

        mock_hf_endpoint.assert_called_with(
            repo_id="meta-llama/Llama-3.1-8B-Instruct",
            huggingfacehub_api_token="test-token",
            temperature=0.1,
            max_new_tokens=1024,
            task="conversational",
            timeout=300,
            stop_sequences=["Observation:", "\nObservation:"]
        )
        mock_chat_hf.assert_called_with(llm=mock_endpoint_instance)

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

    @patch('src.oracle_bot.ReportsManager')
    @patch('src.oracle_bot.create_sql_agent')
    def test_predefined_report(self, mock_create_agent, mock_reports_manager):
        mock_db_manager = MagicMock()
        mock_llm_manager = MagicMock()
        mock_llm = MagicMock()
        mock_llm_manager.get_llm.return_value = mock_llm

        # Setup report mock
        mock_rm_instance = mock_reports_manager.return_value
        mock_rm_instance.find_report_id.return_value = "AT1201"
        mock_rm_instance.get_report.return_value = {
            "name": "Test Report",
            "query": "SELECT * FROM test"
        }
        mock_rm_instance.format_query.return_value = "SELECT * FROM test"
        mock_rm_instance.get_missing_variables.return_value = []

        bot = OracleBot(mock_db_manager, mock_llm_manager)

        # Mock DB response
        mock_db_manager.get_db.return_value.run.return_value = "[('data',)]"

        # Mock LLM response for formatting
        mock_llm.invoke.return_value.content = "Formatted Data"

        result = bot.ask("I want AT1201 reports")

        self.assertEqual(result["answer"], "Formatted Data")
        self.assertEqual(result["sql_queries"], ["SELECT * FROM test"])
        self.assertEqual(result["report_id"], "AT1201")
        mock_rm_instance.log_execution.assert_called_once()

    @patch('src.oracle_bot.ReportsManager')
    @patch('src.oracle_bot.create_sql_agent')
    def test_predefined_report_empty(self, mock_create_agent, mock_reports_manager):
        mock_db_manager = MagicMock()
        mock_llm_manager = MagicMock()

        # Setup report mock
        mock_rm_instance = mock_reports_manager.return_value
        mock_rm_instance.find_report_id.return_value = "AT1201"
        mock_rm_instance.get_report.return_value = {
            "name": "Test Report",
            "query": "SELECT * FROM test"
        }
        mock_rm_instance.format_query.return_value = "SELECT * FROM test"
        mock_rm_instance.get_missing_variables.return_value = []

        bot = OracleBot(mock_db_manager, mock_llm_manager)

        # Mock DB response as empty
        mock_db_manager.get_db.return_value.run.return_value = "[]"

        result = bot.ask("I want AT1201 reports")

        self.assertEqual(result["answer"], "No records found for the requested criteria.")
        self.assertEqual(result["sql_queries"], ["SELECT * FROM test"])

    @patch('src.oracle_bot.ReportsManager')
    @patch('src.oracle_bot.create_sql_agent')
    def test_predefined_report_missing_vars(self, mock_create_agent, mock_reports_manager):
        mock_db_manager = MagicMock()
        mock_llm_manager = MagicMock()

        # Setup report mock
        mock_rm_instance = mock_reports_manager.return_value
        mock_rm_instance.find_report_id.return_value = "AT1201"
        mock_rm_instance.get_report.return_value = {
            "name": "Test Report",
            "query": "SELECT * FROM t WHERE d=:date"
        }
        mock_rm_instance.get_missing_variables.return_value = ["date"]

        bot = OracleBot(mock_db_manager, mock_llm_manager)

        result = bot.ask("give me AT1201")

        self.assertIn("requires additional information: date", result["answer"])
        self.assertEqual(result["sql_queries"], [])

    def test_reports_manager_parameter_extraction(self):
        from src.reports_manager import ReportsManager
        rm = ReportsManager()

        # Mock reports for testing extraction
        rm.reports = {
            "AT1201": {"query": "SELECT * FROM t WHERE d='{date}'"}
        }

        query = rm.format_query("AT1201", "I want AT1201 for 2024-05-15")
        self.assertEqual(query, "SELECT * FROM t WHERE d='2024-05-15'")

    def test_reports_manager_range_extraction(self):
        from src.reports_manager import ReportsManager
        rm = ReportsManager()

        rm.reports = {
            "BAL01": {"query": "SELECT * FROM accounts WHERE bal BETWEEN {min_balance} AND {max_balance}"}
        }

        query = rm.format_query("BAL01", "Show BAL01 with balance between 100 and 500")
        self.assertEqual(query, "SELECT * FROM accounts WHERE bal BETWEEN 100 AND 500")

    def test_reports_manager_colon_syntax(self):
        from src.reports_manager import ReportsManager
        rm = ReportsManager()

        rm.reports = {
            "AT1202": {"query": "SELECT * FROM t WHERE d = :date"}
        }

        query = rm.format_query("AT1202", "give me AT1202 for 2024-09-01")
        # Now we expect quotes
        self.assertEqual(query, "SELECT * FROM t WHERE d = '2024-09-01'")

    @patch('src.db_manager.create_engine')
    @patch('src.db_manager.SQLDatabase')
    def test_oracle_semicolon_stripping(self, mock_sql_db_class, mock_create_engine):
        mock_db_instance = MagicMock()
        mock_sql_db_class.return_value = mock_db_instance
        def mock_run(command, *args, **kwargs):
            return f"Executed: {command}"
        mock_db_instance.run = mock_run

        db_manager = DBManager(db_type="oracle")
        result = db_manager.get_db().run("SELECT * FROM users;")
        self.assertEqual(result, "Executed: SELECT * FROM users")

    def test_reports_manager_missing_vars(self):
        from src.reports_manager import ReportsManager
        rm = ReportsManager()

        rm.reports = {
            "AT1201": {"query": "SELECT * FROM t WHERE d='{date}'"}
        }

        missing = rm.get_missing_variables("AT1201", "give me AT1201")
        self.assertEqual(missing, ["date"])

        missing_none = rm.get_missing_variables("AT1201", "AT1201 for 2024-01-01")
        self.assertEqual(missing_none, [])

if __name__ == '__main__':
    unittest.main()
