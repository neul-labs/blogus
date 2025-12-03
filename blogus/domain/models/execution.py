"""
Domain models for prompt execution and multi-model results.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
import uuid


@dataclass(frozen=True)
class ExecutionId:
    """Value object for execution identification."""
    value: str

    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("ExecutionId value must be a non-empty string")

    @classmethod
    def generate(cls) -> 'ExecutionId':
        """Generate a new unique ExecutionId."""
        return cls(str(uuid.uuid4()))


@dataclass
class TokenUsage:
    """Token usage metrics for an execution."""
    input_tokens: int
    output_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class ModelExecution:
    """
    Result of executing a prompt on a single model.

    Contains the response, performance metrics, and cost information.
    """
    id: ExecutionId
    model: str
    response: str
    latency_ms: float
    tokens: TokenUsage
    cost_usd: float
    success: bool
    error: Optional[str] = None
    executed_at: datetime = field(default_factory=datetime.now)

    # Optional trace context for observability
    trace_id: Optional[str] = None
    span_id: Optional[str] = None

    @classmethod
    def create_success(
        cls,
        model: str,
        response: str,
        latency_ms: float,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float
    ) -> 'ModelExecution':
        """Factory for successful execution."""
        return cls(
            id=ExecutionId.generate(),
            model=model,
            response=response,
            latency_ms=latency_ms,
            tokens=TokenUsage(input_tokens, output_tokens),
            cost_usd=cost_usd,
            success=True
        )

    @classmethod
    def create_failure(
        cls,
        model: str,
        error: str,
        latency_ms: float = 0
    ) -> 'ModelExecution':
        """Factory for failed execution."""
        return cls(
            id=ExecutionId.generate(),
            model=model,
            response="",
            latency_ms=latency_ms,
            tokens=TokenUsage(0, 0),
            cost_usd=0,
            success=False,
            error=error
        )


@dataclass
class MultiModelResult:
    """
    Result of executing a prompt on multiple models.

    Aggregates individual model executions and optionally includes
    comparison results.
    """
    id: ExecutionId
    prompt_id: Optional[str]  # If from a saved prompt
    prompt_text: str          # The actual prompt text executed
    variables_used: Dict[str, str]  # If template was rendered
    executions: List[ModelExecution]
    executed_at: datetime = field(default_factory=datetime.now)

    # Comparison is added separately after execution
    comparison_id: Optional[str] = None

    @property
    def successful_executions(self) -> List[ModelExecution]:
        """Get only successful executions."""
        return [e for e in self.executions if e.success]

    @property
    def failed_executions(self) -> List[ModelExecution]:
        """Get only failed executions."""
        return [e for e in self.executions if not e.success]

    @property
    def total_cost(self) -> float:
        """Get total cost across all executions."""
        return sum(e.cost_usd for e in self.executions)

    @property
    def total_tokens(self) -> int:
        """Get total tokens used across all executions."""
        return sum(e.tokens.total_tokens for e in self.executions)

    @property
    def fastest_model(self) -> Optional[str]:
        """Get the model with lowest latency (successful only)."""
        successful = self.successful_executions
        if not successful:
            return None
        return min(successful, key=lambda e: e.latency_ms).model

    @property
    def cheapest_model(self) -> Optional[str]:
        """Get the model with lowest cost (successful only)."""
        successful = self.successful_executions
        if not successful:
            return None
        return min(successful, key=lambda e: e.cost_usd).model

    def get_execution_by_model(self, model: str) -> Optional[ModelExecution]:
        """Get execution result for a specific model."""
        for e in self.executions:
            if e.model == model:
                return e
        return None

    @classmethod
    def create(
        cls,
        prompt_text: str,
        executions: List[ModelExecution],
        prompt_id: Optional[str] = None,
        variables_used: Optional[Dict[str, str]] = None
    ) -> 'MultiModelResult':
        """Factory method to create MultiModelResult."""
        return cls(
            id=ExecutionId.generate(),
            prompt_id=prompt_id,
            prompt_text=prompt_text,
            variables_used=variables_used or {},
            executions=executions
        )
