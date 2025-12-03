"""
Domain models for the Prompt Registry.

The registry allows prompts to be named, versioned, and deployed with
locked-in model configurations for production use.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from enum import Enum
from abc import ABC, abstractmethod
import uuid
import hashlib
import re


class DeploymentStatus(Enum):
    """Status of a prompt deployment."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class DeploymentId:
    """Value object for deployment identification."""
    value: str

    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("DeploymentId value must be a non-empty string")

    @staticmethod
    def generate() -> 'DeploymentId':
        """Generate a new unique deployment ID."""
        return DeploymentId(str(uuid.uuid4()))


@dataclass(frozen=True)
class PromptName:
    """Value object for prompt names (slugs)."""
    value: str

    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("PromptName must be a non-empty string")
        # Validate slug format: lowercase, alphanumeric, hyphens only
        if not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$', self.value):
            raise ValueError(
                "PromptName must be lowercase alphanumeric with hyphens, "
                "cannot start/end with hyphen. Example: 'customer-support-v2'"
            )
        if len(self.value) > 64:
            raise ValueError("PromptName cannot exceed 64 characters")


@dataclass
class ModelParameters:
    """Configuration parameters for LLM execution."""
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        if self.max_tokens < 1:
            raise ValueError("max_tokens must be at least 1")
        if not 0.0 <= self.top_p <= 1.0:
            raise ValueError("top_p must be between 0.0 and 1.0")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for LLM API calls."""
        params = {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
        }
        if self.frequency_penalty != 0.0:
            params["frequency_penalty"] = self.frequency_penalty
        if self.presence_penalty != 0.0:
            params["presence_penalty"] = self.presence_penalty
        if self.stop_sequences:
            params["stop"] = self.stop_sequences
        return params


@dataclass
class ModelConfig:
    """Model configuration for a prompt deployment."""
    model_id: str  # e.g., "gpt-4o", "claude-3-sonnet-20240229"
    parameters: ModelParameters = field(default_factory=ModelParameters)
    fallback_models: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.model_id or not isinstance(self.model_id, str):
            raise ValueError("model_id must be a non-empty string")


@dataclass
class VersionRecord:
    """Record of a prompt version."""
    version: int
    content_hash: str
    content: str
    model_config: ModelConfig
    created_at: datetime
    created_by: str
    change_summary: Optional[str] = None

    @staticmethod
    def compute_hash(content: str) -> str:
        """Compute a hash of the content for change detection."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:12]


@dataclass
class TrafficRoute:
    """A single route in traffic configuration."""
    version: int
    weight: int  # 0-100 percentage
    model_override: Optional[str] = None  # Override model for this route

    def __post_init__(self):
        if not 0 <= self.weight <= 100:
            raise ValueError("Weight must be between 0 and 100")
        if self.version < 1:
            raise ValueError("Version must be at least 1")


@dataclass
class TrafficConfig:
    """Traffic routing configuration for A/B testing and canary deployments."""
    routes: List[TrafficRoute] = field(default_factory=list)
    shadow_version: Optional[int] = None  # Version to shadow test

    def __post_init__(self):
        if self.routes:
            total_weight = sum(r.weight for r in self.routes)
            if total_weight != 100:
                raise ValueError(f"Traffic weights must sum to 100, got {total_weight}")

    def select_route(self, random_value: float) -> TrafficRoute:
        """
        Select a route based on a random value [0, 1).

        Args:
            random_value: A random float between 0 and 1

        Returns:
            The selected TrafficRoute
        """
        if not self.routes:
            raise ValueError("No routes configured")

        cumulative = 0
        for route in self.routes:
            cumulative += route.weight / 100.0
            if random_value < cumulative:
                return route

        # Fallback to last route (shouldn't happen with valid weights)
        return self.routes[-1]


@dataclass
class ExecutionMetrics:
    """Metrics from a single prompt execution."""
    prompt_name: str
    version: int
    model_used: str
    latency_ms: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    success: bool
    error_message: Optional[str] = None
    executed_at: datetime = field(default_factory=datetime.now)
    shadow_execution: bool = False
    # OpenTelemetry trace context
    trace_id: Optional[str] = None
    span_id: Optional[str] = None


@dataclass
class AggregatedMetrics:
    """Aggregated metrics for a prompt or version."""
    prompt_name: str
    version: Optional[int]  # None for overall metrics
    total_executions: int
    successful_executions: int
    failed_executions: int
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    total_tokens: int
    total_cost_usd: float
    period_start: datetime
    period_end: datetime


