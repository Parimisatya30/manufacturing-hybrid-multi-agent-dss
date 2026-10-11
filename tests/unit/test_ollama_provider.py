
"""Unit tests for the Ollama provider."""

import json
from unittest.mock import MagicMock, patch
from urllib.error import URLError

import pytest

from app.llm import OllamaProvider, OllamaProviderError


def test_generate_returns_response() -> None:
    provider = OllamaProvider()

    mock_response = MagicMock()
    mock_response.__enter__.return_value.read.return_value = (
        json.dumps({"response": "Maintenance explanation"}).encode("utf-8")
    )

    with patch("app.llm.ollama_provider.urlopen", return_value=mock_response) as mock_urlopen:
        result = provider.generate(
            prompt="Explain maintenance.",
            system_prompt="Be concise.",
        )

    assert result == "Maintenance explanation"
    request = mock_urlopen.call_args.args[0]
    payload = json.loads(request.data.decode("utf-8"))
    assert payload["model"] == "gemma3:4b"
    assert payload["stream"] is False
    assert payload["system"] == "Be concise."


def test_generate_rejects_blank_prompt() -> None:
    provider = OllamaProvider()

    with pytest.raises(ValueError, match="prompt must not be blank"):
        provider.generate("   ")


def test_generate_handles_connection_failure() -> None:
    provider = OllamaProvider()

    with patch(
        "app.llm.ollama_provider.urlopen",
        side_effect=URLError("connection refused"),
    ):
        with pytest.raises(OllamaProviderError, match="Could not connect"):
            provider.generate("Explain maintenance.")


def test_generate_rejects_empty_response() -> None:
    provider = OllamaProvider()

    mock_response = MagicMock()
    mock_response.__enter__.return_value.read.return_value = (
        json.dumps({"response": "  "}).encode("utf-8")
    )

    with patch(
        "app.llm.ollama_provider.urlopen",
        return_value=mock_response,
    ):
        with pytest.raises(OllamaProviderError, match="empty response"):
            provider.generate("Explain maintenance.")


def test_generate_rejects_invalid_json() -> None:
    provider = OllamaProvider()

    mock_response = MagicMock()
    mock_response.__enter__.return_value.read.return_value = b"not-json"

    with patch(
        "app.llm.ollama_provider.urlopen",
        return_value=mock_response,
    ):
        with pytest.raises(OllamaProviderError, match="invalid response"):
            provider.generate("Explain maintenance.")