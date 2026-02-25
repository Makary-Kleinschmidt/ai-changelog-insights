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
    MAX_REPOS = 9
    CHECK_LIMIT = 200 # Increased limit
    
    # Dates to check: Target Date, then previous days if needed
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    dates_to_check = [target_date_str]
    
    # Add previous 2 days as fallback
    for i in range(1, 3):
        prev_date = target_date - timedelta(days=i)
        dates_to_check.append(prev_date.strftime("%Y-%m-%d"))
        
    print(f"📅 Strategy: Check {dates_to_check[0]} first, then fallback to {dates_to_check[1:]} if needed.")
    
    primary_list = []
    secondary_list = []
    
    checked_count = 0
    repo_generator = yield_active_ai_repos(days_lookback=3)
    
    start_time = time.time()
    
    for repo_data in repo_generator:
        checked_count += 1
        print(f"[{checked_count}/{CHECK_LIMIT}] Checking {repo_data['full_name']} (Stars: {repo_data['stars']})...")
        
        if not repo_data['changelog']:
            print("  -> No CHANGELOG or Releases found. Skipping.")
            continue
            
        # Check Today
        summary_today = check_for_daily_update(repo_data['changelog'], dates_to_check[0])
        
        if summary_today and summary_today != "NO_UPDATE":
            print(f"  ✅ FOUND UPDATE for {dates_to_check[0]}!")
            summary_html = markdown.markdown(summary_today, extensions=['extra', 'codehilite'])
            
            primary_list.append({
                "name": repo_data['name'],
                "full_name": repo_data['full_name'],
                "description": repo_data['description'],
                "url": repo_data['url'],
                "stars": repo_data['stars'],
                "summary_html": summary_html,
                "update_date": dates_to_check[0],
                "is_fresh": True
            })
        else:
            # Check Yesterday (Fallback)
            print(f"  -> No update for {dates_to_check[0]}. Checking {dates_to_check[1]}...")
            summary_yesterday = check_for_daily_update(repo_data['changelog'], dates_to_check[1])
            
            if summary_yesterday and summary_yesterday != "NO_UPDATE":
                print(f"  ⚠️ FOUND OLDER UPDATE for {dates_to_check[1]}")
                summary_html = markdown.markdown(summary_yesterday, extensions=['extra', 'codehilite'])
                
                secondary_list.append({
                    "name": repo_data['name'],
                    "full_name": repo_data['full_name'],
                    "description": repo_data['description'],
                    "url": repo_data['url'],
                    "stars": repo_data['stars'],
                    "summary_html": summary_html,
                    "update_date": dates_to_check[1],
                    "is_fresh": False
                })
            else:
                 print("  -> No recent updates found.")

        # Check termination condition
        if len(primary_list) >= MAX_REPOS:
            print(f"🎉 Secured {MAX_REPOS} fresh updates!")
            break
            
        if checked_count >= CHECK_LIMIT:
            print("⚠️ Reached check limit. Stopping search.")
            break
            
    # Combine lists
    # Prioritize fresh updates
    final_repos = primary_list
    
    if len(final_repos) < MAX_REPOS:
        needed = MAX_REPOS - len(final_repos)
        print(f"ℹ️ Filling {needed} slots with older updates...")
        final_repos.extend(secondary_list[:needed])

    # 2. Generate HTML
    print(f"🎨 Generating dashboard with {len(final_repos)} updates...")
    
    try:
        with open("site/template.html", "r", encoding="utf-8") as f:
            template = Template(f.read())
            
        html = template.render(
            title="AI Changelog Insights",
            date=target_date_str,
            repos=final_repos,
            generated_at=datetime.now(timezone.utc).strftime("%H:%M UTC")
        )
        
        with open("site/index.html", "w", encoding="utf-8") as f:
            f.write(html)
            
        # 3. Save metadata
        with open("site/meta.json", "w", encoding="utf-8") as f:
            json.dump({
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "target_date": target_date_str,
                "repo_count": len(final_repos),
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
