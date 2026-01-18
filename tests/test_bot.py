import unittest
from unittest.mock import MagicMock, patch
from src.db_manager import DBManager
from src.llm_manager import LLMManager
from src.oracle_bot import OracleBot

class TestOracleBot(unittest.TestCase):
    @patch('src.oracle_bot.SQLDatabaseChain')
    @patch('src.llm_manager.ChatOpenAI')
    def test_ask(self, mock_chat_openai, mock_db_chain_class):
        # Mock LLM and Chain
        mock_llm = MagicMock()
        mock_chat_openai.return_value = mock_llm
        
        mock_db_chain = MagicMock()
        mock_db_chain_class.from_llm.return_value = mock_db_chain
        
        db_manager = DBManager(db_type="sqlite")
        llm_manager = LLMManager(llm_type="openai")
        bot = OracleBot(db_manager, llm_manager)
        
        # Mocking the chain's invoke method
        mock_db_chain.invoke.return_value = {"result": "There are 2 employees in Sales."}
        
        result = bot.ask("How many employees are in Sales?")
        self.assertEqual(result, "There are 2 employees in Sales.")
        mock_db_chain.invoke.assert_called_once()

if __name__ == "__main__":
    unittest.main()
