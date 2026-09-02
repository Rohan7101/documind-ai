import time
from typing import Optional

from app.ai.base import AIProvider
from app.ai.providers.mock import MockAIProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.core.config import settings
from app.core.exceptions import (
    AIProviderNotConfiguredException,
    AISummarizationFailedException,
    AITextTooLargeException,
)
from app.core.logging import logger


class AIService:
    """Service layer orchestrating AI provider selection, input validation, and summarization workflows."""

    def __init__(self, provider: Optional[AIProvider] = None) -> None:
        self.provider = provider or self._resolve_provider()

    @staticmethod
    def _resolve_provider() -> AIProvider:
        """Instantiate the configured AI provider based on application settings."""
        provider_name = (settings.AI_PROVIDER or "mock").lower().strip()

        if provider_name == "mock":
            return MockAIProvider()
        elif provider_name == "openai":
            return OpenAIProvider()
        else:
            logger.error(f"Unrecognized AI_PROVIDER configured: '{provider_name}'")
            raise AIProviderNotConfiguredException(
                f"Unsupported AI provider '{provider_name}'. Supported providers: 'mock', 'openai'."
            )

    async def summarize_text(self, text: Optional[str]) -> str:
        """Validate input text, enforce size boundaries, and generate a summary using the configured provider.

        Args:
            text: The text extracted from the document.

        Returns:
            The generated summary text.

        Raises:
            AISummarizationFailedException: If text is empty or invalid.
            AITextTooLargeException: If text exceeds AI_MAX_INPUT_CHARS.
            AIProviderNotConfiguredException: If provider configuration is invalid.
            AIProviderErrorException: If upstream provider returns an error.
        """
        if text is None or not text.strip():
            logger.warning("Attempted to summarize empty or whitespace-only text.")
            raise AISummarizationFailedException("Cannot summarize empty or whitespace-only document text.")

        cleaned_text = text.strip()
        char_count = len(cleaned_text)

        if char_count > settings.AI_MAX_INPUT_CHARS:
            logger.warning(
                f"Document text length ({char_count} chars) exceeds configured limit ({settings.AI_MAX_INPUT_CHARS} chars)."
            )
            raise AITextTooLargeException(
                f"Document text ({char_count} characters) exceeds the maximum allowed limit of {settings.AI_MAX_INPUT_CHARS} characters."
            )

        logger.info(
            f"Initiating summarization via provider='{self.provider.provider_name}' for input of {char_count} characters."
        )
        start_time = time.perf_counter()

        summary = await self.provider.generate_summary(cleaned_text)
        elapsed = time.perf_counter() - start_time

        final_summary = summary.strip()
        if not final_summary:
            raise AISummarizationFailedException("AI provider generated an empty summary.")

        logger.info(
            f"Summarization completed in {elapsed:.2f}s via provider='{self.provider.provider_name}'. "
            f"Summary length: {len(final_summary)} characters."
        )
        return final_summary
