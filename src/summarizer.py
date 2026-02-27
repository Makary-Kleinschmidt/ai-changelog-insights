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
    """Creates and returns a Gemini client with timeout."""
    api_key = os.getenv('GEMINI_API_KEY') or config.GEMINI_API_KEY
    if not api_key:
        print("Warning: GEMINI_API_KEY not found.")
        return None
    # Configure timeout via http_options (in milliseconds)
    timeout_ms = getattr(config, 'GEMINI_TIMEOUT', 60) * 1000
    return genai.Client(
        api_key=api_key,
        http_options={'timeout': timeout_ms}
    )


def _repair_truncated_json(text: str) -> dict | None:
    """
    Attempts to repair JSON that was truncated mid-generation by closing
    any open strings, arrays, and objects.
    """
    # Close any open quoted string
    quote_count = text.count('"') - text.count('\\"')
    if quote_count % 2 != 0:
        text += '"'

    # Close open brackets/braces from inside out
    stack = []
    in_string = False
    escape = False
    for ch in text:
        if escape:
            escape = False
            continue
        if ch == '\\':
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch in ('{', '['):
            stack.append('}' if ch == '{' else ']')
        elif ch in ('}', ']'):
            if stack and stack[-1] == ch:
                stack.pop()

    # Remove any trailing comma before we close
    text = text.rstrip().rstrip(',')
    text += ''.join(reversed(stack))

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _parse_json_response(text: str) -> dict | None:
    """Extracts and parses JSON from an LLM response, handling markdown fences, preamble, and truncation."""
    text = text.strip()
    
    # Remove markdown code fences if present
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    
    # 1. Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. Try to find the first '{' and last '}'
    import re
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    except AttributeError:
        pass

    # 3. Repair truncated JSON (response was cut off mid-generation)
    first_brace = text.find('{')
    if first_brace != -1:
        truncated = text[first_brace:]
        repaired = _repair_truncated_json(truncated)
        if repaired:
            print(f"  🔧 Repaired truncated JSON successfully.")
            return repaired
            
    print(f"Failed to parse JSON from LLM: {text[:150]}...")
    return None



# Track exhausted models globally for the session
_exhausted_models = set()

def _call_gemini_with_fallback(prompt, system_instruction, temperature=0.2, max_tokens=None):
    """
    Calls Gemini API with model fallback and retries on transient errors (503/429/504).
    Tries the primary model first, then each fallback model.
    Returns the response object or None.
    """
    client = _get_gemini_client()
    if not client:
        return None

    if max_tokens is None:
        max_tokens = getattr(config, 'MAX_OUTPUT_TOKENS', 16000)

    # Build ordered model list: primary first, then fallbacks (which exclude the primary)
    primary = getattr(config, 'GEMINI_MODEL', 'gemini-2.5-flash')
    fallbacks = getattr(config, 'GEMINI_FALLBACK_MODELS', [])
    models = [primary] + [m for m in fallbacks if m != primary]
    
    # Filter out models known to be exhausted in this session
    models = [m for m in models if m not in _exhausted_models]
    
    if not models:
        print("❌ All configured models are exhausted or unavailable.")
        return None
    
    for model_name in models:
        # Double check in case it was added during another thread/process (unlikely here but good practice)
        if model_name in _exhausted_models:
            continue
            
        for attempt in range(config.MAX_RETRIES + 1):
            try:
                print(f"  🤖 Calling {model_name} (Attempt {attempt + 1})...", flush=True)
                start_time = time.time()
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=genai.types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                        response_mime_type="application/json",
                    ),
                )
                duration = time.time() - start_time
                print(f"  ✅ Response received in {duration:.1f}s.", flush=True)
                
                # Rate limit pause after success
                print(f"  ⏳ Rate limit pause ({config.RATE_LIMIT_DELAY}s)...")
                time.sleep(config.RATE_LIMIT_DELAY)
                
                return response
            
            except Exception as e:
                err_msg = str(e).lower()
                # Retryable: 503 Service Unavailable, 429 Rate Limit, 504 Deadline Exceeded
                is_retryable = any(code in err_msg for code in [
                    "503", "service unavailable",
                    "429", "resource_exhausted",
                    "504", "deadline_exceeded"
                ])
                
                if is_retryable:
                    if attempt < config.MAX_RETRIES:
                        # Try to extract server-suggested retry delay
                        wait_time = config.RETRY_DELAY
                        import re as _re
                        delay_match = _re.search(r'retryDelay.*?(\d+)s', str(e))
                        if delay_match:
                            suggested = int(delay_match.group(1))
                            wait_time = max(wait_time, suggested + 2)
                        
                        # 429 Specific Handling: If it's a 429, it might be RPM or Daily Limit.
                        # We wait and retry. If it fails repeatedly, we'll catch it after the loop.
                        if "429" in err_msg or "resource_exhausted" in err_msg:
                            print(f"  ⚠️ Rate Limit/Quota (429) on {model_name}. Retrying in {wait_time}s...")
                        else:
                            print(f"  ⚠️ Transient error ({e}). Retrying in {wait_time}s...")
                            
                        time.sleep(wait_time)
                        continue
                    else:
                        # Retries exhausted.
                        # If the last error was a 429, assume it's a Daily Limit (RPD) or persistent overload.
                        # Mark as exhausted for the session so we don't waste time on it again.
                        if "429" in err_msg or "resource_exhausted" in err_msg:
                            print(f"  🚫 {model_name} seems to have hit DAILY LIMIT (or persistent 429). Marking as exhausted.")
                            _exhausted_models.add(model_name)
                        
                        print(f"  ❌ Max retries reached for {model_name}. Trying next model...")
                else:
                    # For other errors (like 404 or prompt blocking), try next model immediately
                    print(f"  ❌ Error with {model_name}: {e}")
                    break
    
    return None


def check_for_daily_update(content: str, target_date: str) -> dict:
    """
    Checks if there is an update for the target_date and returns a dictionary.
    Uses Gemini API with fallback and retries.
    """
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

    response = _call_gemini_with_fallback(
        prompt=prompt,
        system_instruction="You are a precise technical changelog parser that outputs only valid JSON."
    )

    if not response or not response.text:
        return None

    data = _parse_json_response(response.text)
    if not data or not data.get("update_found"):
        return None
    return data


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

    response = _call_gemini_with_fallback(
        prompt=prompt,
        system_instruction="You are a Senior AI Ecosystem Analyst that outputs strict JSON.",
        temperature=0.3
    )

    if not response or not response.text:
        return None

    return _parse_json_response(response.text)
