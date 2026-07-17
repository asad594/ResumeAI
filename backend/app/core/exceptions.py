from fastapi import HTTPException, status
import openai
import traceback
import sys
from loguru import logger
from app.core.config import settings


class AppException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


class NotFoundException(AppException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class UnauthorizedException(AppException):
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class ForbiddenException(AppException):
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class BadRequestException(AppException):
    def __init__(self, detail: str = "Bad request"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class ConflictException(AppException):
    def __init__(self, detail: str = "Conflict"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class FileTooLargeException(AppException):
    def __init__(self, max_size_mb: int = 10):
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum limit of {max_size_mb}MB",
        )


class InvalidFileTypeException(AppException):
    def __init__(self, allowed_types: list = None):
        types_str = ", ".join(allowed_types) if allowed_types else "PDF, DOCX"
        super().__init__(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Invalid file type. Allowed: {types_str}",
        )


class LLMAPIException(HTTPException):
    def __init__(self, status_code: int, detail: dict):
        super().__init__(status_code=status_code, detail=detail)


def handle_llm_exception(e: Exception) -> LLMAPIException:
    if isinstance(e, LLMAPIException):
        return e
    
    # Capture complete Python traceback
    exc_type, exc_value, exc_traceback = sys.exc_info()
    tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback)) if exc_type else "No traceback available"

    # Always log the complete backend exception and traceback
    logger.exception("Complete technical error from LLM API call:")

    # Defaults
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_type = "unknown_error"
    message = "An unexpected error occurred while communicating with the AI service. Please try again later."
    retry_after = None
    
    # Diagnostic fields to extract
    http_status = None
    response_json = None
    request_model = settings.OPENROUTER_MODEL
    endpoint = f"{(settings.OPENROUTER_BASE_URL or 'https://openrouter.ai/api/v1').rstrip('/')}/chat/completions"
    exception_type = type(e).__name__

    # Check if this is an OpenAI SDK exception
    if isinstance(e, openai.OpenAIError):
        body = getattr(e, "body", None)
        headers = getattr(e, "headers", None)
        if not headers and hasattr(e, "response") and e.response:
            headers = getattr(e.response, "headers", None)
            
        # Extract HTTP status
        if hasattr(e, "status_code"):
            http_status = getattr(e, "status_code")
        elif hasattr(e, "response") and e.response:
            http_status = getattr(e.response, "status_code", None)

        # Extract Response JSON
        if body:
            response_json = body
        elif hasattr(e, "response") and e.response:
            try:
                response_json = e.response.json()
            except Exception:
                try:
                    response_json = e.response.text
                except Exception:
                    pass

        logger.error(f"OpenAIError details - Type: {type(e).__name__}, Body: {body}, Headers: {headers}")

        # Attempt to parse retry delay from headers
        if headers:
            headers_lower = {k.lower(): v for k, v in headers.items()}
            retry_after_str = headers_lower.get("retry-after") or headers_lower.get("retry-delay")
            if retry_after_str:
                try:
                    retry_after = int(float(retry_after_str))
                except ValueError:
                    pass

        # Attempt to parse retry delay from Google's response body structure
        if isinstance(body, dict):
            error_data = body.get("error", {})
            details = error_data.get("details", [])
            if isinstance(details, list):
                for detail in details:
                    if isinstance(detail, dict) and "retryDelay" in detail:
                        delay_str = detail["retryDelay"]
                        if isinstance(delay_str, str) and delay_str.endswith("s"):
                            try:
                                retry_after = int(float(delay_str[:-1]))
                            except ValueError:
                                pass

        # Map by specific OpenAI exception classes
        if isinstance(e, openai.AuthenticationError):
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR  # Keep 500 to avoid logging out frontend clients via 401
            error_type = "invalid_api_key"
            message = "Invalid LLM API key. Please check your credentials and configuration."
        
        elif isinstance(e, openai.RateLimitError):
            err_msg = str(e).lower()
            body_msg = ""
            body_status = ""
            if body and isinstance(body, dict):
                body_msg = str(body.get("error", {}).get("message", "")).lower()
                body_status = str(body.get("error", {}).get("status", "")).upper()

            is_quota = "quota" in err_msg or "quota" in body_msg or "resource_exhausted" in err_msg or body_status == "RESOURCE_EXHAUSTED"

            if is_quota:
                status_code = status.HTTP_429_TOO_MANY_REQUESTS
                error_type = "quota_exceeded"
                message = "AI service quota has been exceeded. Please check your billing details and usage limits."
            else:
                status_code = status.HTTP_429_TOO_MANY_REQUESTS
                error_type = "rate_limiting"
                message = "Too many requests to the AI service. You are being rate limited."
        
        elif isinstance(e, openai.NotFoundError):
            status_code = status.HTTP_400_BAD_REQUEST
            error_type = "invalid_model_name"
            message = "The requested AI model name is invalid or does not exist."
            
        elif isinstance(e, openai.APITimeoutError):
            status_code = status.HTTP_504_GATEWAY_TIMEOUT
            error_type = "network_timeout"
            message = "The connection to the AI service timed out. Please try again."
            
        elif isinstance(e, openai.InternalServerError):
            status_code = status.HTTP_502_BAD_GATEWAY
            error_type = "internal_error"
            message = "The AI service encountered an internal error. Please try again later."
            
        elif isinstance(e, openai.APIConnectionError):
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            error_type = "network_timeout"
            message = "Failed to connect to the AI service. Please check your network connection."
            
        elif isinstance(e, openai.APIStatusError):
            status_code = e.status_code
            err_msg = str(e).lower()
            if status_code == 401:
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                error_type = "invalid_api_key"
                message = "Invalid LLM API key. Please check your credentials and configuration."
            elif status_code == 429:
                is_quota = "quota" in err_msg or "resource_exhausted" in err_msg
                if is_quota:
                    error_type = "quota_exceeded"
                    message = "AI service quota has been exceeded. Please check your billing details and usage limits."
                else:
                    error_type = "rate_limiting"
                    message = "Too many requests to the AI service. You are being rate limited."
            elif status_code == 404:
                status_code = status.HTTP_400_BAD_REQUEST
                error_type = "invalid_model_name"
                message = "The requested AI model name is invalid or does not exist."
            elif 500 <= status_code < 600:
                status_code = status.HTTP_502_BAD_GATEWAY
                error_type = "internal_error"
                message = "The AI service encountered an internal error. Please try again later."
    else:
        # Fallback inspection of raw exception message
        err_msg = str(e).lower()
        if "429" in err_msg or "quota" in err_msg or "resource_exhausted" in err_msg:
            status_code = status.HTTP_429_TOO_MANY_REQUESTS
            if "quota" in err_msg or "resource_exhausted" in err_msg:
                error_type = "quota_exceeded"
                message = "AI service quota has been exceeded. Please check your billing details and usage limits."
            else:
                error_type = "rate_limiting"
                message = "Too many requests to the AI service. You are being rate limited."
        elif "timeout" in err_msg or "timed out" in err_msg:
            status_code = status.HTTP_504_GATEWAY_TIMEOUT
            error_type = "network_timeout"
            message = "The connection to the AI service timed out. Please try again."
        elif "api key" in err_msg or "invalid api" in err_msg or "401" in err_msg:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            error_type = "invalid_api_key"
            message = "Invalid LLM API key. Please check your credentials and configuration."
        elif "model" in err_msg and ("not found" in err_msg or "invalid" in err_msg or "404" in err_msg):
            status_code = status.HTTP_400_BAD_REQUEST
            error_type = "invalid_model_name"
            message = "The requested AI model name is invalid or does not exist."

    # Always log diagnostic information explicitly
    logger.error(
        f"DIAGNOSTIC LOG:\n"
        f"- Exception Type: {exception_type}\n"
        f"- HTTP Status: {http_status}\n"
        f"- Response JSON: {response_json}\n"
        f"- Request Model: {request_model}\n"
        f"- Endpoint: {endpoint}\n"
        f"- Stack Trace:\n{tb_str}"
    )

    if response_json:
        logger.error(f"Complete OpenRouter response body:\n{response_json}")

    detail = {
        "message": message,
        "error_type": error_type,
    }
    if retry_after is not None:
        detail["retry_after"] = retry_after

    # Return original exception details in development mode only
    if settings.ENVIRONMENT == "development":
        detail["original_exception"] = str(e)
        detail["exception_type"] = exception_type
        detail["stack_trace"] = tb_str
        if response_json:
            detail["response_json"] = response_json

    return LLMAPIException(status_code=status_code, detail=detail)

