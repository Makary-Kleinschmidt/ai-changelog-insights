import requests
import os
import json
try:
    from . import config
except ImportError:
    import config

def check_for_daily_update(content: str, target_date: str) -> str:
    """
    Checks if there is an update for the target_date and returns summary or 'NO_UPDATE'.
    """
    api_key = os.getenv('OPENROUTER_API_KEY') or config.OPENROUTER_API_KEY
    if not api_key:
        print("Warning: OPENROUTER_API_KEY not found.")
        return "NO_UPDATE"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://ai-changelog-insights.github.io",
        "X-Title": "AI Changelog Insights"
    }
    
    # Truncate content to avoid token limits (keep top 8000 chars where latest updates usually are)
    truncated_content = content[:8000]
    
    prompt = config.CHANGELOG_UPDATE_CHECK_PROMPT.format(
        content=truncated_content,
        target_date=target_date
    )

    payload = {
        "model": config.REWRITE_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a precise technical changelog parser."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ],
        "temperature": 0.1, # Very low temp for strict parsing
        "max_tokens": 500
    }
    
    try:
        response = requests.post(
            config.OPENROUTER_BASE_URL + "/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        
        choices = response.json().get("choices", [])
        if not choices:
            return "NO_UPDATE"
            
        result = choices[0]["message"]["content"].strip()
        
        # Basic validation
        if "NO_UPDATE" in result:
            return "NO_UPDATE"
            
        return result
        
    except Exception as e:
        print(f"Error calling OpenRouter: {e}")
        return "NO_UPDATE"
