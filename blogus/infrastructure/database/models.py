"""
TortoiseORM database models for the Prompt Registry.
"""

from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator
from enum import Enum


class DeploymentStatusEnum(str, Enum):
    """Deployment status enum for database."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class DeploymentModel(models.Model):
    """Database model for prompt deployments."""

    id = fields.UUIDField(pk=True)
    name = fields.CharField(max_length=64, unique=True, index=True)
    description = fields.TextField()
    content = fields.TextField()
    goal = fields.TextField(null=True)

    # Model configuration (stored as JSON)
    model_id = fields.CharField(max_length=100)
    temperature = fields.FloatField(default=0.7)
    max_tokens = fields.IntField(default=1000)
    top_p = fields.FloatField(default=1.0)
    frequency_penalty = fields.FloatField(default=0.0)
    presence_penalty = fields.FloatField(default=0.0)
    stop_sequences = fields.JSONField(default=[])
    fallback_models = fields.JSONField(default=[])

    # Organization
    tags = fields.JSONField(default=[])
    category = fields.CharField(max_length=50, default="general", index=True)
    author = fields.CharField(max_length=100, default="anonymous", index=True)

    # Versioning
    version = fields.IntField(default=1)

    # Traffic configuration
    shadow_version = fields.IntField(null=True)

    # Status
    status = fields.CharEnumField(DeploymentStatusEnum, default=DeploymentStatusEnum.ACTIVE, index=True)

    # Timestamps
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    # Relations
    version_history: fields.ReverseRelation["VersionHistoryModel"]
    traffic_routes: fields.ReverseRelation["TrafficRouteModel"]

    class Meta:
        table = "deployments"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.name} v{self.version}"


class VersionHistoryModel(models.Model):
    """Database model for version history."""

    id = fields.UUIDField(pk=True)
    deployment = fields.ForeignKeyField(
        "models.DeploymentModel",
        related_name="version_history",
        on_delete=fields.CASCADE
    )

    version = fields.IntField()
    content_hash = fields.CharField(max_length=12)
    content = fields.TextField()

    # Model config at this version
    model_id = fields.CharField(max_length=100)
    temperature = fields.FloatField(default=0.7)
    max_tokens = fields.IntField(default=1000)
    top_p = fields.FloatField(default=1.0)
    frequency_penalty = fields.FloatField(default=0.0)
    presence_penalty = fields.FloatField(default=0.0)
    stop_sequences = fields.JSONField(default=[])
    fallback_models = fields.JSONField(default=[])

    created_at = fields.DatetimeField(auto_now_add=True)
    created_by = fields.CharField(max_length=100)
    change_summary = fields.TextField(null=True)

    class Meta:
        table = "version_history"
        ordering = ["-version"]
        unique_together = (("deployment", "version"),)

    def __str__(self):
        return f"{self.deployment.name} v{self.version}"


class TrafficRouteModel(models.Model):
    """Database model for traffic routes."""

    id = fields.UUIDField(pk=True)
    deployment = fields.ForeignKeyField(
        "models.DeploymentModel",
        related_name="traffic_routes",
        on_delete=fields.CASCADE
    )

    version = fields.IntField()
    weight = fields.IntField()  # 0-100
    model_override = fields.CharField(max_length=100, null=True)

    class Meta:
        table = "traffic_routes"

    def __str__(self):
        return f"v{self.version}: {self.weight}%"


class ExecutionMetricModel(models.Model):
    """Database model for execution metrics."""

    id = fields.UUIDField(pk=True)
    prompt_name = fields.CharField(max_length=64, index=True)
    version = fields.IntField(index=True)
    model_used = fields.CharField(max_length=100, index=True)

    # Performance
    latency_ms = fields.FloatField()
    input_tokens = fields.IntField()
    output_tokens = fields.IntField()
    total_tokens = fields.IntField()
    estimated_cost_usd = fields.FloatField()

    # Status
    success = fields.BooleanField(default=True, index=True)
    error_message = fields.TextField(null=True)
    shadow_execution = fields.BooleanField(default=False, index=True)

    # Tracing
    trace_id = fields.CharField(max_length=32, null=True, index=True)
    span_id = fields.CharField(max_length=16, null=True)

    # Timestamp
    executed_at = fields.DatetimeField(auto_now_add=True, index=True)

    class Meta:
        table = "execution_metrics"
        ordering = ["-executed_at"]
        indexes = [
            ("prompt_name", "executed_at"),
            ("prompt_name", "version", "executed_at"),
        ]

    def __str__(self):
        return f"{self.prompt_name} v{self.version} @ {self.executed_at}"


# Pydantic models for API serialization (auto-generated)
DeploymentPydantic = pydantic_model_creator(DeploymentModel, name="Deployment")
VersionHistoryPydantic = pydantic_model_creator(VersionHistoryModel, name="VersionHistory")
ExecutionMetricPydantic = pydantic_model_creator(ExecutionMetricModel, name="ExecutionMetric")
