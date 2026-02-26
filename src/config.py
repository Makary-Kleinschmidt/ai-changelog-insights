import os
from dotenv import load_dotenv

load_dotenv()

# --- OpenRouter (commented out, kept for rollback) ---
# OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
# OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
# REWRITE_MODEL = "deepseek/deepseek-v3.2"

# --- Gemini API ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-3.0-flash"
RATE_LIMIT_DELAY = 12  # seconds between calls (5 RPM limit)
DAILY_LIMIT = 20       # max 20 requests per day

GH_ACCESS_TOKEN = os.getenv("GH_ACCESS_TOKEN")

# VIP Repositories to always check
VIP_REPOS = [
    # Agents & Frameworks
    "All-Hands-AI/OpenHands",
    "Significant-Gravitas/AutoGPT",
    "langchain-ai/langchain",
    "langchain-ai/langgraph",
    "run-llama/llama_index",
    "microsoft/autogen",
    "microsoft/Semantic-Kernel",
    "crewAIInc/crewAI",
    "agno-agi/agno",
    "infiniflow/ragflow",

    # Models & Inference
    "ollama/ollama",
    "vllm-project/vllm",
    "ggerganov/llama.cpp",
    "huggingface/transformers",
    "huggingface/peft",
    "huggingface/diffusers",
    "pytorch/pytorch",
    
    # SDKs
    "anthropics/anthropic-sdk-python",
    "google/generative-ai-python",
    "openai/openai-python",
    
    # Tools & UI
    "open-webui/open-webui",
    "AUTOMATIC1111/stable-diffusion-webui",
    "Comfy-Org/ComfyUI",
    "gradio-app/gradio",
    "streamlit/streamlit",
    
    # Vector DBs & Data
    "chroma-core/chroma",
    "qdrant/qdrant",
    "huggingface/datasets",
    
    # Audio/Video/Other
    "openai/whisper",
    "ultralytics/ultralytics"
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

2.  **What's New (whats_new)**: A list of factual bullet points describing WHAT changed.
    -   Each item should be a single, specific fact (e.g., "Added streaming support for tool calls in the Chat API").
    -   Be specific and technical. No vague statements.
    -   NEVER mention whether an update is "nightly", "daily", "weekly", or what those terms mean.
    -   NEVER describe release cadence or timing. Focus ONLY on the technical changes themselves.

3.  **Why It's Important (why_important)**: A paragraph providing context and significance.
    -   Explain the practical benefit IN DEPTH (at least 3-4 sentences).
    -   Provide context on the problem being solved.
    -   Compare "before" vs "after" scenarios.
    -   Explain why this matters for the user's workflow or application.
    -   Example: "Previously, vector search on large datasets could take seconds. This update introduces a new indexing algorithm that reduces latency by 50% for RAG pipelines, making real-time applications viable."

4.  **Try It Out (try_it_out)**: Provide 3 levels of implementation examples.
    -   Each level should have a short descriptive label and valid, copy-pasteable code.
    -   **beginner**: The simplest possible usage. Install + hello world.
    -   **intermediate**: A realistic use case with configuration or parameters.
    -   **advanced**: Production-ready pattern with error handling, best practices, or integration.
    -   Do not use placeholders like `your_code_here`. Make them working examples.

Output Format (JSON):
{{
  "update_found": true,
  "title": "Release Title/Version",
  "whats_new": [
    "Added streaming support for tool calls",
    "Fixed memory leak in batch processing",
    "Deprecated old v1 embedding endpoint"
  ],
  "why_important": "Detailed paragraph explaining significance and context...",
  "try_it_out": {{
    "language": "python",
    "beginner": {{
      "label": "Quick Start",
      "code": "pip install library\\nfrom library import feature\\nresult = feature.run()\\nprint(result)"
    }},
    "intermediate": {{
      "label": "With Configuration",
      "code": "from library import feature\\n\\nclient = feature.Client(timeout=30)\\nresult = client.run(param='value', stream=True)\\nfor chunk in result:\\n    print(chunk)"
    }},
    "advanced": {{
      "label": "Production Setup",
      "code": "import asyncio\\nfrom library import feature\\n\\nasync def main():\\n    client = feature.AsyncClient(\\n        timeout=30,\\n        retries=3\\n    )\\n    try:\\n        result = await client.run(param='value')\\n        print(result)\\n    except Exception as e:\\n        logging.error(f'Failed: {{e}}')\\n\\nasyncio.run(main())"
    }}
  }}
}}
"""

GLOBAL_SUMMARY_PROMPT = """You are a Senior AI Ecosystem Analyst.
Your task is to analyze a collection of daily updates from major AI libraries/tools and identify cross-cutting themes, synergies, and potential conflicts.

Updates for today:
{updates_json}

Instructions:
1.  **Analyze Synergies**: Look for connections between updates.
    -   Did multiple libraries add support for the same model?
    -   Are there complementary features?
2.  **Identify Potential Issues**:
    -   Are there breaking changes in a core library that might affect dependent libraries?
    -   Are there conflicting dependency requirements?
3.  **Write the Ecosystem Summary (CRITICAL)**:
    -   Write a CONTINUOUS, PROGRESSIVE summary — do NOT use section headers or level labels.
    -   Structure it as multiple paragraphs that naturally flow from simple to complex:
        - Start with foundational context anyone can understand (what happened today, which tools updated).
        - In the middle paragraphs, explain the technical connections and synergies between updates.
        - End with advanced analysis: architectural implications, potential breaking changes, migration strategies.
    -   Each paragraph should build on the previous one. A reader starts with beginner info and ends with advanced insights.
    -   Use Markdown links for any URLs: [display text](https://url). This is important for rendering.

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

