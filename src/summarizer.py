import requests
import os
import json
try:
    from . import config
except ImportError:
    import config

def check_for_daily_update(content: str, target_date: str) -> dict:
    """
    Checks if there is an update for the target_date and returns a dictionary.
    """
    api_key = os.getenv('OPENROUTER_API_KEY') or config.OPENROUTER_API_KEY
    if not api_key:
        print("Warning: OPENROUTER_API_KEY not found.")
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://ai-changelog-insights.github.io",
        "X-Title": "AI Changelog Insights"
    }
    
    # 1. Local Pre-check (Cost Saving)
    if target_date not in content:
        print(f"  📉 Local optimization: '{target_date}' not found in changelog. Skipping LLM.")
        return None

    # 2. Extract relevant section (Token Saving)
    # Find the date index
    idx = content.find(target_date)
    
    # Start context 1000 chars before (to catch the header like "## v1.2.3 (2026-02-25)")
    start_idx = max(0, idx - 1000)
    
    # End context: Take next 4000 chars (Increased from 2000 to capture full release notes for better "Try It Out")
    end_idx = min(len(content), idx + 4000)
    
    truncated_content = content[start_idx:end_idx]
    
    prompt = config.CHANGELOG_UPDATE_CHECK_PROMPT.format(
        content=truncated_content,
        target_date=target_date
    )

    payload = {
        "model": config.REWRITE_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a precise technical changelog parser that outputs only valid JSON."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ],
        "temperature": 0.2, # Slightly increased to allow for better code generation creativity while keeping strict JSON
        "response_format": {"type": "json_object"},
        "max_tokens": 2000 # Increased from 1000 to allow for longer code snippets
    }
    
    try:
        response = requests.post(
            config.OPENROUTER_BASE_URL + "/chat/completions",
            headers=headers,
            json=payload,
            timeout=45 # Increased timeout for longer generation
        )
        response.raise_for_status()
        
        choices = response.json().get("choices", [])
        if not choices:
            return None
            
        result_text = choices[0]["message"]["content"].strip()
        
        # Clean up if markdown code block is present
        if result_text.startswith("```json"):
            result_text = result_text[7:-3].strip()
        elif result_text.startswith("```"):
            result_text = result_text[3:-3].strip()
            
        try:
            data = json.loads(result_text)
            if not data.get("update_found"):
                return None
            return data
        except json.JSONDecodeError:
            print(f"Failed to parse JSON from LLM: {result_text[:100]}...")
            return None
        
    except Exception as e:
        print(f"Error calling OpenRouter: {e}")
        return None
