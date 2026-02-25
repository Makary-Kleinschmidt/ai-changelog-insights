import os
import json
import time
from datetime import datetime, timezone
from github import Github, Auth, RateLimitExceededException
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Iterator, Dict, Optional
import base64

def get_github_client():
    token = os.getenv("GITHUB_TOKEN")
    if token:
        auth = Auth.Token(token)
        return Github(auth=auth)
    print("Warning: No GITHUB_TOKEN found. Using unauthenticated requests (Rate limit: 60/hr).")
    return Github()

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type((RateLimitExceededException, ConnectionError))
)
def search_repos_with_retry(query, sort="updated", order="desc", page=0):
    g = get_github_client()
    return g.search_repositories(query=query, sort=sort, order=order).get_page(page)

def yield_active_ai_repos() -> Iterator[Dict]:
    """
    Yields active AI repositories one by one, fetching fresh data.
    """
    g = get_github_client()
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Query for Python AI repos updated today
    # "pushed:>YYYY-MM-DD" ensures we only look at recently active repos
    query = f"topic:ai language:python pushed:>={today_str}"
    
    page = 0
    seen_repos = set()
    
    while True:
        try:
            print(f"Fetching page {page} of active AI repos...")
            repos = search_repos_with_retry(query, sort="updated", order="desc", page=page)
            
            if not repos:
                print("No more repositories found.")
                break
                
            for repo in repos:
                if repo.id in seen_repos:
                    continue
                seen_repos.add(repo.id)
                
                # Fetch fresh changelog content
                changelog_content = get_changelog_content(repo)
                
                yield {
                    "repo_obj": repo,
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "url": repo.html_url,
                    "stars": repo.stargazers_count,
                    "updated_at": repo.updated_at.isoformat(),
                    "changelog": changelog_content
                }
                
            page += 1
            
        except RateLimitExceededException:
            print("Rate limit exceeded. Waiting...")
            time.sleep(60) # Simple wait if retry failed
        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            break

def get_changelog_content(repo) -> Optional[str]:
    # Optimization: Get root file list ONCE
    try:
        contents = repo.get_contents("")
        root_files = {file.name.lower(): file for file in contents}
    except Exception as e:
        # print(f"    Error fetching file list: {e}")
        return None

    # Priority list of filenames
    filenames = ["changelog.md", "history.md", "releases.md", "changes.md",
                 "changelog.rst", "history.rst", "releases.rst", "changes.rst",
                 "changelog.txt", "history.txt", "releases.txt", "changes.txt"]
    
    for filename in filenames:
        if filename in root_files:
            try:
                content_file = root_files[filename]
                if content_file.size > 1000000:
                    continue
                return base64.b64decode(content_file.content).decode("utf-8")
            except:
                continue
            
    return None
