import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
REWRITE_MODEL = "deepseek/deepseek-v3.2"
GH_ACCESS_TOKEN = os.getenv("GH_ACCESS_TOKEN")

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
    -   **Why It Matters**: Explain the practical benefit IN DEPTH. This section should be detailed and comprehensive (at least 3-4 sentences per item).
        -   Provide context on the problem being solved.
        -   Compare "before" vs "after" scenarios.
        -   Explain *why* this is important for the user's workflow or application.
        -   Example: Instead of just "Faster queries", say "Previously, vector search on large datasets could take seconds. This update introduces a new indexing algorithm that reduces latency by 50% for RAG pipelines, making real-time applications viable."
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

GLOBAL_SUMMARY_PROMPT = """You are a Senior AI Ecosystem Analyst.
Your task is to analyze a collection of daily updates from major AI libraries/tools and identify cross-cutting themes, synergies, and potential conflicts.

Updates for today:
{updates_json}

Instructions:
1.  **Analyze Synergies**: Look for connections between updates.
    -   Did multiple libraries add support for the same model (e.g., Llama 3)?
    -   Are there complementary features (e.g., LangChain adds a tool that AutoGPT can use)?
2.  **Identify Potential Issues**:
    -   Are there breaking changes in a core library (like `transformers`) that might affect dependent libraries (like `langchain` or `llama_index`)?
    -   Are there conflicting dependency requirements?
3.  **Synthesize**: Create a high-level summary of the day's AI ecosystem.

Output Format (JSON):
{{
  "synergies": [
    {{
      "title": "Unified Model Support",
      "description": "Both LangChain and LlamaIndex added support for Gemini 1.5 Pro, enabling..."
    }}
  ],
  "potential_issues": [
    {{
      "title": "Dependency Conflict Risk",
      "description": "Transformers v4.39 introduces a breaking change in tokenization that might affect..."
    }}
  ],
  "ecosystem_summary": "Today's updates focus heavily on agentic workflows..."
}}
"""
