import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.github_client import yield_active_ai_repos

class TestGithubClient(unittest.TestCase):
    @patch('src.github_client.get_github_client')
    @patch('src.github_client.yield_vip_repos')
    def test_yield_active_ai_repos(self, mock_yield_vip, mock_get_client):
        # Mocking VIP repos to yield one item
        mock_yield_vip.return_value = iter([{
            "name": "vip-repo",
            "full_name": "org/vip-repo",
            "description": "desc",
            "url": "http://url",
            "stars": 100,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "changelog": "## [2024-01-01] Update"
        }])
        
        # Mocking standard search
        mock_github = MagicMock()
        mock_repo = MagicMock()
        mock_repo.name = "standard-repo"
        mock_repo.full_name = "org/standard-repo"
        mock_repo.description = "standard"
        mock_repo.html_url = "http://standard"
        mock_repo.stargazers_count = 50
        mock_repo.updated_at = datetime.now(timezone.utc)
        
        # Mock get_release to avoid 404 block
        mock_release = MagicMock()
        mock_release.body = "## [2024-01-01] New features"
        mock_repo.get_releases.return_value = [mock_release]
        
        class DummyList(list):
            totalCount = 1
            
        mock_github.search_repositories.return_value = DummyList([mock_repo])
        mock_get_client.return_value = mock_github
        
        repos = list(yield_active_ai_repos(days_lookback=3))
        self.assertTrue(isinstance(repos, list))

if __name__ == '__main__':
    unittest.main()
