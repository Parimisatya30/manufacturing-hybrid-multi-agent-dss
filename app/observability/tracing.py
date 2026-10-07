from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    ConsoleSpanExporter,
)


TRACER_NAME = "manufacturing-dss"


def _configure_tracing() -> None:
    """Configure the OpenTelemetry tracer provider."""

    provider = TracerProvider()

    provider.add_span_processor(
        SimpleSpanProcessor(
            ConsoleSpanExporter()
        )
    )

    trace.set_tracer_provider(provider)


_configure_tracing()

tracer = trace.get_tracer(TRACER_NAME)