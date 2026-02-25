import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
REWRITE_MODEL = "arcee-ai/trinity-large-preview:free"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# VIP Repositories to always check
VIP_REPOS = [
    "All-Hands-AI/OpenHands",
    "Significant-Gravitas/AutoGPT",
    "langchain-ai/langchain",
    "run-llama/llama_index",
    "huggingface/transformers",
    "anthropics/anthropic-sdk-python",
    "google/generative-ai-python",
    "microsoft/autogen",
    "crewAIInc/crewAI"
]

# Actionable Insights Prompt
CHANGELOG_UPDATE_CHECK_PROMPT = """You are an expert developer advocate.
Your task is to analyze the provided CHANGELOG for an entry dated **{target_date}** (YYYY-MM-DD).

Input CHANGELOG:
{content}

Instructions:
1.  **Identify Updates**: Check if there is an entry strictly matching {target_date}.
    -   If NO: Output ONLY the JSON: `{{"update_found": false}}`.
    -   If YES: Extract the update details and format as JSON.
2.  **Analyze Impact**:
    -   **What's New**: A concise summary of the update.
    -   **Why It Matters**: A list of key changes with their impact.
    -   **Try It Out**: A code snippet or command to use the new feature.

Output Format (JSON):
{{
  "update_found": true,
  "title": "Release Title or Version",
  "summary": "Concise summary of what is new...",
  "impact": [
    {{
      "name": "Feature Name",
      "description": "Why it matters..."
    }},
    {{
      "name": "Another Feature",
      "description": "Impact explanation..."
    }}
  ],
  "try_it_out": {{
    "language": "python",
    "code": "print('Hello World')"
  }}
}}
"""
