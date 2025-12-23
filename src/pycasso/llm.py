import base64
import logging
import os
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_TIMEOUT = 60.0
RETRY_DELAY = 5.0

PROMPT_TEMPLATE = """You are an artist creating unique visual art inspired by code. Your task is to create art that truly represents THIS SPECIFIC codebase, not generic tech imagery.

## Code Analysis:
{code_summary}

## Your Task:
Create a detailed image generation prompt that captures the UNIQUE essence of this codebase.

CRITICAL REQUIREMENTS:
1. **Be Specific**: Reference the actual domain concepts, libraries, and functionality described above
2. **Visual Metaphors**: Transform the code's purpose into visual elements:
   - If it processes data → flowing streams, transformations, crystals forming
   - If it has APIs → interconnected nodes, gateways, bridges
   - If it generates content → blooming flowers, stars being born, paint splatters
   - If it has AI/ML → neural networks as organic structures, learning as growth
3. **Reflect Complexity**: Match the visual complexity to the code complexity
4. **Domain Colors**: Use colors that evoke the domain (e.g., green for nature apps, gold for finance)

## Style Requirement:
{style}

## Output Format:
Write ONLY the image generation prompt. Make it detailed (2-4 sentences) and highly specific to this codebase. Do NOT include generic tech elements like "circuit boards" or "binary code" unless the code is actually about those things."""


@dataclass
class LLMConfig:
    api_key: str
    prompt_model: str = "openai/gpt-4.1"
    image_model: str = "google/gemini-2.0-flash-exp:free"
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
    prompt = PROMPT_TEMPLATE.format(code_summary=code_summary, style=style)

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
