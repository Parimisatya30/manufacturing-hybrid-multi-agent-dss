
"""Smoke test for the local Ollama provider."""

from app.llm import OllamaProvider


def main() -> None:
    provider = OllamaProvider()

    response = provider.generate(
        prompt="Explain predictive maintenance in two sentences.",
        system_prompt=(
            "You are a manufacturing engineering assistant. "
            "Be concise and factual."
        ),
    )

    print("Provider: Ollama")
    print("Model: gemma3:4b")
    print(f"Response: {response}")


if __name__ == "__main__":
    main()