"""
Observability infrastructure package.
"""

from .tracing import (
    init_tracing,
    shutdown_tracing,
    get_tracer,
    TracingConfig,
    trace_prompt_execution,
    trace_llm_call,
    create_span_context,
    trace_execution,
    record_llm_metrics,
    record_error,
    get_current_trace_info,
)
from .instrumented_service import InstrumentedExecutor

__all__ = [
    "init_tracing",
    "shutdown_tracing",
    "get_tracer",
    "TracingConfig",
    "trace_prompt_execution",
    "trace_llm_call",
    "create_span_context",
    "trace_execution",
    "record_llm_metrics",
    "record_error",
    "get_current_trace_info",
    "InstrumentedExecutor",
]
