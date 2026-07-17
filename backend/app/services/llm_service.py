import time
import openai
from app.core.config import settings
from app.core.exceptions import handle_llm_exception, LLMAPIException, BadRequestException
from loguru import logger


class LLMService:
    def __init__(self):
        self.client = None
        api_key = settings.OPENROUTER_API_KEY
        base_url = settings.OPENROUTER_BASE_URL or "https://openrouter.ai/api/v1"
        
        if api_key:
            self.client = openai.OpenAI(
                api_key=api_key,
                base_url=base_url,
                default_headers={
                    "HTTP-Referer": "https://github.com/asad594/ResumeAI",
                    "X-Title": "AI Resume Analyzer",
                }
            )

    async def generate_chat_completion(
        self,
        messages: list,
        response_format: dict = None,
        temperature: float = 0.2,
        max_tokens: int = None,
        model: str = None,
        max_retries: int = 3,
    ) -> str:
        if not self.client:
            raise ValueError("OpenRouter API key is not configured. Set OPENROUTER_API_KEY in .env")
            
        model_name = model or settings.OPENROUTER_MODEL or "google/gemini-2.5-flash"
        
        kwargs = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
        }
        if response_format:
            kwargs["response_format"] = response_format
        if max_tokens:
            kwargs["max_tokens"] = max_tokens

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(**kwargs)
                content = response.choices[0].message.content
                if content is None:
                    raise ValueError("LLM response content was empty")
                
                # Verify and log request details
                token_usage = getattr(response, "usage", None)
                usage_dict = {
                    "prompt_tokens": getattr(token_usage, "prompt_tokens", None),
                    "completion_tokens": getattr(token_usage, "completion_tokens", None),
                    "total_tokens": getattr(token_usage, "total_tokens", None),
                } if token_usage else None

                logger.info(
                    f"OpenRouter Request Verification:\n"
                    f"- Model: {getattr(response, 'model', model_name)}\n"
                    f"- Base URL: {self.client.base_url}\n"
                    f"- Token Usage: {usage_dict}\n"
                    f"- Response ID: {getattr(response, 'id', None)}"
                )
                
                return content
            except Exception as e:
                # Log failed request verification details
                logger.error(
                    f"OpenRouter Request Failed Verification:\n"
                    f"- Model: {model_name}\n"
                    f"- Base URL: {self.client.base_url}"
                )
                
                # Check for transient failures
                is_transient = False
                
                if isinstance(e, (openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError, openai.InternalServerError)):
                    is_transient = True
                elif hasattr(e, "status_code"):
                    if getattr(e, "status_code") in (429, 500, 502, 503, 504):
                        is_transient = True
                else:
                    err_msg = str(e).lower()
                    if "429" in err_msg or "rate limit" in err_msg or "timeout" in err_msg or "timed out" in err_msg or "connection" in err_msg or "internal error" in err_msg or "quota" in err_msg:
                        is_transient = True
                
                # Do NOT retry for invalid API key (401), invalid model (404/400)
                if isinstance(e, (openai.AuthenticationError, openai.NotFoundError)) or "api key" in str(e).lower() or "invalid api" in str(e).lower() or "model" in str(e).lower():
                    is_transient = False
                
                if is_transient and attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + 2
                    logger.warning(f"Transient LLM error on attempt {attempt + 1}. Retrying in {wait_time}s... Error: {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    raise handle_llm_exception(e)
