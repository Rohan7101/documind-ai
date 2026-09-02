from app.ai.base import AIProvider


class MockAIProvider(AIProvider):
    """Deterministic mock AI provider for testing and offline local development."""

    @property
    def provider_name(self) -> str:
        return "mock"

    async def generate_summary(self, text: str) -> str:
        """Generate a deterministic mock summary without external network calls."""
        cleaned = text.strip()
        word_count = len(cleaned.split())
        first_line = cleaned.split("\n")[0].strip()
        snippet = (first_line[:50] + "...") if len(first_line) > 50 else first_line

        return (
            f"Summary (Mock): The document discusses '{snippet}'. "
            f"It comprises approximately {word_count} words and outlines key concepts, findings, and specifications."
        )
