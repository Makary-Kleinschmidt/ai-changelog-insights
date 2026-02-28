import unittest
from unittest.mock import patch, mock_open
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# We already have test_flow.py but we can add an extra test for main.
from src.main import generate_site

class TestMain(unittest.TestCase):
    @patch('src.main.yield_active_ai_repos')
    @patch('src.main.check_for_daily_update')
    @patch('src.main.generate_global_summary')
    @patch('builtins.open', new_callable=mock_open, read_data="{{title}}")
    @patch('src.main.json.dump')
    def test_generate_site_skips_if_exists_no_force(self, mock_json, mock_file, mock_global_summary, mock_check, mock_yield):
        with patch('src.main.Path.exists', return_value=True):
            generate_site("2024-01-01", force=False)
            mock_yield.assert_not_called()

    @patch('src.main.yield_active_ai_repos')
    @patch('src.main.check_for_daily_update')
    @patch('src.main.generate_global_summary')
    @patch('builtins.open', new_callable=mock_open, read_data="{{title}}")
    @patch('src.main.json.dump')
    def test_generate_site_force(self, mock_json, mock_file, mock_global_summary, mock_check, mock_yield):
        with patch('src.main.Path.exists', return_value=True):
            mock_yield.return_value = iter([])
            generate_site("2024-01-01", force=True)
            mock_yield.assert_called()

if __name__ == '__main__':
    unittest.main()
