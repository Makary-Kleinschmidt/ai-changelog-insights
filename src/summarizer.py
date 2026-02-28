import os
import json
import time
from google import genai
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    retry_if_exception,
)
from src import config


def _get_gemini_client():
    """Creates and returns a Gemini client with timeout."""
    api_key = os.getenv("GEMINI_API_KEY") or config.GEMINI_API_KEY
    if not api_key:
        print("Warning: GEMINI_API_KEY not found.")
        return None
    # Configure timeout via http_options (in milliseconds)
    timeout_ms = getattr(config, "GEMINI_TIMEOUT", 60) * 1000
    return genai.Client(api_key=api_key, http_options={"timeout": timeout_ms})


# Track exhausted models globally for the session
_exhausted_models = set()


def retry_if_api_error(exception):
    err_msg = str(exception).lower()
    return any(
        code in err_msg
        for code in [
            "503",
            "service unavailable",
            "429",
            "resource_exhausted",
            "504",
            "deadline_exceeded",
        ]
    )


@retry(
    stop=stop_after_attempt(getattr(config, "MAX_RETRIES", 2) + 1),
    wait=wait_exponential(multiplier=1, min=getattr(config, "RETRY_DELAY", 30), max=60),
    retry=retry_if_exception_type(Exception) & retry_if_exception(retry_if_api_error),
)
def _call_gemini_single_model(
    client,
    model_name,
    prompt,
    system_instruction,
    temperature,
    max_tokens,
    response_schema,
):
    print(f"  🤖 Calling {model_name}...", flush=True)
    start_time = time.time()

    gen_config = genai.types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=temperature,
        max_output_tokens=max_tokens,
        response_mime_type="application/json",
    )
    if response_schema:
        gen_config.response_schema = response_schema

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=gen_config,
    )
    duration = time.time() - start_time
    print(f"  ✅ Response received in {duration:.1f}s.", flush=True)

    # Rate limit pause after success
    rate_limit_delay = getattr(config, "RATE_LIMIT_DELAY", 12)
    print(f"  ⏳ Rate limit pause ({rate_limit_delay}s)...")
    time.sleep(rate_limit_delay)

    return response


def _call_gemini_with_fallback(
    prompt, system_instruction, temperature=0.2, max_tokens=None, response_schema=None
):
    """
    Calls Gemini API with model fallback and retries on transient errors (503/429/504).
    Tries the primary model first, then each fallback model.
    Returns the response object or None.
    """
    client = _get_gemini_client()
    if not client:
        return None

    if max_tokens is None:
        max_tokens = getattr(config, "MAX_OUTPUT_TOKENS", 16000)

    # Build ordered model list: primary first, then fallbacks (which exclude the primary)
    primary = getattr(config, "GEMINI_MODEL", "gemini-2.5-flash")
    fallbacks = getattr(config, "GEMINI_FALLBACK_MODELS", [])
    models = [primary] + [m for m in fallbacks if m != primary]

    # Filter out models known to be exhausted in this session
    models = [m for m in models if m not in _exhausted_models]

    if not models:
        print("❌ All configured models are exhausted or unavailable.")
        return None

    for model_name in models:
        if model_name in _exhausted_models:
            continue

        try:
            return _call_gemini_single_model(
                client,
                model_name,
                prompt,
                system_instruction,
                temperature,
                max_tokens,
                response_schema,
            )
        except Exception as e:
            err_msg = str(e).lower()
            if "429" in err_msg or "resource_exhausted" in err_msg:
                print(
                    f"  🚫 {model_name} seems to have hit DAILY LIMIT (or persistent 429). Marking as exhausted."
                )
                _exhausted_models.add(model_name)

            print(
                f"  ❌ Max retries reached or unrecoverable error with {model_name}: {e}. Trying next model..."
            )

    return None


def check_for_daily_update(content: str, target_date: str) -> dict:
    """
    Checks if there is an update for the target_date and returns a dictionary.
    Uses Gemini API with fallback and retries.
    """
    if target_date not in content:
        print(
            f"  📉 Local optimization: '{target_date}' not found in changelog. Skipping LLM."
        )
        return None

    idx = content.find(target_date)
    start_idx = max(0, idx - 1000)
    end_idx = min(len(content), idx + 4000)
    truncated_content = content[start_idx:end_idx]

    prompt = config.CHANGELOG_UPDATE_CHECK_PROMPT.format(
        content=truncated_content, target_date=target_date
    )

    schema = {
        "type": "OBJECT",
        "properties": {
            "update_found": {"type": "BOOLEAN"},
            "title": {"type": "STRING"},
            "description": {"type": "STRING"},
            "whats_new": {"type": "ARRAY", "items": {"type": "STRING"}},
            "why_important": {"type": "STRING"},
            "try_it_out": {
                "type": "OBJECT",
                "properties": {
                    "language": {"type": "STRING"},
                    "beginner": {
                        "type": "OBJECT",
                        "properties": {
                            "label": {"type": "STRING"},
                            "code": {"type": "STRING"},
                        },
                    },
                    "intermediate": {
                        "type": "OBJECT",
                        "properties": {
                            "label": {"type": "STRING"},
                            "code": {"type": "STRING"},
                        },
                    },
                    "advanced": {
                        "type": "OBJECT",
                        "properties": {
                            "label": {"type": "STRING"},
                            "code": {"type": "STRING"},
                        },
                    },
                },
            },
        },
        "required": ["update_found"],
    }

    response = _call_gemini_with_fallback(
        prompt=prompt,
        system_instruction="You are a precise technical changelog parser that outputs only valid JSON according to the schema.",
        response_schema=schema,
    )

    if not response or not response.text:
        return None

    try:
        data = json.loads(response.text)
        if not data.get("update_found"):
            return None
        return data
    except json.JSONDecodeError as e:
        print(f"  ❌ Failed to parse JSON response: {e}")
        return None


def generate_global_summary(repos_data: list) -> dict:
    """
    Generates a high-level summary of all updates, looking for synergies and issues.
    Uses Gemini API with rate limiting.
    """
    if not repos_data:
        return None

    client = _get_gemini_client()
    if not client:
        return None

    updates_json = []
    for repo in repos_data:
        updates_json.append(
            {
                "name": repo.get("name"),
                "summary": (repo.get("title") or "")
                + ": "
                + (repo.get("description") or ""),
            }
        )

    prompt = config.GLOBAL_SUMMARY_PROMPT.format(
        updates_json=json.dumps(updates_json, indent=2)
    )

    schema = {
        "type": "OBJECT",
        "properties": {
            "ecosystem_summary": {"type": "STRING"},
            "synergies": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "title": {"type": "STRING"},
                        "description": {"type": "STRING"},
                    },
                    "required": ["title", "description"],
                },
            },
            "potential_issues": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "title": {"type": "STRING"},
                        "description": {"type": "STRING"},
                    },
                    "required": ["title", "description"],
                },
            },
        },
        "required": ["ecosystem_summary"],
    }

    response = _call_gemini_with_fallback(
        prompt=prompt,
        system_instruction="You are a Senior AI Ecosystem Analyst that outputs strict JSON according to the formula.",
        temperature=0.3,
        response_schema=schema,
    )

    if not response or not response.text:
        return None

    try:
        return json.loads(response.text)
    except json.JSONDecodeError as e:
        print(f"  ❌ Failed to parse JSON response: {e}")
        return None
