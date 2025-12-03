"""
OpenTelemetry tracing configuration and utilities for prompt execution.
"""

import os
from dataclasses import dataclass
from functools import wraps
from typing import Optional, Dict, Any, Callable, TypeVar
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.trace import Status, StatusCode, Span
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator


# Try to import OTLP exporter (optional)
try:
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    OTLP_AVAILABLE = True
except ImportError:
    OTLP_AVAILABLE = False


F = TypeVar('F', bound=Callable[..., Any])


@dataclass
class TracingConfig:
    """Configuration for OpenTelemetry tracing."""
    service_name: str = "blogus"
    service_version: str = "0.2.0"
    environment: str = "development"
    otlp_endpoint: Optional[str] = None
    console_export: bool = False
    enabled: bool = True

    @classmethod
    def from_env(cls) -> "TracingConfig":
        """Create configuration from environment variables."""
        return cls(
            service_name=os.environ.get("OTEL_SERVICE_NAME", "blogus"),
            service_version=os.environ.get("OTEL_SERVICE_VERSION", "0.2.0"),
            environment=os.environ.get("OTEL_ENVIRONMENT", "development"),
            otlp_endpoint=os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"),
            console_export=os.environ.get("OTEL_CONSOLE_EXPORT", "").lower() == "true",
            enabled=os.environ.get("OTEL_ENABLED", "true").lower() == "true"
        )


_tracer_provider: Optional[TracerProvider] = None
_initialized: bool = False


def init_tracing(config: Optional[TracingConfig] = None) -> None:
    """Initialize OpenTelemetry tracing."""
    global _tracer_provider, _initialized

    if _initialized:
        return

    if config is None:
        config = TracingConfig.from_env()

    if not config.enabled:
        _initialized = True
        return

    # Create resource with service info
    resource = Resource.create({
        SERVICE_NAME: config.service_name,
        "service.version": config.service_version,
        "deployment.environment": config.environment,
    })

    # Create tracer provider
    _tracer_provider = TracerProvider(resource=resource)

    # Add OTLP exporter if endpoint is configured
    if config.otlp_endpoint and OTLP_AVAILABLE:
        otlp_exporter = OTLPSpanExporter(endpoint=config.otlp_endpoint)
        _tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    # Add console exporter if enabled
    if config.console_export:
        console_exporter = ConsoleSpanExporter()
        _tracer_provider.add_span_processor(BatchSpanProcessor(console_exporter))

    # Set as global tracer provider
    trace.set_tracer_provider(_tracer_provider)
    _initialized = True


def shutdown_tracing() -> None:
    """Shutdown tracing and flush any pending spans."""
    global _tracer_provider, _initialized

    if _tracer_provider is not None:
        _tracer_provider.shutdown()
        _tracer_provider = None

    _initialized = False


def get_tracer(name: str = "blogus") -> trace.Tracer:
    """Get a tracer instance."""
    if not _initialized:
        init_tracing()
    return trace.get_tracer(name)


def create_span_context() -> Dict[str, str]:
    """Create span context for propagation."""
    carrier: Dict[str, str] = {}
    propagator = TraceContextTextMapPropagator()
    propagator.inject(carrier)
    return carrier


def get_current_trace_info() -> Dict[str, Optional[str]]:
    """Get current trace and span IDs."""
    span = trace.get_current_span()
    if span and span.is_recording():
        ctx = span.get_span_context()
        return {
            "trace_id": format(ctx.trace_id, '032x'),
            "span_id": format(ctx.span_id, '016x')
        }
    return {"trace_id": None, "span_id": None}


@contextmanager
def trace_prompt_execution(
    prompt_name: str,
    version: int,
    model_id: str,
    attributes: Optional[Dict[str, Any]] = None
):
    """
    Context manager for tracing prompt execution.

    Usage:
        with trace_prompt_execution("my-prompt", 1, "gpt-4o") as span:
            result = execute_prompt(...)
            span.set_attribute("response.tokens", result.tokens)
    """
    tracer = get_tracer()

    span_attributes = {
        "prompt.name": prompt_name,
        "prompt.version": version,
        "llm.model": model_id,
        "llm.provider": _get_provider_from_model(model_id),
    }

    if attributes:
        span_attributes.update(attributes)

    with tracer.start_as_current_span(
        name=f"prompt.execute.{prompt_name}",
        kind=trace.SpanKind.CLIENT,
        attributes=span_attributes
    ) as span:
        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise


@contextmanager
def trace_llm_call(
    model_id: str,
    operation: str = "completion",
    attributes: Optional[Dict[str, Any]] = None
):
    """
    Context manager for tracing individual LLM API calls.

    Usage:
        with trace_llm_call("gpt-4o", "completion") as span:
            response = litellm.completion(...)
            span.set_attribute("llm.response.tokens", response.usage.total_tokens)
    """
    tracer = get_tracer()

    span_attributes = {
        "llm.model": model_id,
        "llm.operation": operation,
        "llm.provider": _get_provider_from_model(model_id),
    }

    if attributes:
        span_attributes.update(attributes)

    with tracer.start_as_current_span(
        name=f"llm.{operation}",
        kind=trace.SpanKind.CLIENT,
        attributes=span_attributes
    ) as span:
        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise


def trace_execution(
    name: str,
    kind: trace.SpanKind = trace.SpanKind.INTERNAL,
    attributes: Optional[Dict[str, Any]] = None
) -> Callable[[F], F]:
    """
    Decorator for tracing function execution.

    Usage:
        @trace_execution("my.operation")
        async def my_function():
            ...
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.start_as_current_span(
                name=name,
                kind=kind,
                attributes=attributes or {}
            ) as span:
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.start_as_current_span(
                name=name,
                kind=kind,
                attributes=attributes or {}
            ) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore

    return decorator


def record_llm_metrics(
    span: Span,
    input_tokens: int,
    output_tokens: int,
    total_tokens: int,
    latency_ms: float,
    cost_usd: float
) -> None:
    """Record LLM execution metrics on a span."""
    span.set_attribute("llm.usage.prompt_tokens", input_tokens)
    span.set_attribute("llm.usage.completion_tokens", output_tokens)
    span.set_attribute("llm.usage.total_tokens", total_tokens)
    span.set_attribute("llm.latency_ms", latency_ms)
    span.set_attribute("llm.cost_usd", cost_usd)


def record_error(span: Span, error: Exception, error_type: str = "unknown") -> None:
    """Record an error on a span."""
    span.set_attribute("error.type", error_type)
    span.set_attribute("error.message", str(error))
    span.set_status(Status(StatusCode.ERROR, str(error)))
    span.record_exception(error)


def _get_provider_from_model(model_id: str) -> str:
    """Infer provider from model ID."""
    model_lower = model_id.lower()
    if model_lower.startswith("gpt-"):
        return "openai"
    elif model_lower.startswith("claude-"):
        return "anthropic"
    elif model_lower.startswith("groq/"):
        return "groq"
    elif model_lower.startswith("gemini"):
        return "google"
    elif model_lower.startswith("mistral"):
        return "mistral"
    elif "/" in model_id:
        return model_id.split("/")[0]
    return "unknown"
