import pytest
import openai
from unittest.mock import patch, MagicMock
from app.services.llm_service import LLMService
from app.core.exceptions import LLMAPIException


def test_llm_service_initialization():
    with patch("app.core.config.settings.OPENROUTER_API_KEY", "test-key"):
        service = LLMService()
        assert service.client is not None
        assert service.client.api_key == "test-key"
        assert service.client.base_url == "https://openrouter.ai/api/v1/"


@pytest.mark.asyncio
async def test_llm_service_successful_generation():
    service = LLMService()
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Test content"
    mock_client.chat.completions.create.return_value.choices = [mock_choice]
    service.client = mock_client

    content = await service.generate_chat_completion(
        messages=[{"role": "user", "content": "hello"}],
        temperature=0.3
    )
    assert content == "Test content"
    from app.core.config import settings
    mock_client.chat.completions.create.assert_called_once_with(
        model=settings.OPENROUTER_MODEL,
        messages=[{"role": "user", "content": "hello"}],
        temperature=0.3
    )


@pytest.mark.asyncio
async def test_llm_service_transient_retry_logic():
    service = LLMService()
    mock_client = MagicMock()
    
    from httpx import Response, Request
    req = Request("POST", "url")
    resp = Response(429, request=req)
    rate_limit_err = openai.RateLimitError(message="Rate limited", response=resp, body={})
    
    mock_choice = MagicMock()
    mock_choice.message.content = "Success after retries"
    
    mock_client.chat.completions.create.side_effect = [rate_limit_err, rate_limit_err, MagicMock(choices=[mock_choice])]
    service.client = mock_client

    with patch("time.sleep") as mock_sleep:
        content = await service.generate_chat_completion(
            messages=[{"role": "user", "content": "hello"}],
            max_retries=3
        )
        assert content == "Success after retries"
        assert mock_client.chat.completions.create.call_count == 3
        assert mock_sleep.call_count == 2


@pytest.mark.asyncio
async def test_llm_service_fatal_no_retry():
    service = LLMService()
    mock_client = MagicMock()
    
    from httpx import Response, Request
    req = Request("POST", "url")
    resp = Response(401, request=req)
    auth_err = openai.AuthenticationError(message="Unauthorized key", response=resp, body={})
    
    mock_client.chat.completions.create.side_effect = auth_err
    service.client = mock_client

    with patch("time.sleep") as mock_sleep:
        with pytest.raises(LLMAPIException) as exc_info:
            await service.generate_chat_completion(
                messages=[{"role": "user", "content": "hello"}],
                max_retries=3
            )
        assert exc_info.value.status_code == 500
        assert mock_client.chat.completions.create.call_count == 1
        assert mock_sleep.call_count == 0
