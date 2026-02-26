import os
import json
import time
from google import genai
try:
    from . import config
except ImportError:
    import config

# --- OpenRouter version (commented out, kept for rollback) ---
# import requests
#
# def check_for_daily_update_openrouter(content: str, target_date: str) -> dict:
#     api_key = os.getenv('OPENROUTER_API_KEY') or config.OPENROUTER_API_KEY
#     if not api_key:
#         print("Warning: OPENROUTER_API_KEY not found.")
#         return None
#     headers = {
#         "Authorization": f"Bearer {api_key}",
#         "Content-Type": "application/json",
#         "HTTP-Referer": "https://ai-changelog-insights.github.io",
#         "X-Title": "AI Changelog Insights"
#     }
#     if target_date not in content:
#         print(f"  📉 Local optimization: '{target_date}' not found in changelog. Skipping LLM.")
#         return None
#     idx = content.find(target_date)
#     start_idx = max(0, idx - 1000)
#     end_idx = min(len(content), idx + 4000)
#     truncated_content = content[start_idx:end_idx]
#     prompt = config.CHANGELOG_UPDATE_CHECK_PROMPT.format(content=truncated_content, target_date=target_date)
#     payload = {
#         "model": config.REWRITE_MODEL,
#         "messages": [
#             {"role": "system", "content": "You are a precise technical changelog parser that outputs only valid JSON."},
#             {"role": "user", "content": prompt}
#         ],
#         "temperature": 0.2,
#         "response_format": {"type": "json_object"},
#         "max_tokens": 2000
#     }
#     try:
#         response = requests.post(config.OPENROUTER_BASE_URL + "/chat/completions", headers=headers, json=payload, timeout=45)
#         response.raise_for_status()
#         choices = response.json().get("choices", [])
#         if not choices:
#             return None
#         result_text = choices[0]["message"]["content"].strip()
#         if result_text.startswith("```json"):
#             result_text = result_text[7:-3].strip()
#         elif result_text.startswith("```"):
#             result_text = result_text[3:-3].strip()
#         try:
#             data = json.loads(result_text)
#             if not data.get("update_found"):
#                 return None
#             return data
#         except json.JSONDecodeError:
#             print(f"Failed to parse JSON from LLM: {result_text[:100]}...")
#             return None
#     except Exception as e:
#         print(f"Error calling OpenRouter: {e}")
#         return None
#
# def generate_global_summary_openrouter(repos_data: list) -> dict:
#     if not repos_data:
#         return None
#     api_key = os.getenv('OPENROUTER_API_KEY') or config.OPENROUTER_API_KEY
#     if not api_key:
#         return None
#     headers = {
#         "Authorization": f"Bearer {api_key}",
#         "Content-Type": "application/json",
#         "HTTP-Referer": "https://ai-changelog-insights.github.io",
#         "X-Title": "AI Changelog Insights"
#     }
#     updates_json = []
#     for repo in repos_data:
#         updates_json.append({"name": repo.get('name'), "summary": (repo.get('title') or '') + ": " + (repo.get('description') or '')})
#     prompt = config.GLOBAL_SUMMARY_PROMPT.format(updates_json=json.dumps(updates_json, indent=2))
#     payload = {
#         "model": config.REWRITE_MODEL,
#         "messages": [
#             {"role": "system", "content": "You are a Senior AI Ecosystem Analyst that outputs strict JSON."},
#             {"role": "user", "content": prompt}
#         ],
#         "temperature": 0.3,
#         "response_format": {"type": "json_object"},
#         "max_tokens": 1500
#     }
#     try:
#         response = requests.post(config.OPENROUTER_BASE_URL + "/chat/completions", headers=headers, json=payload, timeout=60)
#         response.raise_for_status()
#         choices = response.json().get("choices", [])
#         if not choices:
#             return None
#         result_text = choices[0]["message"]["content"].strip()
#         if result_text.startswith("```json"):
#             result_text = result_text[7:-3].strip()
#         elif result_text.startswith("```"):
#             result_text = result_text[3:-3].strip()
#         return json.loads(result_text)
#     except Exception as e:
#         print(f"Error generating global summary: {e}")
#         return None

# --- Gemini API version ---

def _get_gemini_client():
    """Creates and returns a Gemini client."""
    api_key = os.getenv('GEMINI_API_KEY') or config.GEMINI_API_KEY
    if not api_key:
        print("Warning: GEMINI_API_KEY not found.")
        return None
    return genai.Client(api_key=api_key)


def _parse_json_response(text: str) -> dict | None:
    """Extracts and parses JSON from an LLM response, handling markdown fences."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        print(f"Failed to parse JSON from LLM: {text[:100]}...")
        return None


def check_for_daily_update(content: str, target_date: str) -> dict:
    """
    Checks if there is an update for the target_date and returns a dictionary.
    Uses Gemini API with rate limiting.
    """
    client = _get_gemini_client()
    if not client:
        return None

    # 1. Local Pre-check (Cost Saving)
    if target_date not in content:
        print(f"  📉 Local optimization: '{target_date}' not found in changelog. Skipping LLM.")
        return None

    # 2. Extract relevant section (Token Saving)
    idx = content.find(target_date)
    start_idx = max(0, idx - 1000)
    end_idx = min(len(content), idx + 4000)
    truncated_content = content[start_idx:end_idx]

    prompt = config.CHANGELOG_UPDATE_CHECK_PROMPT.format(
        content=truncated_content,
        target_date=target_date
    )

    try:
        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction="You are a precise technical changelog parser that outputs only valid JSON.",
                temperature=0.2,
                max_output_tokens=2000,
                response_mime_type="application/json",
            ),
        )

        # Rate limiting: 5 RPM
        print(f"  ⏳ Rate limit pause ({config.RATE_LIMIT_DELAY}s)...")
        time.sleep(config.RATE_LIMIT_DELAY)

        result_text = response.text
        if not result_text:
            return None

        data = _parse_json_response(result_text)
        if not data or not data.get("update_found"):
            return None
        return data

    except Exception as e:
        print(f"Error calling Gemini API: {e}")
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

    # Prepare input data
    updates_json = []
    for repo in repos_data:
        updates_json.append({
            "name": repo.get('name'),
            "summary": (repo.get('title') or '') + ": " + (repo.get('description') or '')
        })

    prompt = config.GLOBAL_SUMMARY_PROMPT.format(
        updates_json=json.dumps(updates_json, indent=2)
    )

    try:
        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction="You are a Senior AI Ecosystem Analyst that outputs strict JSON.",
                temperature=0.3,
                max_output_tokens=1500,
                response_mime_type="application/json",
            ),
        )

        # Rate limiting: 5 RPM
        print(f"  ⏳ Rate limit pause ({config.RATE_LIMIT_DELAY}s)...")
        time.sleep(config.RATE_LIMIT_DELAY)

        result_text = response.text
        if not result_text:
            return None

        return _parse_json_response(result_text)

    except Exception as e:
        print(f"Error generating global summary: {e}")
        return None
