"""
TortoiseORM repository implementations for the Prompt Registry.
"""

import uuid
from typing import Optional, List, Set, Dict
from datetime import datetime, timedelta

from tortoise.expressions import Q
from tortoise.functions import Count, Avg, Sum

from .models import (
    DeploymentModel, VersionHistoryModel, TrafficRouteModel,
    ExecutionMetricModel, DeploymentStatusEnum
)
from ...domain.models.registry import (
    PromptDeployment, PromptRegistry, DeploymentId, PromptName,
    DeploymentStatus, ModelConfig, ModelParameters, VersionRecord,
    TrafficConfig, TrafficRoute, MetricsStore, ExecutionMetrics, AggregatedMetrics
)
from ...shared.exceptions import ConfigurationError


class TortoisePromptRegistry(PromptRegistry):
    """TortoiseORM implementation of PromptRegistry."""

    async def register(self, deployment: PromptDeployment) -> PromptDeployment:
        """Register a new prompt deployment."""
        # Check for name collision
        exists = await DeploymentModel.filter(name=deployment.name.value).exists()
        if exists:
            raise ConfigurationError(
                f"Deployment with name '{deployment.name.value}' already exists"
            )

        # Create deployment
        db_deployment = await DeploymentModel.create(
            id=uuid.UUID(deployment.id.value),
            name=deployment.name.value,
            description=deployment.description,
            content=deployment.content,
            goal=deployment.goal,
            model_id=deployment.model_config.model_id,
            temperature=deployment.model_config.parameters.temperature,
            max_tokens=deployment.model_config.parameters.max_tokens,
            top_p=deployment.model_config.parameters.top_p,
            frequency_penalty=deployment.model_config.parameters.frequency_penalty,
            presence_penalty=deployment.model_config.parameters.presence_penalty,
            stop_sequences=deployment.model_config.parameters.stop_sequences,
            fallback_models=deployment.model_config.fallback_models,
            tags=list(deployment.tags),
            category=deployment.category,
            author=deployment.author,
            version=deployment.version,
            status=DeploymentStatusEnum(deployment.status.value)
        )

        return await self._to_domain(db_deployment)

    async def get_by_id(self, deployment_id: DeploymentId) -> Optional[PromptDeployment]:
        """Get deployment by ID."""
        db_deployment = await DeploymentModel.filter(
            id=uuid.UUID(deployment_id.value)
        ).prefetch_related("version_history", "traffic_routes").first()

        if not db_deployment:
            return None

        return await self._to_domain(db_deployment)

    async def get_by_name(self, name: PromptName) -> Optional[PromptDeployment]:
        """Get deployment by name."""
        db_deployment = await DeploymentModel.filter(
            name=name.value
        ).prefetch_related("version_history", "traffic_routes").first()

        if not db_deployment:
            return None

        return await self._to_domain(db_deployment)

    async def list_all(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[DeploymentStatus] = None
    ) -> List[PromptDeployment]:
        """List all deployments with pagination."""
        query = DeploymentModel.all()

        if status:
            query = query.filter(status=DeploymentStatusEnum(status.value))

        db_deployments = await query.offset(offset).limit(limit).prefetch_related(
            "version_history", "traffic_routes"
        )

        return [await self._to_domain(d) for d in db_deployments]

    async def search(
        self,
        query: Optional[str] = None,
        tags: Optional[Set[str]] = None,
        category: Optional[str] = None,
        author: Optional[str] = None
    ) -> List[PromptDeployment]:
        """Search deployments by various criteria."""
        db_query = DeploymentModel.all()

        if query:
            db_query = db_query.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(content__icontains=query)
            )

        if category:
            db_query = db_query.filter(category=category)

        if author:
            db_query = db_query.filter(author=author)

        db_deployments = await db_query.prefetch_related(
            "version_history", "traffic_routes"
        )

        # Filter by tags in Python (JSON field filtering is DB-specific)
        if tags:
            db_deployments = [
                d for d in db_deployments
                if any(tag in d.tags for tag in tags)
            ]

        return [await self._to_domain(d) for d in db_deployments]

    async def update(self, deployment: PromptDeployment) -> PromptDeployment:
        """Update an existing deployment."""
        db_deployment = await DeploymentModel.filter(
            id=uuid.UUID(deployment.id.value)
        ).first()

        if not db_deployment:
            raise ConfigurationError(
                f"Deployment with ID '{deployment.id.value}' does not exist"
            )

        # Update fields
        db_deployment.description = deployment.description
        db_deployment.content = deployment.content
        db_deployment.goal = deployment.goal
        db_deployment.model_id = deployment.model_config.model_id
        db_deployment.temperature = deployment.model_config.parameters.temperature
        db_deployment.max_tokens = deployment.model_config.parameters.max_tokens
        db_deployment.top_p = deployment.model_config.parameters.top_p
        db_deployment.frequency_penalty = deployment.model_config.parameters.frequency_penalty
        db_deployment.presence_penalty = deployment.model_config.parameters.presence_penalty
        db_deployment.stop_sequences = deployment.model_config.parameters.stop_sequences
        db_deployment.fallback_models = deployment.model_config.fallback_models
        db_deployment.tags = list(deployment.tags)
        db_deployment.category = deployment.category
        db_deployment.author = deployment.author
        db_deployment.version = deployment.version
        db_deployment.status = DeploymentStatusEnum(deployment.status.value)

        if deployment.traffic_config:
            db_deployment.shadow_version = deployment.traffic_config.shadow_version
        else:
            db_deployment.shadow_version = None

        await db_deployment.save()

        # Update version history
        for vr in deployment.version_history:
            exists = await VersionHistoryModel.filter(
                deployment=db_deployment,
                version=vr.version
            ).exists()

            if not exists:
                await VersionHistoryModel.create(
                    id=uuid.uuid4(),
                    deployment=db_deployment,
                    version=vr.version,
                    content_hash=vr.content_hash,
                    content=vr.content,
                    model_id=vr.model_config.model_id,
                    temperature=vr.model_config.parameters.temperature,
                    max_tokens=vr.model_config.parameters.max_tokens,
                    top_p=vr.model_config.parameters.top_p,
                    frequency_penalty=vr.model_config.parameters.frequency_penalty,
                    presence_penalty=vr.model_config.parameters.presence_penalty,
                    stop_sequences=vr.model_config.parameters.stop_sequences,
                    fallback_models=vr.model_config.fallback_models,
                    created_by=vr.created_by,
                    change_summary=vr.change_summary
                )

        # Update traffic routes
        await TrafficRouteModel.filter(deployment=db_deployment).delete()

        if deployment.traffic_config:
            for route in deployment.traffic_config.routes:
                await TrafficRouteModel.create(
                    id=uuid.uuid4(),
                    deployment=db_deployment,
                    version=route.version,
                    weight=route.weight,
                    model_override=route.model_override
                )

        return await self.get_by_id(deployment.id)

    async def delete(self, name: PromptName) -> bool:
        """Delete a deployment by name."""
        deleted_count = await DeploymentModel.filter(name=name.value).delete()
        return deleted_count > 0

    async def exists(self, name: PromptName) -> bool:
        """Check if a deployment with the given name exists."""
        return await DeploymentModel.filter(name=name.value).exists()

    async def _to_domain(self, db_deployment: DeploymentModel) -> PromptDeployment:
        """Convert database model to domain model."""
        # Build model config
        parameters = ModelParameters(
            temperature=db_deployment.temperature,
            max_tokens=db_deployment.max_tokens,
            top_p=db_deployment.top_p,
            frequency_penalty=db_deployment.frequency_penalty,
            presence_penalty=db_deployment.presence_penalty,
            stop_sequences=db_deployment.stop_sequences or []
        )

        model_config = ModelConfig(
            model_id=db_deployment.model_id,
            parameters=parameters,
            fallback_models=db_deployment.fallback_models or []
        )

        # Build version history
        version_history = []
        for vr in await db_deployment.version_history.all():
            vr_params = ModelParameters(
                temperature=vr.temperature,
                max_tokens=vr.max_tokens,
                top_p=vr.top_p,
                frequency_penalty=vr.frequency_penalty,
                presence_penalty=vr.presence_penalty,
                stop_sequences=vr.stop_sequences or []
            )
            vr_config = ModelConfig(
                model_id=vr.model_id,
                parameters=vr_params,
                fallback_models=vr.fallback_models or []
            )
            version_history.append(VersionRecord(
                version=vr.version,
                content_hash=vr.content_hash,
                content=vr.content,
                model_config=vr_config,
                created_at=vr.created_at,
                created_by=vr.created_by,
                change_summary=vr.change_summary
            ))

        # Build traffic config
        traffic_config = None
        routes = await db_deployment.traffic_routes.all()
        if routes or db_deployment.shadow_version:
            traffic_routes = [
                TrafficRoute(
                    version=r.version,
                    weight=r.weight,
                    model_override=r.model_override
                )
                for r in routes
            ]
            if traffic_routes:
                traffic_config = TrafficConfig(
                    routes=traffic_routes,
                    shadow_version=db_deployment.shadow_version
                )

        return PromptDeployment(
            id=DeploymentId(str(db_deployment.id)),
            name=PromptName(db_deployment.name),
            description=db_deployment.description,
            content=db_deployment.content,
            goal=db_deployment.goal,
            model_config=model_config,
            tags=set(db_deployment.tags or []),
            category=db_deployment.category,
            author=db_deployment.author,
            version=db_deployment.version,
            version_history=version_history,
            traffic_config=traffic_config,
            status=DeploymentStatus(db_deployment.status.value),
            created_at=db_deployment.created_at,
            updated_at=db_deployment.updated_at
        )