@dataclass
class PromptDeployment:
    """
    A deployed prompt with model configuration.

    This is the core entity of the registry - a named, versioned prompt
    that can be executed via the API.
    """
    id: DeploymentId
    name: PromptName
    description: str

    # Content
    content: str  # The prompt text (may contain {{variables}})
    goal: Optional[str] = None

    # Model Configuration (locked-in)
    model_config: ModelConfig = field(default_factory=lambda: ModelConfig(model_id="gpt-4o"))

    # Organization
    tags: Set[str] = field(default_factory=set)
    category: str = "general"
    author: str = "anonymous"

    # Versioning
    version: int = 1
    version_history: List[VersionRecord] = field(default_factory=list)

    # Traffic Routing
    traffic_config: Optional[TrafficConfig] = None

    # Status
    status: DeploymentStatus = DeploymentStatus.ACTIVE

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.content or not self.content.strip():
            raise ValueError("Prompt content cannot be empty")
        if len(self.description) > 500:
            raise ValueError("Description cannot exceed 500 characters")

    @property
    def is_template(self) -> bool:
        """Check if this prompt contains template variables."""
        return bool(re.search(r'\{\{\s*\w+\s*\}\}', self.content))

    @property
    def template_variables(self) -> List[str]:
        """Extract template variable names from the content."""
        return re.findall(r'\{\{\s*(\w+)\s*\}\}', self.content)

    @property
    def content_hash(self) -> str:
        """Get hash of current content."""
        return VersionRecord.compute_hash(self.content)

    def render(self, variables: Dict[str, str]) -> str:
        """
        Render the prompt template with provided variables.

        Args:
            variables: Dictionary of variable names to values

        Returns:
            Rendered prompt string
        """
        result = self.content
        for var_name, value in variables.items():
            pattern = r'\{\{\s*' + re.escape(var_name) + r'\s*\}\}'
            result = re.sub(pattern, value, result)

        # Check for unresolved variables
        remaining = re.findall(r'\{\{\s*(\w+)\s*\}\}', result)
        if remaining:
            raise ValueError(f"Unresolved template variables: {remaining}")

        return result

    def create_version_record(self, change_summary: Optional[str] = None) -> VersionRecord:
        """Create a version record for the current state."""
        return VersionRecord(
            version=self.version,
            content_hash=self.content_hash,
            content=self.content,
            model_config=self.model_config,
            created_at=datetime.now(),
            created_by=self.author,
            change_summary=change_summary
        )

    def update_content(self, new_content: str, author: str,
                      change_summary: Optional[str] = None) -> None:
        """
        Update the prompt content, creating a new version.

        Args:
            new_content: The new prompt content
            author: Who made the change
            change_summary: Optional summary of what changed
        """
        if new_content == self.content:
            return  # No change

        # Save current version to history
        self.version_history.append(self.create_version_record(change_summary))

        # Update to new version
        self.content = new_content
        self.version += 1
        self.author = author
        self.updated_at = datetime.now()

    def update_model_config(self, new_config: ModelConfig, author: str,
                           change_summary: Optional[str] = None) -> None:
        """
        Update the model configuration, creating a new version.
        """
        # Save current version to history
        self.version_history.append(self.create_version_record(
            change_summary or f"Model changed to {new_config.model_id}"
        ))

        # Update
        self.model_config = new_config
        self.version += 1
        self.author = author
        self.updated_at = datetime.now()

    def get_version(self, version_num: int) -> Optional[VersionRecord]:
        """Get a specific version from history."""
        if version_num == self.version:
            return self.create_version_record()

        for record in self.version_history:
            if record.version == version_num:
                return record
        return None

    def rollback_to_version(self, version_num: int, author: str) -> None:
        """
        Rollback to a previous version.

        This creates a new version with the content from the specified version.
        """
        target = self.get_version(version_num)
        if not target:
            raise ValueError(f"Version {version_num} not found")

        self.update_content(
            target.content,
            author,
            f"Rollback to version {version_num}"
        )
        self.model_config = target.model_config

    def set_traffic_config(self, config: TrafficConfig) -> None:
        """Set traffic routing configuration."""
        # Validate that all referenced versions exist
        max_version = self.version
        for route in config.routes:
            if route.version > max_version:
                raise ValueError(f"Route references non-existent version {route.version}")
        if config.shadow_version and config.shadow_version > max_version:
            raise ValueError(f"Shadow version {config.shadow_version} does not exist")

        self.traffic_config = config
        self.updated_at = datetime.now()

    def clear_traffic_config(self) -> None:
        """Clear traffic config, routing 100% to latest version."""
        self.traffic_config = None
        self.updated_at = datetime.now()


# Repository Interface
class PromptRegistry(ABC):
    """Abstract repository for prompt deployments."""

    @abstractmethod
    def register(self, deployment: PromptDeployment) -> PromptDeployment:
        """Register a new prompt deployment."""
        pass

    @abstractmethod
    def get_by_id(self, deployment_id: DeploymentId) -> Optional[PromptDeployment]:
        """Get deployment by ID."""
        pass

    @abstractmethod
    def get_by_name(self, name: PromptName) -> Optional[PromptDeployment]:
        """Get deployment by name."""
        pass

    @abstractmethod
    def list_all(self,
                 limit: int = 100,
                 offset: int = 0,
                 status: Optional[DeploymentStatus] = None) -> List[PromptDeployment]:
        """List all deployments with pagination."""
        pass

    @abstractmethod
    def search(self,
               query: Optional[str] = None,
               tags: Optional[Set[str]] = None,
               category: Optional[str] = None,
               author: Optional[str] = None) -> List[PromptDeployment]:
        """Search deployments by various criteria."""
        pass

    @abstractmethod
    def update(self, deployment: PromptDeployment) -> PromptDeployment:
        """Update an existing deployment."""
        pass

    @abstractmethod
    def delete(self, name: PromptName) -> bool:
        """Delete a deployment by name."""
        pass

    @abstractmethod
    def exists(self, name: PromptName) -> bool:
        """Check if a deployment with the given name exists."""
        pass


class MetricsStore(ABC):
    """Abstract store for execution metrics."""

    @abstractmethod
    def record(self, metrics: ExecutionMetrics) -> None:
        """Record execution metrics."""
        pass

    @abstractmethod
    def get_aggregated(self,
                       prompt_name: str,
                       version: Optional[int] = None,
                       period_hours: int = 24) -> AggregatedMetrics:
        """Get aggregated metrics for a prompt/version."""
        pass

    @abstractmethod
    def get_recent(self,
                   prompt_name: str,
                   limit: int = 100) -> List[ExecutionMetrics]:
        """Get recent execution metrics."""
        pass

    @abstractmethod
    def compare_versions(self,
                        prompt_name: str,
                        versions: List[int],
                        period_hours: int = 24) -> Dict[int, AggregatedMetrics]:
        """Compare metrics across versions."""
        pass
