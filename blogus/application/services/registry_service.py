"""
Application service for prompt registry operations.

This service handles prompt deployment management, execution with traffic routing,
and metrics collection.
"""

import random
import time
import json
import yaml
from typing import Optional, List, Dict, Set
from datetime import datetime

from ..dto import (
    DeploymentDto, DeploymentSummaryDto, ExecutionResultDto, MetricsSummaryDto,
    ModelConfigDto, ModelParametersDto, VersionRecordDto, TrafficConfigDto, TrafficRouteDto,
    RegisterDeploymentRequest, RegisterDeploymentResponse,
    UpdateDeploymentContentRequest, UpdateDeploymentModelRequest,
    SetTrafficConfigRequest, ExecuteDeploymentRequest, ExecuteDeploymentResponse,
    RollbackDeploymentRequest, GetMetricsRequest, GetMetricsResponse,
    CompareVersionsRequest, CompareVersionsResponse
)
from ...domain.models.registry import (
    PromptDeployment, PromptRegistry, DeploymentId, PromptName,
    DeploymentStatus, ModelConfig, ModelParameters, VersionRecord,
    TrafficConfig, TrafficRoute, MetricsStore, ExecutionMetrics
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


class RegistryService:
    """Application service for prompt registry operations."""

    def __init__(
        self,
        registry: PromptRegistry,
        metrics_store: MetricsStore,
        llm_provider  # LiteLLM provider for execution
    ):
        self._registry = registry
        self._metrics_store = metrics_store
        self._llm_provider = llm_provider

    # ==================== Deployment Management ====================

    async def register_deployment(
        self, request: RegisterDeploymentRequest
    ) -> RegisterDeploymentResponse:
        """Register a new prompt deployment."""
        # Create model parameters
        parameters = ModelParameters(
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p
        )

        # Create model config
        model_config = ModelConfig(
            model_id=request.model_id,
            parameters=parameters,
            fallback_models=request.fallback_models or []
        )

        # Create deployment
        deployment = PromptDeployment(
            id=DeploymentId.generate(),
            name=PromptName(request.name),
            description=request.description,
            content=request.content,
            goal=request.goal,
            model_config=model_config,
            tags=set(request.tags) if request.tags else set(),
            category=request.category,
            author=request.author
        )

        # Register in repository
        deployment = self._registry.register(deployment)

        return RegisterDeploymentResponse(
            deployment=self._to_deployment_dto(deployment)
        )

    async def get_deployment(self, name: str) -> Optional[DeploymentDto]:
        """Get a deployment by name."""
        deployment = self._registry.get_by_name(PromptName(name))
        return self._to_deployment_dto(deployment) if deployment else None

    async def list_deployments(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[DeploymentSummaryDto]:
        """List deployments with optional filters."""
        status_enum = DeploymentStatus(status) if status else None

        if category or tags:
            # Use search for filtered results
            deployments = self._registry.search(
                category=category,
                tags=set(tags) if tags else None
            )
            # Apply status filter if needed
            if status_enum:
                deployments = [d for d in deployments if d.status == status_enum]
            # Apply pagination
            deployments = deployments[offset:offset + limit]
        else:
            deployments = self._registry.list_all(limit, offset, status_enum)

        return [self._to_deployment_summary_dto(d) for d in deployments]

    async def search_deployments(
        self,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        category: Optional[str] = None,
        author: Optional[str] = None
    ) -> List[DeploymentSummaryDto]:
        """Search deployments by various criteria."""
        deployments = self._registry.search(
            query=query,
            tags=set(tags) if tags else None,
            category=category,
            author=author
        )
        return [self._to_deployment_summary_dto(d) for d in deployments]

    async def update_content(
        self, request: UpdateDeploymentContentRequest
    ) -> DeploymentDto:
        """Update deployment content (creates new version)."""
        deployment = self._registry.get_by_name(PromptName(request.name))
        if not deployment:
            raise ConfigurationError(f"Deployment '{request.name}' not found")

        deployment.update_content(
            request.new_content,
            request.author,
            request.change_summary
        )

        deployment = self._registry.update(deployment)
        return self._to_deployment_dto(deployment)

    async def update_model_config(
        self, request: UpdateDeploymentModelRequest
    ) -> DeploymentDto:
        """Update deployment model configuration (creates new version)."""
        deployment = self._registry.get_by_name(PromptName(request.name))
        if not deployment:
            raise ConfigurationError(f"Deployment '{request.name}' not found")

        # Build new parameters (use existing values for unspecified fields)
        current_params = deployment.model_config.parameters
        new_params = ModelParameters(
            temperature=request.temperature if request.temperature is not None else current_params.temperature,
            max_tokens=request.max_tokens if request.max_tokens is not None else current_params.max_tokens,
            top_p=request.top_p if request.top_p is not None else current_params.top_p,
            frequency_penalty=current_params.frequency_penalty,
            presence_penalty=current_params.presence_penalty,
            stop_sequences=current_params.stop_sequences
        )

        new_config = ModelConfig(
            model_id=request.model_id,
            parameters=new_params,
            fallback_models=request.fallback_models if request.fallback_models is not None else deployment.model_config.fallback_models
        )

        deployment.update_model_config(new_config, request.author, request.change_summary)
        deployment = self._registry.update(deployment)
        return self._to_deployment_dto(deployment)

    async def set_traffic_config(
        self, request: SetTrafficConfigRequest
    ) -> DeploymentDto:
        """Set traffic routing configuration for A/B testing."""
        deployment = self._registry.get_by_name(PromptName(request.name))
        if not deployment:
            raise ConfigurationError(f"Deployment '{request.name}' not found")

        routes = [
            TrafficRoute(
                version=r.version,
                weight=r.weight,
                model_override=r.model_override
            )
            for r in request.routes
        ]

        config = TrafficConfig(
            routes=routes,
            shadow_version=request.shadow_version
        )

        deployment.set_traffic_config(config)
        deployment = self._registry.update(deployment)
        return self._to_deployment_dto(deployment)

    async def clear_traffic_config(self, name: str) -> DeploymentDto:
        """Clear traffic configuration (route 100% to latest)."""
        deployment = self._registry.get_by_name(PromptName(name))
        if not deployment:
            raise ConfigurationError(f"Deployment '{name}' not found")

        deployment.clear_traffic_config()
        deployment = self._registry.update(deployment)
        return self._to_deployment_dto(deployment)

    async def rollback(self, request: RollbackDeploymentRequest) -> DeploymentDto:
        """Rollback deployment to a previous version."""
        deployment = self._registry.get_by_name(PromptName(request.name))
        if not deployment:
            raise ConfigurationError(f"Deployment '{request.name}' not found")

        deployment.rollback_to_version(request.target_version, request.author)
        deployment = self._registry.update(deployment)
        return self._to_deployment_dto(deployment)

    async def set_status(
        self, name: str, status: str
    ) -> DeploymentDto:
        """Update deployment status."""
        deployment = self._registry.get_by_name(PromptName(name))
        if not deployment:
            raise ConfigurationError(f"Deployment '{name}' not found")

        deployment.status = DeploymentStatus(status)
        deployment = self._registry.update(deployment)
        return self._to_deployment_dto(deployment)

    async def delete_deployment(self, name: str) -> bool:
        """Delete a deployment."""
        return self._registry.delete(PromptName(name))

    # ==================== Execution Engine ====================

    async def execute(
        self, request: ExecuteDeploymentRequest
    ) -> ExecuteDeploymentResponse:
        """Execute a prompt deployment with traffic routing."""
        deployment = self._registry.get_by_name(PromptName(request.name))
        if not deployment:
            raise ConfigurationError(f"Deployment '{request.name}' not found")

        if deployment.status != DeploymentStatus.ACTIVE:
            raise ConfigurationError(
                f"Deployment '{request.name}' is not active (status: {deployment.status.value})"
            )

        # Select version based on traffic config
        version, model_override = self._select_version(deployment)

        # Get the prompt content for selected version
        if version == deployment.version:
            content = deployment.content
            model_config = deployment.model_config
        else:
            version_record = deployment.get_version(version)
            if not version_record:
                raise ConfigurationError(f"Version {version} not found")
            content = version_record.content
            model_config = version_record.model_config

        # Apply model override if specified in traffic route
        model_id = model_override if model_override else model_config.model_id

        # Render template if variables provided
        if request.variables:
            try:
                content = deployment.render(request.variables)
            except ValueError as e:
                raise ConfigurationError(str(e))

        # Execute the prompt
        start_time = time.time()
        result, token_info = await self._execute_llm(
            content, model_id, model_config.parameters
        )
        latency_ms = (time.time() - start_time) * 1000

        # Calculate cost
        cost = self._estimate_cost(
            model_id,
            token_info["input_tokens"],
            token_info["output_tokens"]
        )

        # Record metrics
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
            executed_at=datetime.now()
        )
        self._metrics_store.record(metrics)

        # Execute shadow version if configured
        shadow_response = None
        if deployment.traffic_config and deployment.traffic_config.shadow_version:
            shadow_response = await self._execute_shadow(
                deployment, request.variables
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

    def _select_version(
        self, deployment: PromptDeployment
    ) -> tuple[int, Optional[str]]:
        """Select version based on traffic configuration."""
        if not deployment.traffic_config or not deployment.traffic_config.routes:
            return deployment.version, None

        # Select route based on random value
        random_value = random.random()
        route = deployment.traffic_config.select_route(random_value)
        return route.version, route.model_override

    async def _execute_llm(
        self,
        content: str,
        model_id: str,
        parameters: ModelParameters
    ) -> tuple[str, Dict]:
        """Execute LLM call and return result with token info."""
        from litellm import completion

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

        return result, token_info

    async def _execute_shadow(
        self,
        deployment: PromptDeployment,
        variables: Optional[Dict[str, str]]
    ) -> Optional[str]:
        """Execute shadow version (for comparison, doesn't affect main response)."""
        if not deployment.traffic_config or not deployment.traffic_config.shadow_version:
            return None

        try:
            shadow_version = deployment.traffic_config.shadow_version
            version_record = deployment.get_version(shadow_version)
            if not version_record:
                return None

            content = version_record.content
            if variables and deployment.is_template:
                # Re-render with shadow content
                import re
                result = content
                for var_name, value in variables.items():
                    pattern = r'\{\{\s*' + re.escape(var_name) + r'\s*\}\}'
                    result = re.sub(pattern, value, result)
                content = result

            start_time = time.time()
            result, token_info = await self._execute_llm(
                content,
                version_record.model_config.model_id,
                version_record.model_config.parameters
            )
            latency_ms = (time.time() - start_time) * 1000

            # Record shadow metrics
            cost = self._estimate_cost(
                version_record.model_config.model_id,
                token_info["input_tokens"],
                token_info["output_tokens"]
            )

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
                shadow_execution=True
            )
            self._metrics_store.record(metrics)

            return result

        except Exception:
            # Shadow execution failures are silent
            return None

    def _estimate_cost(
        self, model_id: str, input_tokens: int, output_tokens: int
    ) -> float:
        """Estimate cost based on token usage."""
        costs = MODEL_COSTS.get(model_id, {"input": 0.001, "output": 0.002})
        input_cost = (input_tokens / 1000) * costs["input"]
        output_cost = (output_tokens / 1000) * costs["output"]
        return input_cost + output_cost

    # ==================== Metrics ====================

    async def get_metrics(
        self, request: GetMetricsRequest
    ) -> GetMetricsResponse:
        """Get metrics for a deployment."""
        aggregated = self._metrics_store.get_aggregated(
            request.name,
            request.version,
            request.period_hours
        )

        success_rate = 0.0
        if aggregated.total_executions > 0:
            success_rate = aggregated.successful_executions / aggregated.total_executions

        return GetMetricsResponse(
            metrics=MetricsSummaryDto(
                prompt_name=aggregated.prompt_name,
                version=aggregated.version,
                total_executions=aggregated.total_executions,
                success_rate=success_rate,
                avg_latency_ms=aggregated.avg_latency_ms,
                p95_latency_ms=aggregated.p95_latency_ms,
                total_tokens=aggregated.total_tokens,
                total_cost_usd=aggregated.total_cost_usd,
                period_hours=request.period_hours
            )
        )

    async def compare_versions(
        self, request: CompareVersionsRequest
    ) -> CompareVersionsResponse:
        """Compare metrics across versions."""
        comparisons = self._metrics_store.compare_versions(
            request.name,
            request.versions,
            request.period_hours
        )

        result = {}
        for version, aggregated in comparisons.items():
            success_rate = 0.0
            if aggregated.total_executions > 0:
                success_rate = aggregated.successful_executions / aggregated.total_executions

            result[version] = MetricsSummaryDto(
                prompt_name=aggregated.prompt_name,
                version=aggregated.version,
                total_executions=aggregated.total_executions,
                success_rate=success_rate,
                avg_latency_ms=aggregated.avg_latency_ms,
                p95_latency_ms=aggregated.p95_latency_ms,
                total_tokens=aggregated.total_tokens,
                total_cost_usd=aggregated.total_cost_usd,
                period_hours=request.period_hours
            )

        return CompareVersionsResponse(comparisons=result)

    # ==================== DTO Conversion ====================

    def _to_deployment_dto(self, deployment: PromptDeployment) -> DeploymentDto:
        """Convert domain deployment to DTO."""
        return DeploymentDto(
            id=deployment.id.value,
            name=deployment.name.value,
            description=deployment.description,
            content=deployment.content,
            goal=deployment.goal,
            model_config=self._to_model_config_dto(deployment.model_config),
            tags=list(deployment.tags),
            category=deployment.category,
            author=deployment.author,
            version=deployment.version,
            version_history=[
                self._to_version_record_dto(vr)
                for vr in deployment.version_history
            ],
            traffic_config=self._to_traffic_config_dto(deployment.traffic_config) if deployment.traffic_config else None,
            status=deployment.status.value,
            is_template=deployment.is_template,
            template_variables=deployment.template_variables,
            created_at=deployment.created_at,
            updated_at=deployment.updated_at
        )

    def _to_deployment_summary_dto(
        self, deployment: PromptDeployment
    ) -> DeploymentSummaryDto:
        """Convert domain deployment to summary DTO."""
        return DeploymentSummaryDto(
            id=deployment.id.value,
            name=deployment.name.value,
            description=deployment.description,
            model_id=deployment.model_config.model_id,
            version=deployment.version,
            status=deployment.status.value,
            category=deployment.category,
            author=deployment.author,
            tags=list(deployment.tags),
            is_template=deployment.is_template,
            updated_at=deployment.updated_at
        )

    def _to_model_config_dto(self, config: ModelConfig) -> ModelConfigDto:
        """Convert model config to DTO."""
        return ModelConfigDto(
            model_id=config.model_id,
            parameters=ModelParametersDto(
                temperature=config.parameters.temperature,
                max_tokens=config.parameters.max_tokens,
                top_p=config.parameters.top_p,
                frequency_penalty=config.parameters.frequency_penalty,
                presence_penalty=config.parameters.presence_penalty,
                stop_sequences=config.parameters.stop_sequences
            ),
            fallback_models=config.fallback_models
        )

    def _to_version_record_dto(self, record: VersionRecord) -> VersionRecordDto:
        """Convert version record to DTO."""
        return VersionRecordDto(
            version=record.version,
            content_hash=record.content_hash,
            content=record.content,
            model_config=self._to_model_config_dto(record.model_config),
            created_at=record.created_at,
            created_by=record.created_by,
            change_summary=record.change_summary
        )

    def _to_traffic_config_dto(
        self, config: TrafficConfig
    ) -> TrafficConfigDto:
        """Convert traffic config to DTO."""
        return TrafficConfigDto(
            routes=[
                TrafficRouteDto(
                    version=r.version,
                    weight=r.weight,
                    model_override=r.model_override
                )
                for r in config.routes
            ],
            shadow_version=config.shadow_version
        )

    # ==================== Export/Import ====================

    async def export_deployment(
        self, name: str, format: str = "json", include_history: bool = False
    ) -> str:
        """
        Export a deployment to the specified format.

        Args:
            name: Deployment name
            format: Output format (json, yaml, markdown)
            include_history: Include version history in export

        Returns:
            Exported content as string
        """
        deployment = self._registry.get_by_name(PromptName(name))
        if not deployment:
            raise ConfigurationError(f"Deployment '{name}' not found")

        if format == "json":
            return self._export_json(deployment, include_history)
        elif format == "yaml":
            return self._export_yaml(deployment, include_history)
        elif format == "markdown":
            return self._export_markdown(deployment, include_history)
        else:
            raise ConfigurationError(f"Unsupported export format: {format}")

    async def import_deployment(
        self, content: str, format: str = "json", author: str = "import"
    ) -> DeploymentDto:
        """
        Import a deployment from the specified format.

        Args:
            content: Import content
            format: Input format (json, yaml)
            author: Author for the imported deployment

        Returns:
            Imported deployment DTO
        """
        if format == "json":
            data = json.loads(content)
        elif format == "yaml":
            data = yaml.safe_load(content)
        else:
            raise ConfigurationError(f"Unsupported import format: {format}")

        return await self._import_from_dict(data, author)

    def _export_json(
        self, deployment: PromptDeployment, include_history: bool
    ) -> str:
        """Export deployment to JSON."""
        data = self._deployment_to_export_dict(deployment, include_history)
        return json.dumps(data, indent=2, default=str)

    def _export_yaml(
        self, deployment: PromptDeployment, include_history: bool
    ) -> str:
        """Export deployment to YAML."""
        data = self._deployment_to_export_dict(deployment, include_history)
        return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)

    def _export_markdown(
        self, deployment: PromptDeployment, include_history: bool
    ) -> str:
        """Export deployment to Markdown documentation."""
        lines = [
            f"# {deployment.name.value}",
            "",
            f"> {deployment.description}",
            "",
            "## Metadata",
            "",
            f"- **Status**: {deployment.status.value}",
            f"- **Version**: {deployment.version}",
            f"- **Category**: {deployment.category}",
            f"- **Author**: {deployment.author}",
            f"- **Model**: {deployment.model_config.model_id}",
        ]

        if deployment.tags:
            lines.append(f"- **Tags**: {', '.join(deployment.tags)}")

        if deployment.goal:
            lines.extend(["", "## Goal", "", deployment.goal])

        # Model Configuration
        lines.extend([
            "",
            "## Model Configuration",
            "",
            "```yaml",
            f"model_id: {deployment.model_config.model_id}",
            f"temperature: {deployment.model_config.parameters.temperature}",
            f"max_tokens: {deployment.model_config.parameters.max_tokens}",
            f"top_p: {deployment.model_config.parameters.top_p}",
        ])
        if deployment.model_config.fallback_models:
            lines.append(f"fallback_models: {deployment.model_config.fallback_models}")
        lines.append("```")

        # Template variables
        if deployment.is_template:
            lines.extend([
                "",
                "## Template Variables",
                "",
            ])
            for var in deployment.template_variables:
                lines.append(f"- `{{{{{var}}}}}`")

        # Content
        lines.extend([
            "",
            "## Prompt Content",
            "",
            "```",
            deployment.content,
            "```",
        ])

        # Traffic configuration
        if deployment.traffic_config and deployment.traffic_config.routes:
            lines.extend([
                "",
                "## Traffic Configuration",
                "",
            ])
            for route in deployment.traffic_config.routes:
                override = f" (model: {route.model_override})" if route.model_override else ""
                lines.append(f"- Version {route.version}: {route.weight}%{override}")
            if deployment.traffic_config.shadow_version:
                lines.append(f"- Shadow: Version {deployment.traffic_config.shadow_version}")

        # Version history
        if include_history and deployment.version_history:
            lines.extend([
                "",
                "## Version History",
                "",
            ])
            for vr in reversed(deployment.version_history):
                summary = vr.change_summary or "No summary"
                lines.append(f"- **v{vr.version}** ({vr.created_at.strftime('%Y-%m-%d')}): {summary}")

        lines.extend([
            "",
            "---",
            f"*Created: {deployment.created_at.strftime('%Y-%m-%d %H:%M')}*  ",
            f"*Updated: {deployment.updated_at.strftime('%Y-%m-%d %H:%M')}*",
        ])

        return "\n".join(lines)

    def _deployment_to_export_dict(
        self, deployment: PromptDeployment, include_history: bool
    ) -> Dict:
        """Convert deployment to export dictionary."""
        data = {
            "name": deployment.name.value,
            "description": deployment.description,
            "content": deployment.content,
            "goal": deployment.goal,
            "model_config": {
                "model_id": deployment.model_config.model_id,
                "parameters": {
                    "temperature": deployment.model_config.parameters.temperature,
                    "max_tokens": deployment.model_config.parameters.max_tokens,
                    "top_p": deployment.model_config.parameters.top_p,
                    "frequency_penalty": deployment.model_config.parameters.frequency_penalty,
                    "presence_penalty": deployment.model_config.parameters.presence_penalty,
                    "stop_sequences": deployment.model_config.parameters.stop_sequences
                },
                "fallback_models": deployment.model_config.fallback_models
            },
            "category": deployment.category,
            "tags": list(deployment.tags),
            "version": deployment.version,
            "status": deployment.status.value
        }

        if include_history and deployment.version_history:
            data["version_history"] = [
                {
                    "version": vr.version,
                    "content_hash": vr.content_hash,
                    "content": vr.content,
                    "model_config": {
                        "model_id": vr.model_config.model_id,
                        "parameters": {
                            "temperature": vr.model_config.parameters.temperature,
                            "max_tokens": vr.model_config.parameters.max_tokens,
                            "top_p": vr.model_config.parameters.top_p
                        }
                    },
                    "created_at": vr.created_at.isoformat(),
                    "created_by": vr.created_by,
                    "change_summary": vr.change_summary
                }
                for vr in deployment.version_history
            ]

        return data

    async def _import_from_dict(self, data: Dict, author: str) -> DeploymentDto:
        """Import deployment from dictionary."""
        # Check if deployment already exists
        name = data.get("name")
        if not name:
            raise ConfigurationError("Import data missing 'name' field")

        if self._registry.exists(PromptName(name)):
            raise ConfigurationError(f"Deployment '{name}' already exists. Delete it first or use a different name.")

        # Extract model config
        mc_data = data.get("model_config", {})
        params_data = mc_data.get("parameters", {})

        parameters = ModelParameters(
            temperature=params_data.get("temperature", 0.7),
            max_tokens=params_data.get("max_tokens", 1000),
            top_p=params_data.get("top_p", 1.0),
            frequency_penalty=params_data.get("frequency_penalty", 0.0),
            presence_penalty=params_data.get("presence_penalty", 0.0),
            stop_sequences=params_data.get("stop_sequences", [])
        )

        model_config = ModelConfig(
            model_id=mc_data.get("model_id", "gpt-4o"),
            parameters=parameters,
            fallback_models=mc_data.get("fallback_models", [])
        )

        # Create deployment
        deployment = PromptDeployment(
            id=DeploymentId.generate(),
            name=PromptName(name),
            description=data.get("description", ""),
            content=data.get("content", ""),
            goal=data.get("goal"),
            model_config=model_config,
            tags=set(data.get("tags", [])),
            category=data.get("category", "general"),
            author=author
        )

        # Register
        deployment = self._registry.register(deployment)

        return self._to_deployment_dto(deployment)
