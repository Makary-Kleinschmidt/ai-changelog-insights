import os
import json
import time
from datetime import datetime, timezone, timedelta
from github import Github, Auth, RateLimitExceededException, UnknownObjectException
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Iterator, Dict, Optional
import base64

try:
    from . import config
except ImportError:
    import config

def get_github_client():
    token = os.getenv("GH_ACCESS_TOKEN")
    if token:
        auth = Auth.Token(token)
        return Github(auth=auth)
    print("Warning: No GH_ACCESS_TOKEN found. Using unauthenticated requests (Rate limit: 60/hr).")
    return Github()

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type((RateLimitExceededException, ConnectionError))
)
def get_repo_with_retry(repo_name):
    g = get_github_client()
    return g.get_repo(repo_name)

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type((RateLimitExceededException, ConnectionError))
)
def search_repos_with_retry(query, sort="stars", order="desc", page=0):
    g = get_github_client()
    return g.search_repositories(query=query, sort=sort, order=order).get_page(page)

def yield_vip_repos() -> Iterator[Dict]:
    """
    Yields VIP repositories first.
    """
    print("🌟 Checking VIP Repositories...")
    for repo_name in config.VIP_REPOS:
        try:
            repo = get_repo_with_retry(repo_name)
            content = get_changelog_content(repo) or get_releases_content(repo)
            
            yield {
                "repo_obj": repo,
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "url": repo.html_url,
                "stars": repo.stargazers_count,
                "updated_at": repo.updated_at.isoformat(),
                "changelog": content
            }
        except UnknownObjectException:
            print(f"  -> Repo {repo_name} not found.")
        except Exception as e:
            print(f"  -> Error fetching VIP {repo_name}: {e}")

def yield_active_ai_repos(days_lookback=3) -> Iterator[Dict]:
    """
    Yields active AI repositories, prioritized by stars.
    """
    # 1. Yield VIPs first
    yield from yield_vip_repos()
    
    # 2. Search for others
    g = get_github_client()
    
    start_date = datetime.now(timezone.utc) - timedelta(days=days_lookback)
    start_date_str = start_date.strftime("%Y-%m-%d")
    
    # Query: Updated recently, High Stars, Decent Forks (Quality Filter)
    # We remove 'sort=updated' and use 'sort=stars' to find the GIANTS that updated recently
    query = f"topic:ai language:python pushed:>={start_date_str} stars:>500 forks:>50"
    
    page = 0
    seen_repos = set(config.VIP_REPOS) # Don't re-yield VIPs
    
    while True:
        try:
            print(f"Fetching page {page} of POPULAR AI repos (updated since {start_date_str})...")
            repos = search_repos_with_retry(query, sort="stars", order="desc", page=page)
            
            if not repos:
                print("No more repositories found.")
                break
                
            for repo in repos:
                if repo.full_name in seen_repos:
                    continue
                seen_repos.add(repo.full_name)
                
                # Fetch content (Changelog OR Releases)
                content = get_changelog_content(repo) or get_releases_content(repo)
                
                yield {
                    "repo_obj": repo,
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "url": repo.html_url,
                    "stars": repo.stargazers_count,
                    "updated_at": repo.updated_at.isoformat(),
                    "changelog": content
                }
                
            page += 1
            
        except RateLimitExceededException:
            print("Rate limit exceeded. Waiting...")
            time.sleep(60)
        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            break

def get_changelog_content(repo) -> Optional[str]:
    try:
        contents = repo.get_contents("")
        root_files = {file.name.lower(): file for file in contents}
    except Exception as e:
        return None

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

def get_releases_content(repo) -> Optional[str]:
    """
    Fetches the last 5 releases and formats them as a pseudo-changelog.
    """
    try:
        releases = repo.get_releases()[:5]
        if not releases:
            return None
            
        pseudo_changelog = "# Changelog (from GitHub Releases)\n\n"
        for release in releases:
            date_str = release.published_at.strftime("%Y-%m-%d")
            pseudo_changelog += f"## [{date_str}] {release.title or release.tag_name}\n"
            pseudo_changelog += f"{release.body}\n\n"
            
        return pseudo_changelog
    except:
        return None
