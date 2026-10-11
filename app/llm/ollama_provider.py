
"""Local LLM provider backed by the Ollama HTTP API."""

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class OllamaProviderError(RuntimeError):
    """Raised when Ollama cannot generate a response."""


class OllamaProvider:
    """Generate text using a locally running Ollama model."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "gemma3:4b",
        timeout: int = 120,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:
        """Generate a non-streaming response from Ollama."""

        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must not be blank")

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }

        if system_prompt:
            payload["system"] = system_prompt

        request = Request(
            url=f"{self.base_url}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))

        except HTTPError as exc:
            raise OllamaProviderError(
                f"Ollama returned HTTP {exc.code}."
            ) from exc

        except (URLError, TimeoutError, OSError) as exc:
            raise OllamaProviderError(
                "Could not connect to Ollama or the request timed out."
            ) from exc

        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise OllamaProviderError(
                "Ollama returned an invalid response."
            ) from exc

        generated_text = result.get("response")

        if not isinstance(generated_text, str) or not generated_text.strip():
            raise OllamaProviderError(
                "Ollama returned an empty response."
            )

        return generated_text.strip()