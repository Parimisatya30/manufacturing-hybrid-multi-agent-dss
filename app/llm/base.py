
"""Common interface for language model providers."""

from typing import Protocol


class LLMProvider(Protocol):
    """Interface for interchangeable LLM providers."""

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:
        """Generate a response from a prompt."""
        ...