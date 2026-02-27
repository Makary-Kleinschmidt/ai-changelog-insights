import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
import os
import json

# Add project root to path so we can import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock modules before importing src.main to avoid import errors
sys.modules['src.github_client'] = MagicMock()
sys.modules['src.summarizer'] = MagicMock()

# Now import main
from src.main import generate_site

class TestFlow(unittest.TestCase):
    
    @patch('src.main.yield_active_ai_repos')
    @patch('src.main.check_for_daily_update')
    @patch('builtins.open', new_callable=mock_open, read_data="{{title}}")
    @patch('src.main.json.dump')
    def test_generate_site_flow(self, mock_json_dump, mock_file_open, mock_check_update, mock_yield_repos):
        print("Testing generate_site flow...")
        
        # Mock repo data
        repo1 = {
            "name": "repo1",
            "full_name": "org/repo1",
            "description": "desc1",
            "url": "http://url1",
            "stars": 100,
            "updated_at": "2024-01-01",
            "changelog": "## [2024-01-01] Update"
        }
        repo2 = {
            "name": "repo2",
            "full_name": "org/repo2", 
            "description": "desc2",
            "url": "http://url2",
            "stars": 200,
            "updated_at": "2024-01-01",
            "changelog": "Old changelog"
        }
        
        # Generator yields 2 repos
        mock_yield_repos.return_value = iter([repo1, repo2])
        
        # First repo has update, second doesn't
        mock_check_update.side_effect = [
            {
                "whats_new": ["Feature 1", "Feature 2"],
                "why_important": "It is important.",
                "try_it_out": {
                    "language": "python",
                    "beginner": {"code": "print('hello')"},
                    "intermediate": {"code": "def hello(): pass"},
                    "advanced": {"code": "class Hello: pass"}
                }
            }, 
            None,
            None
        ]
        
        # Run function
        generate_site(target_date_str="2024-01-01")
        
        # Verify check_update called twice
        self.assertEqual(mock_check_update.call_count, 3)
        
        # Verify result was written to json
        # mock_json_dump.call_args[0][0] is the data dict
        saved_data = mock_json_dump.call_args[0][0]
        self.assertEqual(saved_data['repo_count'], 1)
        self.assertEqual(saved_data['target_date'], "2024-01-01")
        
        print("Test passed!")

if __name__ == '__main__':
    unittest.main()
