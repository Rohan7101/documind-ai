from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Abstract base class for all AI model providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the unique identifier/name of the provider."""
        ...

    @abstractmethod
    async def generate_summary(self, text: str) -> str:
        """Generate a concise, factual summary of the provided text.

        Args:
            text: The extracted document text to summarize.

        Returns:
            The generated summary string.

        Raises:
            AIProviderNotConfiguredException: If provider configuration is invalid or missing.
            AIProviderErrorException: If the upstream provider service returns an error.
            AISummarizationFailedException: If summary generation fails.
        """
        ...
