import os
import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from jinja2 import Template
import markdown
import argparse

from src.github_client import yield_active_ai_repos
from src.summarizer import check_for_daily_update, generate_global_summary

def generate_rss_feed(repos, target_date_str, base_dir: Path):
    """Generates an RSS feed for the updates."""
    template_path = base_dir / "site" / "rss_template.xml"
    with open(template_path, "r", encoding="utf-8") as f:
        rss_template = f.read()

    t = Template(rss_template)
    t.globals['markdown'] = lambda text: markdown.markdown(text, extensions=['extra']) if text else ''
    return t.render(
        repos=repos,
        build_date=datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    )

def generate_site(target_date_str: str = None, force: bool = False):
    if not target_date_str:
        target_date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
    print(f"🚀 Starting Real-Time AI Changelog Aggregation for {target_date_str}...")
    
    BASE_DIR = Path(__file__).parent.parent
    site_dir = BASE_DIR / "site"
    site_dir.mkdir(exist_ok=True)
    
    # Check if already generated
    archive_dir = site_dir / "archives"
    archive_dir.mkdir(exist_ok=True)
    archive_path = archive_dir / f"{target_date_str}.html"
    
    if archive_path.exists() and not force:
        print(f"✨ Site for {target_date_str} is already up to date. Skipping generation.")
        print("💡 Use --force to regenerate.")
        return
    
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
        summary_data = check_for_daily_update(repo_data['changelog'], dates_to_check[0])
        
        found_date = dates_to_check[0]
        is_fresh = True
        
        if not summary_data:
            # Check Yesterday (Fallback)
            print(f"  -> No update for {dates_to_check[0]}. Checking {dates_to_check[1]}...")
            summary_data = check_for_daily_update(repo_data['changelog'], dates_to_check[1])
            found_date = dates_to_check[1]
            is_fresh = False
            
        if summary_data:
            print(f"  ✅ FOUND UPDATE for {found_date}!")
            
            # Prepare repo object
            repo_entry = {
                "name": repo_data['name'],
                "full_name": repo_data['full_name'],
                "description": repo_data['description'],
                "url": repo_data['url'],
                "stars": repo_data['stars'],
                "summary_data": summary_data,
                "update_date": found_date,
                "is_fresh": is_fresh,
                "title": summary_data.get('title', 'Update'),
                # For RSS
                "pub_date": datetime.strptime(found_date, "%Y-%m-%d").strftime("%a, %d %b %Y 00:00:00 GMT")
            }
            
            if is_fresh:
                primary_list.append(repo_entry)
            else:
                print(f"  ⚠️ Found older update for {found_date}")
                secondary_list.append(repo_entry)
        else:
             print("  -> No recent updates found.")

        # Check termination condition (including both fresh and recent updates)
        total_secured = len(primary_list) + len(secondary_list)
        if total_secured >= MAX_REPOS:
            print(f"🎉 Secured {MAX_REPOS} updates (Fresh: {len(primary_list)}, Recent: {len(secondary_list)})!")
            break
            
        if checked_count >= CHECK_LIMIT:
            print("⚠️ Reached check limit. Stopping search.")
            break
            
    # Combine lists
    # Prioritize fresh updates
    final_repos = primary_list.copy()
    
    if len(final_repos) < MAX_REPOS:
        needed = MAX_REPOS - len(final_repos)
        print(f"ℹ️ Filling {needed} slots with older updates...")
        final_repos.extend(secondary_list[:needed])

    # 2. Generate Global Summary
    global_summary_data = None
    if final_repos:
        print(f"🎨 Generating dashboard with {len(final_repos)} updates...")
        print("🧠 Generating global ecosystem analysis...")
        global_summary_data = generate_global_summary(final_repos)
    else:
        print("⚠️ No updates found at all (Fresh or Recent). Skipping global summary.")

    try:
        template_file = site_dir / "template.html"
        with open(template_file, "r", encoding="utf-8") as f:
            template_content = f.read()
            template = Template(template_content)
            template.globals['markdown'] = lambda text: markdown.markdown(text, extensions=['extra']) if text else ''
            
        html = template.render(
            title="AI Changelog Insights",
            date=target_date_str,
            repos=final_repos,
            global_summary_data=global_summary_data,
            generated_at=datetime.now(timezone.utc).strftime("%H:%M UTC")
        )
        
        # Write Main Index
        index_file = site_dir / "index.html"
        with open(index_file, "w", encoding="utf-8") as f:
            f.write(html)
            
        # Write Archive
        with open(archive_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"📦 Archived to {archive_path}")
        
        # Write RSS Feed
        rss_xml = generate_rss_feed(final_repos, target_date_str, BASE_DIR)
        rss_file = site_dir / "feed.xml"
        with open(rss_file, "w", encoding="utf-8") as f:
            f.write(rss_xml)
        print("📡 RSS Feed generated.")
            
        # 3. Save metadata
        meta_file = site_dir / "meta.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump({
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "target_date": target_date_str,
                "repo_count": len(final_repos),
                "duration_seconds": time.time() - start_time
            }, f, indent=2)
            
        print("✅ Site updated successfully!")
        
    except Exception as e:
        print(f"❌ Error generating site: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="Target date YYYY-MM-DD", default=None)
    parser.add_argument("--force", help="Force regeneration", action="store_true")
    args = parser.parse_args()
    
    generate_site(args.date, args.force)
