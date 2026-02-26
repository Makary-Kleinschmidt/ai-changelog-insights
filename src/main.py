import os
import json
import time
from datetime import datetime, timezone, timedelta
from jinja2 import Template
import markdown
import argparse

try:
    from github_client import yield_active_ai_repos
    from summarizer import check_for_daily_update, generate_global_summary
except ImportError:
    from src.github_client import yield_active_ai_repos
    from src.summarizer import check_for_daily_update, generate_global_summary

def format_global_summary_html(data: dict) -> str:
    """
    Formats the global summary JSON into HTML.
    Ecosystem summary is collapsed by default and parsed through markdown
    to convert [text](url) links into clickable <a> tags.
    """
    html = []
    
    html.append("<div class='global-summary-card'>")
    html.append("<h2>🌍 Daily Ecosystem Report</h2>")
    
    # Render ecosystem summary through markdown for clickable hyperlinks
    raw_summary = data.get('ecosystem_summary', '')
    rendered_summary = markdown.markdown(raw_summary, extensions=['extra'])
    
    # Wrap in collapsed <details> — user opens it if they want
    html.append("<details class='ecosystem-details'>")
    html.append("<summary class='ecosystem-toggle'>📖 Read Ecosystem Analysis</summary>")
    html.append(f"<div class='ecosystem-overview'>{rendered_summary}</div>")
    html.append("</details>")
    
    if data.get('synergies'):
        html.append("<h3>🔗 Synergies & Connections</h3>")
        html.append("<ul>")
        for item in data['synergies']:
            desc = markdown.markdown(item.get('description', ''), extensions=['extra'])
            html.append(f"<li><strong>{item.get('title')}</strong>: {desc}</li>")
        html.append("</ul>")
        
    if data.get('potential_issues'):
        html.append("<h3>⚠️ Potential Issues & Conflicts</h3>")
        html.append("<ul>")
        for item in data['potential_issues']:
            desc = markdown.markdown(item.get('description', ''), extensions=['extra'])
            html.append(f"<li><strong>{item.get('title')}</strong>: {desc}</li>")
        html.append("</ul>")
        
    html.append("</div>")
    return "\n".join(html)

def format_summary_html(data: dict) -> str:
    """
    Converts the JSON summary data into the HTML format expected by the template.
    Uses new schema: whats_new (list), why_important (str), try_it_out (3 levels).
    """
    html = []
    
    # What's New — bullet point list of facts
    html.append("<h3>🚀 What's New</h3>")
    whats_new = data.get('whats_new', [])
    if whats_new and isinstance(whats_new, list):
        html.append("<ul>")
        for item in whats_new:
            html.append(f"<li>{item}</li>")
        html.append("</ul>")
    else:
        # Fallback for old-format responses that still use 'summary'
        summary = data.get('summary', '')
        if summary:
            html.append(f"<p>{summary}</p>")
    
    # Why It's Important — context paragraph
    why_important = data.get('why_important', '')
    if why_important:
        html.append("<h3>💡 Why It's Important</h3>")
        rendered_why = markdown.markdown(why_important, extensions=['extra'])
        html.append(rendered_why)
    elif data.get('impact'):
        # Fallback for old-format responses
        html.append("<h3>💡 Why It's Important</h3>")
        html.append("<ul>")
        for item in data['impact']:
            name = item.get('name', 'Feature')
            desc = item.get('description', '')
            html.append(f"<li><strong>{name}</strong>: {desc}</li>")
        html.append("</ul>")
        
    # Try It Out — 3 collapsed levels
    if data.get('try_it_out'):
        tio = data['try_it_out']
        lang = tio.get('language', '')
        
        levels = ['beginner', 'intermediate', 'advanced']
        level_icons = {'beginner': '🟢', 'intermediate': '🟡', 'advanced': '🔴'}
        
        has_levels = any(isinstance(tio.get(lvl), dict) for lvl in levels)
        
        if has_levels:
            html.append("<h3>🛠️ Try It Out</h3>")
            for lvl in levels:
                lvl_data = tio.get(lvl)
                if not isinstance(lvl_data, dict):
                    continue
                label = lvl_data.get('label', lvl.capitalize())
                code = lvl_data.get('code', '')
                icon = level_icons.get(lvl, '⚪')
                if code:
                    html.append(f"<details class='try-it-level'>")
                    html.append(f"<summary>{icon} {label}</summary>")
                    html.append(f"<pre><code class=\"language-{lang}\">{code}</code></pre>")
                    html.append("</details>")
        else:
            # Fallback: single code block (old format)
            code = tio.get('code', '')
            if code:
                html.append("<h3>🛠️ Try It Out</h3>")
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

def generate_site(target_date_str: str = None, force: bool = False):
    if not target_date_str:
        target_date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
    print(f"🚀 Starting Real-Time AI Changelog Aggregation for {target_date_str}...")
    
    # Check if already generated
    archive_path = f"site/archives/{target_date_str}.html"
    if os.path.exists(archive_path) and not force:
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

    # 2. Generate Global Summary
    print(f"🎨 Generating dashboard with {len(final_repos)} updates...")
    
    global_summary_html = ""
    if final_repos:
        print("🧠 Generating global ecosystem analysis...")
        global_summary_data = generate_global_summary(final_repos)
        if global_summary_data:
             global_summary_html = format_global_summary_html(global_summary_data)
    
    try:
        with open("site/template.html", "r", encoding="utf-8") as f:
            template = Template(f.read())
            
        html = template.render(
            title="AI Changelog Insights",
            date=target_date_str,
            repos=final_repos,
            global_summary=global_summary_html,
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
    parser.add_argument("--force", help="Force regeneration", action="store_true")
    args = parser.parse_args()
    
    generate_site(args.date, args.force)
