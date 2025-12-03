"""
Instrumented registry service with OpenTelemetry tracing.
"""

import time
from typing import Optional, Dict
from datetime import datetime

from opentelemetry import trace

from .tracing import (
    get_tracer, trace_prompt_execution, trace_llm_call,
    record_llm_metrics, record_error, get_current_trace_info
)
from ...application.dto import (
    ExecuteDeploymentRequest, ExecuteDeploymentResponse, ExecutionResultDto
)
from ...domain.models.registry import (
    PromptDeployment, PromptName, DeploymentStatus,
    ExecutionMetrics, MetricsStore, PromptRegistry, ModelParameters
)
from ...shared.exceptions import ConfigurationError


# Approximate token costs per 1K tokens (USD)
MODEL_COSTS = {
    "gpt-4o": {"input": 0.0025, "output": 0.01},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
    "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
    "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
    "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
}


class InstrumentedExecutor:
    """
    Instrumented prompt executor with OpenTelemetry tracing.

    This class provides traced execution of prompts, recording metrics
    with trace context for correlation.
    """

    def __init__(
        self,
        registry: PromptRegistry,
        metrics_store: MetricsStore,
    ):
        self._registry = registry
        self._metrics_store = metrics_store
        self._tracer = get_tracer("blogus.executor")

    async def execute(
        self, request: ExecuteDeploymentRequest
    ) -> ExecuteDeploymentResponse:
        """Execute a prompt deployment with full tracing."""
        # Get deployment
        deployment = await self._get_deployment(request.name)

        # Select version
        version, model_override = self._select_version(deployment)

        # Get content and config for selected version
        content, model_config = self._get_version_content(deployment, version)

        # Apply model override
        model_id = model_override if model_override else model_config.model_id

        # Render template if needed
        if request.variables:
            try:
                content = deployment.render(request.variables)
            except ValueError as e:
                raise ConfigurationError(str(e))

        # Execute with tracing
        with trace_prompt_execution(
            prompt_name=request.name,
            version=version,
            model_id=model_id,
            attributes={
                "prompt.is_template": deployment.is_template,
                "prompt.category": deployment.category,
                "prompt.has_variables": bool(request.variables),
            }
        ) as span:
            # Execute the LLM call
            start_time = time.time()
            result, token_info = await self._execute_llm_traced(
                content, model_id, model_config.parameters, span
            )
            latency_ms = (time.time() - start_time) * 1000

            # Calculate cost
            cost = self._estimate_cost(
                model_id,
                token_info["input_tokens"],
                token_info["output_tokens"]
            )

            # Record metrics on span
            record_llm_metrics(
                span,
                input_tokens=token_info["input_tokens"],
                output_tokens=token_info["output_tokens"],
                total_tokens=token_info["total_tokens"],
                latency_ms=latency_ms,
                cost_usd=cost
            )

            # Get trace context for metrics storage
            trace_info = get_current_trace_info()

            # Record metrics with trace context
            metrics = ExecutionMetrics(
                prompt_name=request.name,
                version=version,
                model_used=model_id,
                latency_ms=latency_ms,
                input_tokens=token_info["input_tokens"],
                output_tokens=token_info["output_tokens"],
                total_tokens=token_info["total_tokens"],
                estimated_cost_usd=cost,
                success=True,
                executed_at=datetime.now(),
                trace_id=trace_info.get("trace_id"),
                span_id=trace_info.get("span_id")
            )
            await self._metrics_store.record(metrics)

            # Execute shadow version if configured
            shadow_response = None
            if deployment.traffic_config and deployment.traffic_config.shadow_version:
                shadow_response = await self._execute_shadow_traced(
                    deployment, request.variables, span
                )

            return ExecuteDeploymentResponse(
                result=ExecutionResultDto(
                    prompt_name=request.name,
                    version=version,
                    model_used=model_id,
                    response=result,
                    latency_ms=latency_ms,
                    input_tokens=token_info["input_tokens"],
                    output_tokens=token_info["output_tokens"],
                    total_tokens=token_info["total_tokens"],
                    estimated_cost_usd=cost,
                    shadow_response=shadow_response
                )
            )

    async def _get_deployment(self, name: str) -> PromptDeployment:
        """Get deployment with validation."""
        deployment = await self._registry.get_by_name(PromptName(name))
        if not deployment:
            raise ConfigurationError(f"Deployment '{name}' not found")

        if deployment.status != DeploymentStatus.ACTIVE:
            raise ConfigurationError(
                f"Deployment '{name}' is not active (status: {deployment.status.value})"
            )

        return deployment

    def _select_version(
        self, deployment: PromptDeployment
    ) -> tuple[int, Optional[str]]:
        """Select version based on traffic configuration."""
        import random

        if not deployment.traffic_config or not deployment.traffic_config.routes:
            return deployment.version, None

        random_value = random.random()
        route = deployment.traffic_config.select_route(random_value)
        return route.version, route.model_override

    def _get_version_content(
        self, deployment: PromptDeployment, version: int
    ) -> tuple[str, any]:
        """Get content and config for a specific version."""
        if version == deployment.version:
            return deployment.content, deployment.model_config

        version_record = deployment.get_version(version)
        if not version_record:
            raise ConfigurationError(f"Version {version} not found")

        return version_record.content, version_record.model_config

    async def _execute_llm_traced(
        self,
        content: str,
        model_id: str,
        parameters: ModelParameters,
        parent_span: trace.Span
    ) -> tuple[str, Dict]:
        """Execute LLM call with tracing."""
        from litellm import completion

        with trace_llm_call(
            model_id=model_id,
            operation="completion",
            attributes={
                "llm.request.max_tokens": parameters.max_tokens,
                "llm.request.temperature": parameters.temperature,
            }
        ) as span:
            response = completion(
                model=model_id,
                messages=[{"role": "user", "content": content}],
                **parameters.to_dict()
            )

            result = response.choices[0].message.content

            # Extract token usage
            usage = response.usage
            token_info = {
                "input_tokens": usage.prompt_tokens if usage else 0,
                "output_tokens": usage.completion_tokens if usage else 0,
                "total_tokens": usage.total_tokens if usage else 0
            }

            # Record on this span too
            span.set_attribute("llm.response.tokens", token_info["total_tokens"])

            return result, token_info

    async def _execute_shadow_traced(
        self,
        deployment: PromptDeployment,
        variables: Optional[Dict[str, str]],
        parent_span: trace.Span
    ) -> Optional[str]:
        """Execute shadow version with tracing."""
        if not deployment.traffic_config or not deployment.traffic_config.shadow_version:
            return None

        tracer = get_tracer()

        with tracer.start_as_current_span(
            name="prompt.shadow_execution",
            kind=trace.SpanKind.CLIENT,
            attributes={
                "prompt.name": deployment.name.value,
                "prompt.shadow_version": deployment.traffic_config.shadow_version,
            }
        ) as span:
            try:
                shadow_version = deployment.traffic_config.shadow_version
                version_record = deployment.get_version(shadow_version)
                if not version_record:
                    span.set_attribute("shadow.skipped", "version_not_found")
                    return None

                content = version_record.content
                if variables and deployment.is_template:
                    import re
                    result = content
                    for var_name, value in variables.items():
                        pattern = r'\{\{\s*' + re.escape(var_name) + r'\s*\}\}'
                        result = re.sub(pattern, value, result)
                    content = result

                start_time = time.time()
                result, token_info = await self._execute_llm_traced(
                    content,
                    version_record.model_config.model_id,
                    version_record.model_config.parameters,
                    span
                )
                latency_ms = (time.time() - start_time) * 1000

                cost = self._estimate_cost(
                    version_record.model_config.model_id,
                    token_info["input_tokens"],
                    token_info["output_tokens"]
                )

                # Record shadow metrics
                trace_info = get_current_trace_info()
                metrics = ExecutionMetrics(
                    prompt_name=deployment.name.value,
                    version=shadow_version,
                    model_used=version_record.model_config.model_id,
                    latency_ms=latency_ms,
                    input_tokens=token_info["input_tokens"],
                    output_tokens=token_info["output_tokens"],
                    total_tokens=token_info["total_tokens"],
                    estimated_cost_usd=cost,
                    success=True,
                    executed_at=datetime.now(),
                    shadow_execution=True,
                    trace_id=trace_info.get("trace_id"),
                    span_id=trace_info.get("span_id")
                )
                await self._metrics_store.record(metrics)

                return result

            except Exception as e:
                record_error(span, e, "shadow_execution_error")
                return None

    def _estimate_cost(
        self, model_id: str, input_tokens: int, output_tokens: int
    ) -> float:
        """Estimate cost based on token usage."""
        costs = MODEL_COSTS.get(model_id, {"input": 0.001, "output": 0.002})
        input_cost = (input_tokens / 1000) * costs["input"]
        output_cost = (output_tokens / 1000) * costs["output"]
        return input_cost + output_cost
