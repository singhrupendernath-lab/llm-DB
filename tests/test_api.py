import unittest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os
import sys

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api import app

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch('src.api.bot')
    def test_health(self, mock_bot):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")

    @patch('src.api.bot')
    def test_ask(self, mock_bot):
        # Setup mock bot return value
        mock_bot.ask.return_value = {
            "answer": "There are 10 students.",
            "sql_queries": ["SELECT COUNT(*) FROM students"]
        }

        response = self.client.post(
            "/ask",
            json={"question": "how many students?"}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["answer"], "There are 10 students.")
        self.assertEqual(data["sql_queries"], ["SELECT COUNT(*) FROM students"])

    @patch('src.api.bot')
    def test_reports(self, mock_bot):
        mock_bot.reports_manager.reports = {"R1": {"name": "Report 1"}}

        response = self.client.get("/reports")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"R1": {"name": "Report 1"}})

if __name__ == "__main__":
    unittest.main()
