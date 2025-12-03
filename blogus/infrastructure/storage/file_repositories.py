"""
File-based repository implementations.
"""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
from datetime import datetime

from ...domain.models.prompt import Prompt, PromptRepository, PromptId, Score, Fragment, AnalysisStatus
from ...domain.models.analysis import (
    AnalysisId, AnalysisRecord, AnalysisRepository
)
from ...domain.models.testing import (
    TestCaseId, TestRunId, TestCase, TestRun, TestAssertion, TestCaseResult,
    AssertionResult, TestRepository, AssertionType, TestStatus
)
from ...domain.models.registry import (
    PromptDeployment, PromptRegistry, DeploymentId, PromptName,
    DeploymentStatus, ModelConfig, ModelParameters, VersionRecord,
    TrafficConfig, TrafficRoute, MetricsStore, ExecutionMetrics, AggregatedMetrics
)
from ...shared.exceptions import ConfigurationError


class FilePromptRepository(PromptRepository):
    """File-based implementation of PromptRepository for unified Prompt entity."""

    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.prompts_dir = storage_dir / "prompts"
        self.prompts_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, prompt: Prompt) -> None:
        """Save a prompt to file."""
        try:
            prompt_file = self.prompts_dir / f"{prompt.id.value}.json"
            data = self._prompt_to_dict(prompt)

            with open(prompt_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)

        except Exception as e:
            raise ConfigurationError(f"Failed to save prompt {prompt.id.value}: {e}")

    async def find_by_id(self, prompt_id: PromptId) -> Optional[Prompt]:
        """Find prompt by ID."""
        try:
            prompt_file = self.prompts_dir / f"{prompt_id.value}.json"
            if not prompt_file.exists():
                return None

            with open(prompt_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return self._dict_to_prompt(data)

        except Exception as e:
            raise ConfigurationError(f"Failed to load prompt {prompt_id.value}: {e}")

    async def find_all(
        self,
        category: Optional[str] = None,
        has_variables: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Prompt]:
        """Find all prompts with optional filtering."""
        prompts = []

        try:
            for prompt_file in self.prompts_dir.glob("*.json"):
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                prompt = self._dict_to_prompt(data)

                # Apply filters
                if category is not None and prompt.category != category:
                    continue
                if has_variables is not None and prompt.is_template != has_variables:
                    continue

                prompts.append(prompt)

        except Exception as e:
            raise ConfigurationError(f"Failed to load prompts: {e}")

        # Sort by usage count (most used first), then by name
        prompts.sort(key=lambda p: (-p.usage_count, p.name))

        # Apply pagination
        return prompts[offset:offset + limit]

    async def search(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        author: Optional[str] = None
    ) -> List[Prompt]:
        """Search prompts by various criteria."""
        all_prompts = await self.find_all(limit=10000)
        results = []

        for prompt in all_prompts:
            # Filter by query (searches name, description, content)
            if query:
                query_lower = query.lower()
                if not any([
                    query_lower in prompt.name.lower(),
                    query_lower in prompt.description.lower(),
                    query_lower in prompt.content.lower()
                ]):
                    continue

            # Filter by category
            if category and prompt.category != category:
                continue

            # Filter by tags (any match)
            if tags and not set(tags).intersection(prompt.tags):
                continue

            # Filter by author
            if author and prompt.author != author:
                continue

            results.append(prompt)

        return results

    async def delete(self, prompt_id: PromptId) -> bool:
        """Delete a prompt."""
        try:
            prompt_file = self.prompts_dir / f"{prompt_id.value}.json"
            if prompt_file.exists():
                prompt_file.unlink()
                return True
            return False

        except Exception as e:
            raise ConfigurationError(f"Failed to delete prompt {prompt_id.value}: {e}")

    def _prompt_to_dict(self, prompt: Prompt) -> Dict[str, Any]:
        """Convert prompt to dictionary."""
        return {
            "id": prompt.id.value,
            "name": prompt.name,
            "description": prompt.description,
            "content": prompt.content,
            "goal": prompt.goal,
            "category": prompt.category,
            "tags": list(prompt.tags),
            "author": prompt.author,
            "version": prompt.version,
            "usage_count": prompt.usage_count,
            "created_at": prompt.created_at.isoformat(),
            "updated_at": prompt.updated_at.isoformat()
        }

    def _dict_to_prompt(self, data: Dict[str, Any]) -> Prompt:
        """Convert dictionary to prompt."""
        prompt_id = PromptId(data["id"])

        # Parse timestamps
        created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now()
        updated_at = datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now()

        # Handle legacy format (old prompts with "text" field)
        content = data.get("content") or data.get("text", "")

        prompt = Prompt(
            id=prompt_id,
            name=data.get("name", data["id"]),
            description=data.get("description", ""),
            content=content,
            goal=data.get("goal"),
            category=data.get("category", "general"),
            tags=set(data.get("tags", [])),
            author=data.get("author", "unknown"),
            version=data.get("version", 1),
            usage_count=data.get("usage_count", 0),
            created_at=created_at,
            updated_at=updated_at
        )

        return prompt


class FilePromptRegistry(PromptRegistry):
    """File-based implementation of PromptRegistry for prompt deployments."""

    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.registry_dir = storage_dir / "registry"
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        # Index file for name-to-id mapping
        self._index_file = self.registry_dir / "_index.json"
        self._load_index()

    def _load_index(self) -> None:
        """Load the name-to-id index."""
        if self._index_file.exists():
            with open(self._index_file, 'r', encoding='utf-8') as f:
                self._index = json.load(f)
        else:
            self._index = {}

    def _save_index(self) -> None:
        """Save the name-to-id index."""
        with open(self._index_file, 'w', encoding='utf-8') as f:
            json.dump(self._index, f, indent=2)

    def register(self, deployment: PromptDeployment) -> PromptDeployment:
        """Register a new prompt deployment."""
        try:
            # Check for name collision
            if deployment.name.value in self._index:
                raise ConfigurationError(
                    f"Deployment with name '{deployment.name.value}' already exists"
                )

            # Save deployment
            deployment_file = self.registry_dir / f"{deployment.id.value}.json"
            data = self._deployment_to_dict(deployment)

            with open(deployment_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)

            # Update index
            self._index[deployment.name.value] = deployment.id.value
            self._save_index()

            return deployment

        except ConfigurationError:
            raise
        except Exception as e:
            raise ConfigurationError(f"Failed to register deployment: {e}")

    def get_by_id(self, deployment_id: DeploymentId) -> Optional[PromptDeployment]:
        """Get deployment by ID."""
        try:
            deployment_file = self.registry_dir / f"{deployment_id.value}.json"
            if not deployment_file.exists():
                return None

            with open(deployment_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return self._dict_to_deployment(data)

        except Exception as e:
            raise ConfigurationError(f"Failed to load deployment {deployment_id.value}: {e}")

    def get_by_name(self, name: PromptName) -> Optional[PromptDeployment]:
        """Get deployment by name."""
        deployment_id = self._index.get(name.value)
        if not deployment_id:
            return None
        return self.get_by_id(DeploymentId(deployment_id))

    def list_all(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[DeploymentStatus] = None
    ) -> List[PromptDeployment]:
        """List all deployments with pagination."""
        deployments = []

        try:
            for deployment_file in self.registry_dir.glob("*.json"):
                if deployment_file.name == "_index.json":
                    continue

                with open(deployment_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                deployment = self._dict_to_deployment(data)

                # Filter by status if provided
                if status is not None and deployment.status != status:
                    continue

                deployments.append(deployment)

            # Sort by updated_at descending
            deployments.sort(key=lambda d: d.updated_at, reverse=True)

            # Apply pagination
            return deployments[offset:offset + limit]

        except Exception as e:
            raise ConfigurationError(f"Failed to list deployments: {e}")

    def search(
        self,
        query: Optional[str] = None,
        tags: Optional[Set[str]] = None,
        category: Optional[str] = None,
        author: Optional[str] = None
    ) -> List[PromptDeployment]:
        """Search deployments by various criteria."""
        deployments = self.list_all(limit=1000)  # Get all for filtering
        results = []

        for deployment in deployments:
            # Filter by query (searches name, description, content)
            if query:
                query_lower = query.lower()
                if not any([
                    query_lower in deployment.name.value.lower(),
                    query_lower in deployment.description.lower(),
                    query_lower in deployment.content.lower()
                ]):
                    continue

            # Filter by tags (any match)
            if tags and not tags.intersection(deployment.tags):
                continue

            # Filter by category
            if category and deployment.category != category:
                continue

            # Filter by author
            if author and deployment.author != author:
                continue

            results.append(deployment)

        return results

    def update(self, deployment: PromptDeployment) -> PromptDeployment:
        """Update an existing deployment."""
        try:
            deployment_file = self.registry_dir / f"{deployment.id.value}.json"
            if not deployment_file.exists():
                raise ConfigurationError(
                    f"Deployment with ID '{deployment.id.value}' does not exist"
                )

            # Update timestamp
            deployment.updated_at = datetime.now()

            data = self._deployment_to_dict(deployment)
            with open(deployment_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)

            return deployment

        except ConfigurationError:
            raise
        except Exception as e:
            raise ConfigurationError(f"Failed to update deployment: {e}")

    def delete(self, name: PromptName) -> bool:
        """Delete a deployment by name."""
        try:
            deployment_id = self._index.get(name.value)
            if not deployment_id:
                return False

            deployment_file = self.registry_dir / f"{deployment_id}.json"
            if deployment_file.exists():
                deployment_file.unlink()

            del self._index[name.value]
            self._save_index()

            return True

        except Exception as e:
            raise ConfigurationError(f"Failed to delete deployment {name.value}: {e}")

    def exists(self, name: PromptName) -> bool:
        """Check if a deployment with the given name exists."""
        return name.value in self._index

    def _deployment_to_dict(self, deployment: PromptDeployment) -> Dict[str, Any]:
        """Convert deployment to dictionary for storage."""
        return {
            "id": deployment.id.value,
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
            "tags": list(deployment.tags),
            "category": deployment.category,
            "author": deployment.author,
            "version": deployment.version,
            "version_history": [
                {
                    "version": vr.version,
                    "content_hash": vr.content_hash,
                    "content": vr.content,
                    "model_config": {
                        "model_id": vr.model_config.model_id,
                        "parameters": {
                            "temperature": vr.model_config.parameters.temperature,
                            "max_tokens": vr.model_config.parameters.max_tokens,
                            "top_p": vr.model_config.parameters.top_p,
                            "frequency_penalty": vr.model_config.parameters.frequency_penalty,
                            "presence_penalty": vr.model_config.parameters.presence_penalty,
                            "stop_sequences": vr.model_config.parameters.stop_sequences
                        },
                        "fallback_models": vr.model_config.fallback_models
                    },
                    "created_at": vr.created_at.isoformat(),
                    "created_by": vr.created_by,
                    "change_summary": vr.change_summary
                }
                for vr in deployment.version_history
            ],
            "traffic_config": self._traffic_config_to_dict(deployment.traffic_config) if deployment.traffic_config else None,
            "status": deployment.status.value,
            "created_at": deployment.created_at.isoformat(),
            "updated_at": deployment.updated_at.isoformat()
        }

    def _traffic_config_to_dict(self, config: TrafficConfig) -> Dict[str, Any]:
        """Convert traffic config to dictionary."""
        return {
            "routes": [
                {
                    "version": route.version,
                    "weight": route.weight,
                    "model_override": route.model_override
                }
                for route in config.routes
            ],
            "shadow_version": config.shadow_version
        }

    def _dict_to_deployment(self, data: Dict[str, Any]) -> PromptDeployment:
        """Convert dictionary to deployment."""
        # Parse model config
        mc_data = data["model_config"]
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
            model_id=mc_data["model_id"],
            parameters=parameters,
            fallback_models=mc_data.get("fallback_models", [])
        )

        # Parse version history
        version_history = []
        for vr_data in data.get("version_history", []):
            vr_mc_data = vr_data["model_config"]
            vr_params_data = vr_mc_data.get("parameters", {})
            vr_params = ModelParameters(
                temperature=vr_params_data.get("temperature", 0.7),
                max_tokens=vr_params_data.get("max_tokens", 1000),
                top_p=vr_params_data.get("top_p", 1.0),
                frequency_penalty=vr_params_data.get("frequency_penalty", 0.0),
                presence_penalty=vr_params_data.get("presence_penalty", 0.0),
                stop_sequences=vr_params_data.get("stop_sequences", [])
            )
            vr_model_config = ModelConfig(
                model_id=vr_mc_data["model_id"],
                parameters=vr_params,
                fallback_models=vr_mc_data.get("fallback_models", [])
            )
            version_history.append(VersionRecord(
                version=vr_data["version"],
                content_hash=vr_data["content_hash"],
                content=vr_data["content"],
                model_config=vr_model_config,
                created_at=datetime.fromisoformat(vr_data["created_at"]),
                created_by=vr_data["created_by"],
                change_summary=vr_data.get("change_summary")
            ))

        # Parse traffic config
        traffic_config = None
        if data.get("traffic_config"):
            tc_data = data["traffic_config"]
            routes = [
                TrafficRoute(
                    version=r["version"],
                    weight=r["weight"],
                    model_override=r.get("model_override")
                )
                for r in tc_data.get("routes", [])
            ]
            traffic_config = TrafficConfig(
                routes=routes,
                shadow_version=tc_data.get("shadow_version")
            )

        # Parse timestamps
        created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now()
        updated_at = datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now()

        return PromptDeployment(
            id=DeploymentId(data["id"]),
            name=PromptName(data["name"]),
            description=data["description"],
            content=data["content"],
            goal=data.get("goal"),
            model_config=model_config,
            tags=set(data.get("tags", [])),
            category=data.get("category", "general"),
            author=data.get("author", "anonymous"),
            version=data.get("version", 1),
            version_history=version_history,
            traffic_config=traffic_config,
            status=DeploymentStatus(data.get("status", "active")),
            created_at=created_at,
            updated_at=updated_at
        )


class FileMetricsStore(MetricsStore):
    """File-based implementation of MetricsStore for execution metrics."""

    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.metrics_dir = storage_dir / "metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

    def record(self, metrics: ExecutionMetrics) -> None:
        """Record execution metrics."""
        try:
            # Store metrics in daily files per prompt
            date_str = metrics.executed_at.strftime("%Y-%m-%d")
            metrics_file = self.metrics_dir / f"{metrics.prompt_name}_{date_str}.jsonl"

            data = {
                "prompt_name": metrics.prompt_name,
                "version": metrics.version,
                "model_used": metrics.model_used,
                "latency_ms": metrics.latency_ms,
                "input_tokens": metrics.input_tokens,
                "output_tokens": metrics.output_tokens,
                "total_tokens": metrics.total_tokens,
                "estimated_cost_usd": metrics.estimated_cost_usd,
                "success": metrics.success,
                "error_message": metrics.error_message,
                "executed_at": metrics.executed_at.isoformat(),
                "shadow_execution": metrics.shadow_execution
            }

            with open(metrics_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(data, default=str) + "\n")

        except Exception as e:
            # Log but don't fail - metrics are best-effort
            pass

    def get_aggregated(
        self,
        prompt_name: str,
        version: Optional[int] = None,
        period_hours: int = 24
    ) -> AggregatedMetrics:
        """Get aggregated metrics for a prompt/version."""
        recent = self.get_recent(prompt_name, limit=10000)

        # Filter by time period
        cutoff = datetime.now().timestamp() - (period_hours * 3600)
        filtered = [m for m in recent if m.executed_at.timestamp() > cutoff]

        # Filter by version if specified
        if version is not None:
            filtered = [m for m in filtered if m.version == version]

        if not filtered:
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
                period_start=datetime.now(),
                period_end=datetime.now()
            )

        # Calculate aggregates
        latencies = sorted([m.latency_ms for m in filtered])
        successful = [m for m in filtered if m.success]
        failed = [m for m in filtered if not m.success]

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
            total_executions=len(filtered),
            successful_executions=len(successful),
            failed_executions=len(failed),
            avg_latency_ms=sum(latencies) / len(latencies) if latencies else 0.0,
            p50_latency_ms=percentile(latencies, 50),
            p95_latency_ms=percentile(latencies, 95),
            p99_latency_ms=percentile(latencies, 99),
            total_tokens=sum(m.total_tokens for m in filtered),
            total_cost_usd=sum(m.estimated_cost_usd for m in filtered),
            period_start=min(m.executed_at for m in filtered),
            period_end=max(m.executed_at for m in filtered)
        )

    def get_recent(
        self,
        prompt_name: str,
        limit: int = 100
    ) -> List[ExecutionMetrics]:
        """Get recent execution metrics."""
        metrics = []

        try:
            # Read all metrics files for this prompt
            for metrics_file in self.metrics_dir.glob(f"{prompt_name}_*.jsonl"):
                with open(metrics_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            metrics.append(ExecutionMetrics(
                                prompt_name=data["prompt_name"],
                                version=data["version"],
                                model_used=data["model_used"],
                                latency_ms=data["latency_ms"],
                                input_tokens=data["input_tokens"],
                                output_tokens=data["output_tokens"],
                                total_tokens=data["total_tokens"],
                                estimated_cost_usd=data["estimated_cost_usd"],
                                success=data["success"],
                                error_message=data.get("error_message"),
                                executed_at=datetime.fromisoformat(data["executed_at"]),
                                shadow_execution=data.get("shadow_execution", False)
                            ))

            # Sort by executed_at descending and limit
            metrics.sort(key=lambda m: m.executed_at, reverse=True)
            return metrics[:limit]

        except Exception as e:
            return []

    def compare_versions(
        self,
        prompt_name: str,
        versions: List[int],
        period_hours: int = 24
    ) -> Dict[int, AggregatedMetrics]:
        """Compare metrics across versions."""
        return {
            version: self.get_aggregated(prompt_name, version, period_hours)
            for version in versions
        }


class FileAnalysisRepository(AnalysisRepository):
    """File-based implementation of AnalysisRepository for analysis records."""

    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.analysis_dir = storage_dir / "analyses"
        self.analysis_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, analysis: AnalysisRecord) -> None:
        """Save an analysis record."""
        try:
            # Store analyses in subdirectories by prompt_id
            prompt_dir = self.analysis_dir / analysis.prompt_id.value
            prompt_dir.mkdir(parents=True, exist_ok=True)

            analysis_file = prompt_dir / f"{analysis.id.value}.json"
            data = self._analysis_to_dict(analysis)

            with open(analysis_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)

        except Exception as e:
            raise ConfigurationError(f"Failed to save analysis {analysis.id.value}: {e}")

    async def find_by_id(self, analysis_id: AnalysisId) -> Optional[AnalysisRecord]:
        """Find analysis by ID."""
        try:
            # Search all prompt directories
            for prompt_dir in self.analysis_dir.iterdir():
                if prompt_dir.is_dir():
                    analysis_file = prompt_dir / f"{analysis_id.value}.json"
                    if analysis_file.exists():
                        with open(analysis_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        return self._dict_to_analysis(data)
            return None

        except Exception as e:
            raise ConfigurationError(f"Failed to load analysis {analysis_id.value}: {e}")

    async def find_by_prompt(
        self,
        prompt_id: PromptId,
        limit: int = 10
    ) -> List[AnalysisRecord]:
        """Find all analyses for a prompt, newest first."""
        analyses = []

        try:
            prompt_dir = self.analysis_dir / prompt_id.value
            if not prompt_dir.exists():
                return []

            for analysis_file in prompt_dir.glob("*.json"):
                with open(analysis_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                analyses.append(self._dict_to_analysis(data))

            # Sort by analyzed_at descending
            analyses.sort(key=lambda a: a.analyzed_at, reverse=True)
            return analyses[:limit]

        except Exception as e:
            raise ConfigurationError(f"Failed to load analyses for prompt {prompt_id.value}: {e}")

    async def find_latest(self, prompt_id: PromptId) -> Optional[AnalysisRecord]:
        """Find the most recent analysis for a prompt."""
        analyses = await self.find_by_prompt(prompt_id, limit=1)
        return analyses[0] if analyses else None

    async def find_baseline(self, prompt_id: PromptId) -> Optional[AnalysisRecord]:
        """Find the baseline analysis for a prompt."""
        try:
            prompt_dir = self.analysis_dir / prompt_id.value
            if not prompt_dir.exists():
                return None

            for analysis_file in prompt_dir.glob("*.json"):
                with open(analysis_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if data.get("is_baseline", False):
                    return self._dict_to_analysis(data)
            return None

        except Exception as e:
            raise ConfigurationError(f"Failed to find baseline for prompt {prompt_id.value}: {e}")

    async def delete(self, analysis_id: AnalysisId) -> bool:
        """Delete an analysis record."""
        try:
            for prompt_dir in self.analysis_dir.iterdir():
                if prompt_dir.is_dir():
                    analysis_file = prompt_dir / f"{analysis_id.value}.json"
                    if analysis_file.exists():
                        analysis_file.unlink()
                        return True
            return False

        except Exception as e:
            raise ConfigurationError(f"Failed to delete analysis {analysis_id.value}: {e}")

    def _analysis_to_dict(self, analysis: AnalysisRecord) -> Dict[str, Any]:
        """Convert analysis to dictionary."""
        return {
            "id": analysis.id.value,
            "prompt_id": analysis.prompt_id.value,
            "prompt_version": analysis.prompt_version,
            "judge_model": analysis.judge_model,
            "goal_alignment": {"value": analysis.goal_alignment.value, "max_value": analysis.goal_alignment.max_value},
            "effectiveness": {"value": analysis.effectiveness.value, "max_value": analysis.effectiveness.max_value},
            "suggestions": analysis.suggestions,
            "fragments": [
                {
                    "text": f.text,
                    "fragment_type": f.fragment_type,
                    "goal_alignment": {"value": f.goal_alignment.value, "max_value": f.goal_alignment.max_value},
                    "improvement_suggestion": f.improvement_suggestion
                }
                for f in analysis.fragments
            ],
            "inferred_goal": analysis.inferred_goal,
            "status": analysis.status.value,
            "error_message": analysis.error_message,
            "analyzed_at": analysis.analyzed_at.isoformat(),
            "is_baseline": analysis.is_baseline
        }

    def _dict_to_analysis(self, data: Dict[str, Any]) -> AnalysisRecord:
        """Convert dictionary to analysis."""
        fragments = [
            Fragment(
                text=f["text"],
                fragment_type=f["fragment_type"],
                goal_alignment=Score(f["goal_alignment"]["value"], f["goal_alignment"].get("max_value", 10)),
                improvement_suggestion=f["improvement_suggestion"]
            )
            for f in data.get("fragments", [])
        ]

        return AnalysisRecord(
            id=AnalysisId(data["id"]),
            prompt_id=PromptId(data["prompt_id"]),
            prompt_version=data["prompt_version"],
            judge_model=data["judge_model"],
            goal_alignment=Score(data["goal_alignment"]["value"], data["goal_alignment"].get("max_value", 10)),
            effectiveness=Score(data["effectiveness"]["value"], data["effectiveness"].get("max_value", 10)),
            suggestions=data.get("suggestions", []),
            fragments=fragments,
            inferred_goal=data.get("inferred_goal"),
            status=AnalysisStatus(data.get("status", "completed")),
            error_message=data.get("error_message"),
            analyzed_at=datetime.fromisoformat(data["analyzed_at"]) if data.get("analyzed_at") else datetime.now(),
            is_baseline=data.get("is_baseline", False)
        )


class FileTestRepository(TestRepository):
    """File-based implementation of TestRepository for test cases and runs."""

    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.tests_dir = storage_dir / "tests"
        self.tests_dir.mkdir(parents=True, exist_ok=True)

    # Test Cases
    async def save_test_case(self, test_case: TestCase) -> None:
        """Save a test case."""
        try:
            prompt_dir = self.tests_dir / test_case.prompt_id.value / "cases"
            prompt_dir.mkdir(parents=True, exist_ok=True)

            case_file = prompt_dir / f"{test_case.id.value}.json"
            data = self._test_case_to_dict(test_case)

            with open(case_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)

        except Exception as e:
            raise ConfigurationError(f"Failed to save test case {test_case.id.value}: {e}")

    async def find_test_case_by_id(self, test_case_id: TestCaseId) -> Optional[TestCase]:
        """Find test case by ID."""
        try:
            for prompt_dir in self.tests_dir.iterdir():
                if prompt_dir.is_dir():
                    cases_dir = prompt_dir / "cases"
                    if cases_dir.exists():
                        case_file = cases_dir / f"{test_case_id.value}.json"
                        if case_file.exists():
                            with open(case_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            return self._dict_to_test_case(data)
            return None

        except Exception as e:
            raise ConfigurationError(f"Failed to load test case {test_case_id.value}: {e}")

    async def find_test_cases_by_prompt(self, prompt_id: PromptId) -> List[TestCase]:
        """Find all test cases for a prompt."""
        test_cases = []

        try:
            cases_dir = self.tests_dir / prompt_id.value / "cases"
            if not cases_dir.exists():
                return []

            for case_file in cases_dir.glob("*.json"):
                with open(case_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                test_cases.append(self._dict_to_test_case(data))

            # Sort by created_at
            test_cases.sort(key=lambda tc: tc.created_at)
            return test_cases

        except Exception as e:
            raise ConfigurationError(f"Failed to load test cases for prompt {prompt_id.value}: {e}")

    async def delete_test_case(self, test_case_id: TestCaseId) -> bool:
        """Delete a test case."""
        try:
            for prompt_dir in self.tests_dir.iterdir():
                if prompt_dir.is_dir():
                    cases_dir = prompt_dir / "cases"
                    if cases_dir.exists():
                        case_file = cases_dir / f"{test_case_id.value}.json"
                        if case_file.exists():
                            case_file.unlink()
                            return True
            return False

        except Exception as e:
            raise ConfigurationError(f"Failed to delete test case {test_case_id.value}: {e}")

    # Test Runs
    async def save_test_run(self, test_run: TestRun) -> None:
        """Save a test run."""
        try:
            runs_dir = self.tests_dir / test_run.prompt_id.value / "runs"
            runs_dir.mkdir(parents=True, exist_ok=True)

            run_file = runs_dir / f"{test_run.id.value}.json"
            data = self._test_run_to_dict(test_run)

            with open(run_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)

        except Exception as e:
            raise ConfigurationError(f"Failed to save test run {test_run.id.value}: {e}")

    async def find_test_run_by_id(self, test_run_id: TestRunId) -> Optional[TestRun]:
        """Find test run by ID."""
        try:
            for prompt_dir in self.tests_dir.iterdir():
                if prompt_dir.is_dir():
                    runs_dir = prompt_dir / "runs"
                    if runs_dir.exists():
                        run_file = runs_dir / f"{test_run_id.value}.json"
                        if run_file.exists():
                            with open(run_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            return self._dict_to_test_run(data)
            return None

        except Exception as e:
            raise ConfigurationError(f"Failed to load test run {test_run_id.value}: {e}")

    async def find_test_runs_by_prompt(
        self,
        prompt_id: PromptId,
        limit: int = 10
    ) -> List[TestRun]:
        """Find test runs for a prompt, newest first."""
        test_runs = []

        try:
            runs_dir = self.tests_dir / prompt_id.value / "runs"
            if not runs_dir.exists():
                return []

            for run_file in runs_dir.glob("*.json"):
                with open(run_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                test_runs.append(self._dict_to_test_run(data))

            # Sort by started_at descending
            test_runs.sort(key=lambda tr: tr.started_at, reverse=True)
            return test_runs[:limit]

        except Exception as e:
            raise ConfigurationError(f"Failed to load test runs for prompt {prompt_id.value}: {e}")

    async def find_latest_test_run(self, prompt_id: PromptId) -> Optional[TestRun]:
        """Find the most recent test run for a prompt."""
        runs = await self.find_test_runs_by_prompt(prompt_id, limit=1)
        return runs[0] if runs else None

    def _test_case_to_dict(self, test_case: TestCase) -> Dict[str, Any]:
        """Convert test case to dictionary."""
        return {
            "id": test_case.id.value,
            "prompt_id": test_case.prompt_id.value,
            "name": test_case.name,
            "description": test_case.description,
            "input_variables": test_case.input_variables,
            "expected_behavior": test_case.expected_behavior,
            "assertions": [
                {
                    "assertion_type": a.assertion_type.value,
                    "value": a.value,
                    "threshold": a.threshold
                }
                for a in test_case.assertions
            ],
            "tags": test_case.tags,
            "goal_relevance": {
                "value": test_case.goal_relevance.value,
                "max_value": test_case.goal_relevance.max_value
            } if test_case.goal_relevance else None,
            "created_by": test_case.created_by,
            "created_at": test_case.created_at.isoformat()
        }

    def _dict_to_test_case(self, data: Dict[str, Any]) -> TestCase:
        """Convert dictionary to test case."""
        assertions = [
            TestAssertion(
                assertion_type=AssertionType(a["assertion_type"]),
                value=a["value"],
                threshold=a.get("threshold", 0.8)
            )
            for a in data.get("assertions", [])
        ]

        goal_relevance = None
        if data.get("goal_relevance"):
            goal_relevance = Score(
                data["goal_relevance"]["value"],
                data["goal_relevance"].get("max_value", 10)
            )

        return TestCase(
            id=TestCaseId(data["id"]),
            prompt_id=PromptId(data["prompt_id"]),
            name=data["name"],
            description=data.get("description", ""),
            input_variables=data.get("input_variables", {}),
            expected_behavior=data["expected_behavior"],
            assertions=assertions,
            tags=data.get("tags", []),
            goal_relevance=goal_relevance,
            created_by=data.get("created_by", "auto"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now()
        )

    def _test_run_to_dict(self, test_run: TestRun) -> Dict[str, Any]:
        """Convert test run to dictionary."""
        results = {}
        for model, model_results in test_run.results.items():
            results[model] = [
                {
                    "test_case_id": r.test_case_id.value,
                    "model": r.model,
                    "passed": r.passed,
                    "score": r.score,
                    "actual_output": r.actual_output,
                    "assertion_results": [
                        {
                            "assertion": {
                                "assertion_type": ar.assertion.assertion_type.value,
                                "value": ar.assertion.value,
                                "threshold": ar.assertion.threshold
                            },
                            "passed": ar.passed,
                            "actual_value": ar.actual_value,
                            "details": ar.details
                        }
                        for ar in r.assertion_results
                    ],
                    "latency_ms": r.latency_ms,
                    "executed_at": r.executed_at.isoformat()
                }
                for r in model_results
            ]

        return {
            "id": test_run.id.value,
            "prompt_id": test_run.prompt_id.value,
            "prompt_version": test_run.prompt_version,
            "models": test_run.models,
            "status": test_run.status.value,
            "results": results,
            "started_at": test_run.started_at.isoformat(),
            "completed_at": test_run.completed_at.isoformat() if test_run.completed_at else None,
            "error_message": test_run.error_message
        }

    def _dict_to_test_run(self, data: Dict[str, Any]) -> TestRun:
        """Convert dictionary to test run."""
        results = {}
        for model, model_results in data.get("results", {}).items():
            results[model] = [
                TestCaseResult(
                    test_case_id=TestCaseId(r["test_case_id"]),
                    model=r["model"],
                    passed=r["passed"],
                    score=r["score"],
                    actual_output=r["actual_output"],
                    assertion_results=[
                        AssertionResult(
                            assertion=TestAssertion(
                                assertion_type=AssertionType(ar["assertion"]["assertion_type"]),
                                value=ar["assertion"]["value"],
                                threshold=ar["assertion"].get("threshold", 0.8)
                            ),
                            passed=ar["passed"],
                            actual_value=ar.get("actual_value"),
                            details=ar.get("details", "")
                        )
                        for ar in r.get("assertion_results", [])
                    ],
                    latency_ms=r["latency_ms"],
                    executed_at=datetime.fromisoformat(r["executed_at"]) if r.get("executed_at") else datetime.now()
                )
                for r in model_results
            ]

        return TestRun(
            id=TestRunId(data["id"]),
            prompt_id=PromptId(data["prompt_id"]),
            prompt_version=data["prompt_version"],
            models=data.get("models", []),
            status=TestStatus(data.get("status", "pending")),
            results=results,
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else datetime.now(),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            error_message=data.get("error_message")
        )