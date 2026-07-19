"""
Thin GenAI wrapper so the rest of the app never touches a vendor SDK
directly. Swap providers with one env var — no other code changes.

    LLM_PROVIDER=gemini     (default)  needs GEMINI_API_KEY
    LLM_PROVIDER=openai                needs OPENAI_API_KEY
    LLM_PROVIDER=anthropic             needs ANTHROPIC_API_KEY
"""

import os
import json
import urllib.error
import urllib.request

PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()


class LLMError(Exception):
    pass


class LLMRateLimitError(LLMError):
    pass


def _generate_gemini(system_prompt: str, user_prompt: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise LLMError("GEMINI_API_KEY is not set. Add it to your .env file.")

    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    # Build standard Gemini REST payload with systemInstruction
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": user_prompt}
                ]
            }
        ],
        "systemInstruction": {
            "parts": [
                {"text": system_prompt}
            ]
        },
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 500
        }
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = response.read().decode("utf-8")
            data = json.loads(res_data)
            
            # Extract content from response structure
            candidates = data.get("candidates", [])
            if not candidates:
                raise LLMError("No response candidates returned from Gemini API.")
            
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                raise LLMError("Empty content returned from Gemini API.")
                
            return parts[0].get("text", "").strip()
            
    except urllib.error.HTTPError as e:
        if e.code == 429:
            raise LLMRateLimitError("High demand — try again in a few seconds.")
        try:
            error_details = e.read().decode("utf-8")
            error_json = json.loads(error_details)
            error_msg = error_json.get("error", {}).get("message", error_details)
            raise LLMError(f"Gemini API error: {error_msg}")
        except json.JSONDecodeError:
            raise LLMError(f"Gemini API call failed with response code {e.code}")
    except Exception as e:
        raise LLMError(f"Gemini connection failed: {e}")


def _generate_openai(system_prompt: str, user_prompt: str) -> str:
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key.startswith("sk-your"):
        raise LLMError(
            "OPENAI_API_KEY is not set. Add it to your .env file. "
            "Get one at https://platform.openai.com/api-keys"
        )

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,
        max_tokens=500,
    )
    return resp.choices[0].message.content.strip()


def _generate_anthropic(system_prompt: str, user_prompt: str) -> str:
    import anthropic

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key.startswith("sk-ant-your"):
        raise LLMError(
            "ANTHROPIC_API_KEY is not set. Add it to your .env file. "
            "Get one at https://console.anthropic.com/"
        )

    client = anthropic.Anthropic(api_key=api_key)
    model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

    resp = client.messages.create(
        model=model,
        max_tokens=500,
        temperature=0.4,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return resp.content[0].text.strip()


def generate(system_prompt: str, user_prompt: str) -> str:
    """Call the configured GenAI provider and return plain text."""
    try:
        if PROVIDER == "gemini":
            return _generate_gemini(system_prompt, user_prompt)
        if PROVIDER == "anthropic":
            return _generate_anthropic(system_prompt, user_prompt)
        if PROVIDER == "openai":
            return _generate_openai(system_prompt, user_prompt)
        raise LLMError(f"Unknown LLM_PROVIDER '{PROVIDER}'. Use 'gemini', 'openai', or 'anthropic'.")
    except LLMError:
        raise
    except Exception as e:
        raise LLMError(f"LLM call failed: {type(e).__name__}: {e}")
