"""
Single point of contact with the OpenAI API. Every chat completion and
embedding call in the app goes through this service so retry/error/
rate-limit behavior is consistent and centralized.
"""

from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AsyncOpenAI,
    RateLimitError,
)
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import get_settings
from app.core.exceptions import ExternalServiceException
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

_RETRYABLE = (RateLimitError, APIConnectionError, APITimeoutError)


class OpenAIService:
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY is not set — chat/embedding calls will fail until configured.")
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    def _ensure_configured(self) -> None:
        if not settings.OPENAI_API_KEY:
            raise ExternalServiceException(
                "OpenAI API key is not configured on this server. Set OPENAI_API_KEY in your environment."
            )

    @retry(
        reraise=True,
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=1, max=20),
        retry=retry_if_exception_type(_RETRYABLE),
    )
    async def chat_completion(
        self,
        system_prompt: str,
        messages: list[dict],
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ) -> str:
        self._ensure_configured()
        try:
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_CHAT_MODEL,
                messages=[{"role": "system", "content": system_prompt}, *messages],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except RateLimitError:
            logger.warning("OpenAI rate limit hit, retrying...")
            raise
        except (APIConnectionError, APITimeoutError):
            logger.warning("OpenAI connection/timeout error, retrying...")
            raise
        except APIError as exc:
            logger.error("OpenAI API error: %s", exc)
            raise ExternalServiceException(f"OpenAI request failed: {exc}") from exc

    @retry(
        reraise=True,
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=1, max=20),
        retry=retry_if_exception_type(_RETRYABLE),
    )
    async def create_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Batches embedding requests; OpenAI allows up to 2048 inputs per call but we chunk at 100 for latency."""
        self._ensure_configured()
        if not texts:
            return []

        all_embeddings: list[list[float]] = []
        batch_size = 100
        try:
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                response = await self.client.embeddings.create(
                    model=settings.OPENAI_EMBEDDING_MODEL, input=batch
                )
                all_embeddings.extend([item.embedding for item in response.data])
            return all_embeddings
        except RateLimitError:
            logger.warning("OpenAI embeddings rate limit hit, retrying...")
            raise
        except (APIConnectionError, APITimeoutError):
            logger.warning("OpenAI embeddings connection/timeout error, retrying...")
            raise
        except APIError as exc:
            logger.error("OpenAI embeddings API error: %s", exc)
            raise ExternalServiceException(f"OpenAI embeddings request failed: {exc}") from exc


openai_service = OpenAIService()
