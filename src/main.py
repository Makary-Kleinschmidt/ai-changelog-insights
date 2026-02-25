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

def format_summary_html(data: dict) -> str:
    """
    Converts the JSON summary data into the HTML format expected by the template.
    """
    html = []
    
    # What's New
    html.append(f"<h3>🚀 What's New</h3>")
    html.append(f"<p>{data.get('summary', '')}</p>")
    
    # Why It Matters
    if data.get('impact'):
        html.append(f"<h3>💡 Why It Matters</h3>")
        html.append("<ul>")
        for item in data['impact']:
            name = item.get('name', 'Feature')
            desc = item.get('description', '')
            html.append(f"<li><strong>{name}</strong>: {desc}</li>")
        html.append("</ul>")
        
    # Try It Out
    if data.get('try_it_out'):
        tio = data['try_it_out']
        lang = tio.get('language', '')
        code = tio.get('code', '')
        if code:
            html.append(f"<h3>🛠️ Try It Out</h3>")
            # Using pre/code block. 
            # Note: We are manually building HTML, so we need to escape generic content if we were paranoid,
            # but usually LLM output is controlled. 
            # Ideally use markdown for code to get highlighting if we process it later, 
            # but here we are constructing final HTML.
            # Let's wrap in markdown code block and use markdown lib to render it to ensure syntax highlighting works?
            # Or just raw <pre><code>. The existing CSS targets pre/code.
            html.append(f"<pre><code class=\"language-{lang}\">{code}</code></pre>")
            
    return "\n".join(html)

def generate_rss_feed(repos, target_date_str):
    """Generates an RSS feed for the updates."""
    rss_template = """<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>AI Changelog Insights</title>
  <link>https://ai-changelog-insights.github.io</link>
  <description>Daily AI updates, summarized for developers.</description>
  <atom:link href="https://ai-changelog-insights.github.io/feed.xml" rel="self" type="application/rss+xml" />
  <language>en-us</language>
  <lastBuildDate>{{ build_date }}</lastBuildDate>
  {% for repo in repos %}
  <item>
    <title>{{ repo.name }} - {{ repo.title }}</title>
    <link>{{ repo.url }}</link>
    <description><![CDATA[
      {{ repo.summary_html }}
    ]]></description>
    <guid isPermaLink="false">{{ repo.full_name }}-{{ repo.update_date }}</guid>
    <pubDate>{{ repo.pub_date }}</pubDate>
  </item>
  {% endfor %}
</channel>
</rss>
"""
    t = Template(rss_template)
    return t.render(
        repos=repos,
        build_date=datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    )

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
            
            # Convert JSON to HTML
            summary_html = format_summary_html(summary_data)
            
            # Prepare repo object
            repo_entry = {
                "name": repo_data['name'],
                "full_name": repo_data['full_name'],
                "description": repo_data['description'],
                "url": repo_data['url'],
                "stars": repo_data['stars'],
                "summary_html": summary_html,
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
        
        # Write Main Index
        with open("site/index.html", "w", encoding="utf-8") as f:
            f.write(html)
            
        # Write Archive
        os.makedirs("site/archives", exist_ok=True)
        archive_path = f"site/archives/{target_date_str}.html"
        with open(archive_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"📦 Archived to {archive_path}")
        
        # Write RSS Feed
        rss_xml = generate_rss_feed(final_repos, target_date_str)
        with open("site/feed.xml", "w", encoding="utf-8") as f:
            f.write(rss_xml)
        print("📡 RSS Feed generated.")
            
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
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="Target date YYYY-MM-DD", default=None)
    args = parser.parse_args()
    
    generate_site(args.date)
