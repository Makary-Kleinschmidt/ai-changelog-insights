import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
REWRITE_MODEL = "arcee-ai/trinity-large-preview:free"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Strict check for updates from "today"
CHANGELOG_UPDATE_CHECK_PROMPT = """You are a changelog parser.
Your task is to check if the provided CHANGELOG content has an entry dated **{target_date}** (YYYY-MM-DD).

Input CHANGELOG:
{content}

Instructions:
1. Look for headers or entries explicitly dated {target_date}.
2. If found, extract ONLY that entry and summarize it into a concise paragraph highlighting key features, fixes, or breaking changes.
3. If NO entry is found for {target_date}, output ONLY: "NO_UPDATE".
4. If the changelog uses version numbers without dates, look for the LATEST version. If context implies it was released today (e.g. based on surrounding text), summarize it. Otherwise, return "NO_UPDATE".

Output Format:
- If update found: [Summary Paragraph]
- If no update: NO_UPDATE
"""
