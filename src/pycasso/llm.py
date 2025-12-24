import base64
import logging
import os
from dataclasses import dataclass
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_TIMEOUT = 60.0
RETRY_DELAY = 5.0

PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt_template() -> str:
    prompt_file = PROMPTS_DIR / "image_prompt.txt"
    return prompt_file.read_text(encoding="utf-8")


@dataclass
class LLMConfig:
    api_key: str
    prompt_model: str = "anthropic/claude-haiku-4.5"
    image_model: str = "google/gemini-2.5-flash-preview-05-20"
    timeout: float = DEFAULT_TIMEOUT


class LLMError(Exception):
    pass


class AuthenticationError(LLMError):
    pass


class RateLimitError(LLMError):
    pass


class TimeoutError(LLMError):
    pass


def get_api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise LLMError("Set OPENROUTER_API_KEY in environment or .env")
    return key


def generate_prompt(code_summary: str, style: str, config: LLMConfig) -> str:
    template = _load_prompt_template()
    prompt = template.format(code_summary=code_summary, style=style)

    payload = {
        "model": config.prompt_model,
        "messages": [{"role": "user", "content": prompt}],
    }

    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }

    response = _make_request(payload, headers, config.timeout)

    try:
        return response["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as e:
        raise LLMError(f"Unexpected response format: {e}") from e


def generate_image(image_prompt: str, config: LLMConfig) -> bytes:
    payload = {
        "model": config.image_model,
        "messages": [{"role": "user", "content": image_prompt}],
        "modalities": ["image", "text"],
    }

    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }

    response = _make_request(payload, headers, config.timeout)

    try:
        message = response["choices"][0]["message"]
        
        if "images" in message and message["images"]:
            image_data = message["images"][0]["image_url"]["url"]
            
            if image_data.startswith("data:"):
                base64_data = image_data.split(",", 1)[1]
                return base64.b64decode(base64_data)
            
            raise LLMError("Image URL format not supported (expected base64 data URL)")
        
        raise LLMError("No images found in response")
    except (KeyError, IndexError) as e:
        raise LLMError(f"Unexpected image response format: {e}") from e


def _make_request(
    payload: dict, headers: dict, timeout: float, retries: int = 1
) -> dict:
    import time

    last_error: Exception | None = None

    for attempt in range(retries + 1):
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(OPENROUTER_API_URL, json=payload, headers=headers)

            if response.status_code == 401:
                raise AuthenticationError("Authentication failed")
            if response.status_code == 429:
                if attempt < retries:
                    logger.warning("Rate limited, retrying in %s seconds...", RETRY_DELAY)
                    time.sleep(RETRY_DELAY)
                    continue
                raise RateLimitError("Rate limit exceeded")

            response.raise_for_status()
            return response.json()

        except httpx.TimeoutException:
            last_error = TimeoutError("API request timed out")
            if attempt < retries:
                logger.warning("Timeout, retrying...")
                time.sleep(RETRY_DELAY)
                continue

        except httpx.HTTPStatusError as e:
            error_body = e.response.text
            logger.error(f"HTTP {e.response.status_code} error response: {error_body}")
            raise LLMError(f"HTTP error: {e.response.status_code} - {error_body}") from e

    if last_error:
        raise last_error
    raise LLMError("Request failed")
