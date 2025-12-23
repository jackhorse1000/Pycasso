import base64
import os
from unittest.mock import MagicMock, patch

import pytest

from pycasso.llm import (
    LLMConfig,
    LLMError,
    AuthenticationError,
    RateLimitError,
    generate_prompt,
    generate_image,
    get_api_key,
)


@pytest.fixture
def llm_config():
    return LLMConfig(api_key="test_key", timeout=10.0)


def test_get_api_key_missing():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(LLMError, match="Set OPENROUTER_API_KEY"):
            get_api_key()


def test_get_api_key_present():
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "my_key"}):
        assert get_api_key() == "my_key"


def test_generate_prompt_success(llm_config):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "A synthwave artwork"}}]
    }

    with patch("pycasso.llm.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response

        result = generate_prompt("code summary", "synthwave", llm_config)

        assert result == "A synthwave artwork"


def test_generate_prompt_auth_error(llm_config):
    mock_response = MagicMock()
    mock_response.status_code = 401

    with patch("pycasso.llm.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response

        with pytest.raises(AuthenticationError, match="Authentication failed"):
            generate_prompt("code summary", "synthwave", llm_config)


def test_generate_image_success(llm_config):
    image_bytes = b"fake image data"
    base64_image = base64.b64encode(image_bytes).decode()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "I've generated an image for you.",
                    "images": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            }
        ]
    }

    with patch("pycasso.llm.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response

        result = generate_image("prompt", llm_config)

        assert result == image_bytes


def test_generate_image_no_image_in_response(llm_config):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "I couldn't generate an image."
                }
            }
        ]
    }

    with patch("pycasso.llm.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response

        with pytest.raises(LLMError, match="No images found"):
            generate_image("prompt", llm_config)


def test_rate_limit_with_retry(llm_config):
    mock_response_429 = MagicMock()
    mock_response_429.status_code = 429

    with patch("pycasso.llm.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response_429

        with patch("time.sleep"):
            with pytest.raises(RateLimitError, match="Rate limit exceeded"):
                generate_prompt("code summary", "synthwave", llm_config)
