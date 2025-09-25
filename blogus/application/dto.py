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