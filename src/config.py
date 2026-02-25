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
CHANGELOG_UPDATE_CHECK_PROMPT = """You are a Senior DevRel Engineer and Technical Writer.
Your task is to analyze the provided CHANGELOG for an entry dated **{target_date}** (YYYY-MM-DD).

Input CHANGELOG:
{content}

Instructions:
1.  **Identify Updates**: Check if there is an entry strictly matching {target_date}.
    -   If NO: Output ONLY the JSON: `{{"update_found": false}}`.
    -   If YES: Extract the update details and format as JSON.

2.  **Analyze for User Utility (CRITICAL)**:
    -   Users want to know **strictly what to do** with the update.
    -   Avoid abstract descriptions like "Improved performance" or "Fixed bugs". Be specific: "Fixed memory leak in vector search".
    -   **What's New**: A detailed technical summary.
    -   **Why It Matters**: Explain the practical benefit. "Faster queries" -> "Reduces latency by 50% for RAG pipelines".
    -   **Try It Out**: THIS IS THE MOST IMPORTANT SECTION. Provide a **valid, copy-pasteable code snippet** or CLI command that demonstrates the new feature.
        -   If it's a library (Python/JS), show a code example using the new API.
        -   If it's a tool, show the command line usage.
        -   If it's a bug fix, show the code that used to break and now works (or just the corrected usage).
        -   **Do not use placeholders** like `your_code_here` unless absolutely necessary. Make it a working example.

Output Format (JSON):
{{
  "update_found": true,
  "title": "Release Title/Version",
  "summary": "Technical summary of changes...",
  "impact": [
    {{
      "name": "Feature/Change Name",
      "description": "Specific, practical benefit..."
    }},
    {{
      "name": "Another Feature",
      "description": "..."
    }}
  ],
  "try_it_out": {{
    "language": "python",
    "code": "from library import new_feature\\n\\n# Real usage example\\nresult = new_feature.run(param='value')\\nprint(result)"
  }}
}}
"""
