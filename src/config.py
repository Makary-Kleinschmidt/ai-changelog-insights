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
    -   If YES: Summarize it.
    -   If NO: Output ONLY "NO_UPDATE" (do not explain, do not summarize older entries).
2.  **Analyze Impact**: For each major change (Feature, Fix, Breaking), explain:
    -   **What it means**: Translate technical jargon into plain English.
    -   **Why it matters**: How does this improve the developer experience or application performance?
    -   **Actionable Step**: Provide a concrete thing for the user to try.

**IMPORTANT**: 
- Do NOT state "No update found for {target_date}" in your summary. 
- Do NOT mention "The latest entry is..." or "This release is from...".
- Just present the content of the update as if it is fresh news.
- Start directly with the "What's New" content.

Output Format (Markdown):

### 🚀 What's New
[Concise summary of the update content]

### 💡 Why It Matters
- **[Feature/Fix Name]**: [Explanation of impact]
- **[Feature/Fix Name]**: [Explanation of impact]

### 🛠️ Try It Out
[Code snippet or command to use the new feature, if applicable]

---
If NO entry is found for {target_date}, output ONLY: "NO_UPDATE".
"""
