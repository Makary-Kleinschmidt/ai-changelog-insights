import unittest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.summarizer import check_for_daily_update, generate_global_summary

class TestSummarizer(unittest.TestCase):
    @patch('src.summarizer._call_gemini_with_fallback')
    def test_check_for_daily_update_not_found_locally(self, mock_gemini):
        result = check_for_daily_update("Some random log", "2024-01-01")
        self.assertIsNone(result)
        mock_gemini.assert_not_called()

    @patch('src.summarizer._call_gemini_with_fallback')
    def test_check_for_daily_update_found(self, mock_gemini):
        mock_response = MagicMock()
        mock_response.text = '{"update_found": true, "title": "Test Title"}'
        mock_gemini.return_value = mock_response

        # Target date must be in content to bypass local optimization
        result = check_for_daily_update("Some log 2024-01-01 update", "2024-01-01")
        self.assertIsNotNone(result)

    @patch('src.summarizer._call_gemini_with_fallback')
    def test_generate_global_summary(self, mock_gemini):
        mock_response = MagicMock()
        mock_response.text = '{"ecosystem_summary": "Ecosystem is great"}'
        mock_gemini.return_value = mock_response

        # Need to mock the get_gemini_client inside summarizer to not return None
        with patch('src.summarizer._get_gemini_client', return_value=MagicMock()):
            repos_data = [{"name": "repo1", "title": "update", "description": "desc"}]
            result = generate_global_summary(repos_data)
            self.assertIsNotNone(result)

if __name__ == '__main__':
    unittest.main()
