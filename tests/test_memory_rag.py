import unittest
from unittest.mock import MagicMock, patch
from src.db_manager import DBManager
from src.llm_manager import LLMManager
from src.oracle_bot import OracleBot

class TestMemoryRAG(unittest.TestCase):

    @patch('src.vector_manager.Chroma')
    @patch('src.vector_manager.HuggingFaceEmbeddings')
    def test_memory_isolation(self, mock_embeddings, mock_chroma):
        mock_db_manager = MagicMock()
        mock_llm_manager = MagicMock()
        mock_llm_manager.get_llm.return_value = MagicMock()

        bot = OracleBot(mock_db_manager, mock_llm_manager)

        mem1 = bot._get_memory("user1")
        mem2 = bot._get_memory("user2")

        # Check they are different instances
        self.assertTrue(mem1 is not mem2)

        mem1.save_context({"input": "hello from user 1"}, {"output": "hi user 1"})

        # Check history isolation
        history1 = mem1.load_memory_variables({})['chat_history']
        history2 = mem2.load_memory_variables({})['chat_history']

        self.assertTrue(len(history1) > 0)
        self.assertEqual(len(history2), 0)
        print("Memory isolation verified.")

    @patch('src.vector_manager.Chroma')
    @patch('src.vector_manager.HuggingFaceEmbeddings')
    def test_rag_table_selection(self, mock_embeddings, mock_chroma):
        mock_db_manager = MagicMock()
        mock_llm_manager = MagicMock()

        mock_doc = MagicMock()
        mock_doc.page_content = "CREATE TABLE students ..."
        mock_doc.metadata = {"table_name": "students"}
        mock_chroma.return_value.similarity_search.return_value = [mock_doc]

        bot = OracleBot(mock_db_manager, mock_llm_manager)
        tables = bot.vector_manager.get_relevant_tables("who are the students?")

        self.assertIn("students", tables)
        print("RAG table selection verified.")

if __name__ == '__main__':
    unittest.main()
