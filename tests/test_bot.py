import unittest
from unittest.mock import MagicMock, patch
from src.db_manager import DBManager
from src.llm_manager import LLMManager
from src.oracle_bot import OracleBot

class TestOracleBot(unittest.TestCase):
    @patch('src.oracle_bot.create_sql_agent')
    @patch('src.llm_manager.ChatOpenAI')
    def test_ask(self, mock_chat_openai, mock_create_sql_agent):
        # Mock LLM and Agent
        mock_llm = MagicMock()
        mock_chat_openai.return_value = mock_llm
        
        mock_agent_executor = MagicMock()
        mock_create_sql_agent.return_value = mock_agent_executor
        
        db_manager = DBManager(db_type="sqlite")
        llm_manager = LLMManager(llm_type="openai")
        bot = OracleBot(db_manager, llm_manager)
        
        # Mocking the agent's invoke method
        mock_agent_executor.invoke.return_value = {
            "output": "There are 2 employees in Sales.",
            "intermediate_steps": []
        }
        
        result = bot.ask("How many employees are in Sales?")
        self.assertEqual(result["answer"], "There are 2 employees in Sales.")
        mock_agent_executor.invoke.assert_called_once()

if __name__ == "__main__":
    unittest.main()
