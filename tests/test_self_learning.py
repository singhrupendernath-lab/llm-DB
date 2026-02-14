import unittest
from unittest.mock import MagicMock, patch
from src.oracle_bot import OracleBot
import time

class TestSelfLearning(unittest.TestCase):
    @patch('src.vector_manager.Chroma')
    @patch('src.vector_manager.HuggingFaceEmbeddings')
    def test_self_learning_integration(self, mock_embeddings, mock_chroma):
        # Mock dependencies
        mock_db_manager = MagicMock()
        mock_llm_manager = MagicMock()
        mock_llm = MagicMock()
        mock_llm_manager.get_llm.return_value = mock_llm
        mock_llm_manager.llm_type = "openai"
        mock_db_manager.get_usable_table_names.return_value = []

        # Initialize Bot
        bot = OracleBot(mock_db_manager, mock_llm_manager)

        # 1. Simulate asking a question
        question1 = "What is the secret code?"
        answer1 = "The secret code is 12345."

        # Mock agent executor
        mock_executor = MagicMock()
        mock_executor.invoke.return_value = {"output": answer1, "intermediate_steps": []}

        with patch.object(bot, '_create_agent_executor', return_value=mock_executor):
            bot.ask(question1)

        # Wait a bit for the background thread to call add_documents
        max_retries = 10
        while max_retries > 0 and not bot.vector_manager.chat_db.add_documents.called:
            time.sleep(0.1)
            max_retries -= 1

        # Verify add_chat_interaction was called
        self.assertTrue(bot.vector_manager.chat_db.add_documents.called)
        print("First interaction saved successfully.")

        # 2. Simulate asking a follow-up
        question2 = "Tell me the secret code again."

        # Mock retrieval from ChromaDB
        mock_doc = MagicMock()
        mock_doc.page_content = f"Question: {question1}\nAnswer: {answer1}"
        bot.vector_manager.chat_db.similarity_search_by_vector.return_value = [mock_doc]

        # Mock agent executor for second call
        mock_executor2 = MagicMock()
        mock_executor2.invoke.return_value = {"output": answer1, "intermediate_steps": []}

        with patch.object(bot, '_create_agent_executor', return_value=mock_executor2) as mock_create_executor:
            bot.ask(question2)

            # Verify that extra_context was passed to _create_agent_executor
            args, kwargs = mock_create_executor.call_args
            self.assertIn('extra_context', kwargs)
            self.assertIn("Learned Knowledge", kwargs['extra_context'])
            self.assertIn(answer1, kwargs['extra_context'])
            print("Self-learning context retrieval verified.")

if __name__ == '__main__':
    unittest.main()
