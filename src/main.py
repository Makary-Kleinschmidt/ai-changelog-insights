import os
import json
import time
from datetime import datetime, timezone, timedelta
from jinja2 import Template
import markdown
import argparse

try:
    from github_client import yield_active_ai_repos
    from summarizer import check_for_daily_update
except ImportError:
    from src.github_client import yield_active_ai_repos
    from src.summarizer import check_for_daily_update

def generate_site(target_date_str: str = None):
    if not target_date_str:
        target_date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
    print(f"🚀 Starting Real-Time AI Changelog Aggregation for {target_date_str}...")
    
    processed_repos = []
    MAX_REPOS = 10
    CHECK_LIMIT = 100 # Safety break to avoid infinite loops
    checked_count = 0
    
    # 1. Iterate through active repos
    repo_generator = yield_active_ai_repos()
    
    start_time = time.time()
    
    for repo_data in repo_generator:
        checked_count += 1
        print(f"[{checked_count}/{CHECK_LIMIT}] Checking {repo_data['full_name']} for updates on {target_date_str}...")
        
        # Check changelog content
        if not repo_data['changelog']:
            print("  -> No CHANGELOG file found. Skipping.")
            continue
            
        # Check for specific daily update via LLM
        daily_summary = check_for_daily_update(repo_data['changelog'], target_date_str)
        
        if daily_summary and daily_summary != "NO_UPDATE":
            print(f"  ✅ FOUND UPDATE for {repo_data['full_name']}!")
            
            # Convert markdown summary to HTML
            summary_html = markdown.markdown(daily_summary, extensions=['extra', 'codehilite'])
            
            processed_repos.append({
                "name": repo_data['name'],
                "full_name": repo_data['full_name'],
                "description": repo_data['description'],
                "url": repo_data['url'],
                "stars": repo_data['stars'],
                "summary_html": summary_html,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            if len(processed_repos) >= MAX_REPOS:
                print("🎉 Secured 10 distinct daily updates!")
                break
        else:
            print("  -> No entry found for target date.")
            
        if checked_count >= CHECK_LIMIT:
            print("⚠️ Reached check limit. Stopping search.")
            break

    # 2. Generate HTML
    print(f"🎨 Generating dashboard with {len(processed_repos)} updates...")
    
    try:
        with open("site/template.html", "r", encoding="utf-8") as f:
            template = Template(f.read())
            
        html = template.render(
            title="AI Changelog Insights",
            date=target_date_str,
            repos=processed_repos,
            generated_at=datetime.now(timezone.utc).strftime("%H:%M UTC")
        )
        
        with open("site/index.html", "w", encoding="utf-8") as f:
            f.write(html)
            
        # 3. Save metadata
        with open("site/meta.json", "w", encoding="utf-8") as f:
            json.dump({
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "target_date": target_date_str,
                "repo_count": len(processed_repos),
                "duration_seconds": time.time() - start_time
            }, f, indent=2)
            
        print("✅ Site updated successfully!")
        
    except Exception as e:
        print(f"❌ Error generating site: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="Target date YYYY-MM-DD", default=None)
    args = parser.parse_args()
    
    generate_site(args.date)