class TortoiseMetricsStore(MetricsStore):
    """TortoiseORM implementation of MetricsStore."""

    async def record(self, metrics: ExecutionMetrics) -> None:
        """Record execution metrics."""
        await ExecutionMetricModel.create(
            id=uuid.uuid4(),
            prompt_name=metrics.prompt_name,
            version=metrics.version,
            model_used=metrics.model_used,
            latency_ms=metrics.latency_ms,
            input_tokens=metrics.input_tokens,
            output_tokens=metrics.output_tokens,
            total_tokens=metrics.total_tokens,
            estimated_cost_usd=metrics.estimated_cost_usd,
            success=metrics.success,
            error_message=metrics.error_message,
            shadow_execution=metrics.shadow_execution,
            trace_id=getattr(metrics, 'trace_id', None),
            span_id=getattr(metrics, 'span_id', None)
        )

    async def get_aggregated(
        self,
        prompt_name: str,
        version: Optional[int] = None,
        period_hours: int = 24
    ) -> AggregatedMetrics:
        """Get aggregated metrics for a prompt/version."""
        cutoff = datetime.utcnow() - timedelta(hours=period_hours)

        query = ExecutionMetricModel.filter(
            prompt_name=prompt_name,
            executed_at__gte=cutoff
        )

        if version is not None:
            query = query.filter(version=version)

        metrics = await query.all()

        if not metrics:
            return AggregatedMetrics(
                prompt_name=prompt_name,
                version=version,
                total_executions=0,
                successful_executions=0,
                failed_executions=0,
                avg_latency_ms=0.0,
                p50_latency_ms=0.0,
                p95_latency_ms=0.0,
                p99_latency_ms=0.0,
                total_tokens=0,
                total_cost_usd=0.0,
                period_start=datetime.utcnow(),
                period_end=datetime.utcnow()
            )

        # Calculate statistics
        latencies = sorted([m.latency_ms for m in metrics])
        successful = [m for m in metrics if m.success]
        failed = [m for m in metrics if not m.success]

        def percentile(sorted_list: List[float], p: float) -> float:
            if not sorted_list:
                return 0.0
            k = (len(sorted_list) - 1) * p / 100
            f = int(k)
            c = f + 1 if f + 1 < len(sorted_list) else f
            return sorted_list[f] + (k - f) * (sorted_list[c] - sorted_list[f])

        return AggregatedMetrics(
            prompt_name=prompt_name,
            version=version,
            total_executions=len(metrics),
            successful_executions=len(successful),
            failed_executions=len(failed),
            avg_latency_ms=sum(latencies) / len(latencies) if latencies else 0.0,
            p50_latency_ms=percentile(latencies, 50),
            p95_latency_ms=percentile(latencies, 95),
            p99_latency_ms=percentile(latencies, 99),
            total_tokens=sum(m.total_tokens for m in metrics),
            total_cost_usd=sum(m.estimated_cost_usd for m in metrics),
            period_start=min(m.executed_at for m in metrics),
            period_end=max(m.executed_at for m in metrics)
        )

    async def get_recent(
        self,
        prompt_name: str,
        limit: int = 100
    ) -> List[ExecutionMetrics]:
        """Get recent execution metrics."""
        db_metrics = await ExecutionMetricModel.filter(
            prompt_name=prompt_name
        ).order_by("-executed_at").limit(limit)

        return [
            ExecutionMetrics(
                prompt_name=m.prompt_name,
                version=m.version,
                model_used=m.model_used,
                latency_ms=m.latency_ms,
                input_tokens=m.input_tokens,
                output_tokens=m.output_tokens,
                total_tokens=m.total_tokens,
                estimated_cost_usd=m.estimated_cost_usd,
                success=m.success,
                error_message=m.error_message,
                executed_at=m.executed_at,
                shadow_execution=m.shadow_execution
            )
            for m in db_metrics
        ]

    async def compare_versions(
        self,
        prompt_name: str,
        versions: List[int],
        period_hours: int = 24
    ) -> Dict[int, AggregatedMetrics]:
        """Compare metrics across versions."""
        return {
            version: await self.get_aggregated(prompt_name, version, period_hours)
            for version in versions
        }
