"""
Data Transfer Objects for application layer.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from datetime import datetime


@dataclass
class PromptDto:
    """DTO for prompt data."""
    id: str
    text: str
    goal: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class AnalysisDto:
    """DTO for analysis results."""
    prompt_id: str
    goal_alignment: int
    effectiveness: int
    suggestions: List[str]
    status: str
    inferred_goal: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class FragmentDto:
    """DTO for prompt fragments."""
    text: str
    fragment_type: str
    goal_alignment: int
    improvement_suggestion: str


@dataclass
class TestCaseDto:
    """DTO for test cases."""
    input_variables: Dict[str, str]
    expected_output: str
    goal_relevance: int


@dataclass
class TemplateDto:
    """DTO for templates."""
    id: str
    name: str
    description: str
    content: str
    category: str
    tags: List[str]
    author: str
    version: str
    variables: List[str]
    usage_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class BatchTaskDto:
    """DTO for batch tasks."""
    task_id: str
    prompt: str
    operation: str
    parameters: Dict[str, Any]
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None
    duration: float = 0.0


@dataclass
class BatchResultDto:
    """DTO for batch results."""
    batch_id: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    success_rate: float
    total_duration: float
    tasks: List[BatchTaskDto]
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# Request/Response DTOs
@dataclass
class AnalyzePromptRequest:
    """Request to analyze a prompt."""
    prompt_text: str
    judge_model: str
    goal: Optional[str] = None


@dataclass
class AnalyzePromptResponse:
    """Response from prompt analysis."""
    analysis: AnalysisDto
    fragments: List[FragmentDto]


@dataclass
class GenerateTestRequest:
    """Request to generate test case."""
    prompt_text: str
    judge_model: str
    goal: Optional[str] = None


@dataclass
class GenerateTestResponse:
    """Response from test generation."""
    test_case: TestCaseDto


@dataclass
class ExecutePromptRequest:
    """Request to execute a prompt."""
    prompt_text: str
    target_model: str


@dataclass
class ExecutePromptResponse:
    """Response from prompt execution."""
    result: str
    model_used: str
    duration: float


@dataclass
class CreateTemplateRequest:
    """Request to create a template."""
    template_id: str
    name: str
    description: str
    content: str
    category: str = "general"
    tags: List[str] = None
    author: str = "unknown"


@dataclass
class CreateTemplateResponse:
    """Response from template creation."""
    template: TemplateDto


@dataclass
class RenderTemplateRequest:
    """Request to render a template."""
    template_id: str
    variables: Dict[str, str]


@dataclass
class RenderTemplateResponse:
    """Response from template rendering."""
    rendered_content: str


@dataclass
class BatchProcessRequest:
    """Request for batch processing."""
    prompts: List[str]
    operation: str
    parameters: Dict[str, Any]
    batch_id: Optional[str] = None


@dataclass
class BatchProcessResponse:
    """Response from batch processing."""
    batch_result: BatchResultDto


# Registry DTOs
@dataclass
class ModelParametersDto:
    """DTO for model parameters."""
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: List[str] = None


@dataclass
class ModelConfigDto:
    """DTO for model configuration."""
    model_id: str
    parameters: ModelParametersDto = None
    fallback_models: List[str] = None


@dataclass
class VersionRecordDto:
    """DTO for version records."""
    version: int
    content_hash: str
    content: str
    model_config: ModelConfigDto
    created_at: datetime
    created_by: str
    change_summary: Optional[str] = None


@dataclass
class TrafficRouteDto:
    """DTO for traffic routes."""
    version: int
    weight: int
    model_override: Optional[str] = None


@dataclass
class TrafficConfigDto:
    """DTO for traffic configuration."""
    routes: List[TrafficRouteDto]
    shadow_version: Optional[int] = None


@dataclass
class DeploymentDto:
    """DTO for prompt deployments."""
    id: str
    name: str
    description: str
    content: str
    goal: Optional[str]
    model_config: ModelConfigDto
    tags: List[str]
    category: str
    author: str
    version: int
    version_history: List[VersionRecordDto]
    traffic_config: Optional[TrafficConfigDto]
    status: str
    is_template: bool
    template_variables: List[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class DeploymentSummaryDto:
    """DTO for deployment list/summary view."""
    id: str
    name: str
    description: str
    model_id: str
    version: int
    status: str
    category: str
    author: str
    tags: List[str]
    is_template: bool
    updated_at: datetime


@dataclass
class ExecutionResultDto:
    """DTO for execution results."""
    prompt_name: str
    version: int
    model_used: str
    response: str
    latency_ms: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    shadow_response: Optional[str] = None


@dataclass
class MetricsSummaryDto:
    """DTO for metrics summary."""
    prompt_name: str
    version: Optional[int]
    total_executions: int
    success_rate: float
    avg_latency_ms: float
    p95_latency_ms: float
    total_tokens: int
    total_cost_usd: float
    period_hours: int


# Registry Request/Response DTOs
@dataclass
class RegisterDeploymentRequest:
    """Request to register a new prompt deployment."""
    name: str
    description: str
    content: str
    model_id: str
    goal: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 1.0
    fallback_models: List[str] = None
    category: str = "general"
    tags: List[str] = None
    author: str = "anonymous"


@dataclass
class RegisterDeploymentResponse:
    """Response from registering a deployment."""
    deployment: DeploymentDto


@dataclass
class UpdateDeploymentContentRequest:
    """Request to update deployment content."""
    name: str
    new_content: str
    author: str
    change_summary: Optional[str] = None


@dataclass
class UpdateDeploymentModelRequest:
    """Request to update deployment model config."""
    name: str
    model_id: str
    author: str
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    fallback_models: Optional[List[str]] = None
    change_summary: Optional[str] = None


@dataclass
class SetTrafficConfigRequest:
    """Request to set traffic configuration."""
    name: str
    routes: List[TrafficRouteDto]
    shadow_version: Optional[int] = None


@dataclass
class ExecuteDeploymentRequest:
    """Request to execute a prompt deployment."""
    name: str
    variables: Dict[str, str] = None


@dataclass
class ExecuteDeploymentResponse:
    """Response from executing a deployment."""
    result: ExecutionResultDto


@dataclass
class RollbackDeploymentRequest:
    """Request to rollback a deployment."""
    name: str
    target_version: int
    author: str


@dataclass
class GetMetricsRequest:
    """Request to get metrics."""
    name: str
    version: Optional[int] = None
    period_hours: int = 24


@dataclass
class GetMetricsResponse:
    """Response with metrics."""
    metrics: MetricsSummaryDto


@dataclass
class CompareVersionsRequest:
    """Request to compare version metrics."""
    name: str
    versions: List[int]
    period_hours: int = 24


@dataclass
class CompareVersionsResponse:
    """Response with version comparison."""
    comparisons: Dict[int, MetricsSummaryDto]