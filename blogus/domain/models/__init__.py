"""
Domain models package.

This package contains all domain entities and value objects for the Blogus
prompt engineering toolkit.
"""

# Core prompt models
from .prompt import (
    # Value Objects
    PromptId,
    ModelId,
    Score,
    Goal,
    # Entities
    Prompt,
    Fragment,
    AnalysisResult,
    PromptTestCase,
    # Enums
    AnalysisStatus,
    # Repository Interfaces
    PromptRepository,
    LLMProvider,
)

# Analysis models (persisted)
from .analysis import (
    AnalysisId,
    AnalysisRecord,
    AnalysisRepository,
)

# Execution models
from .execution import (
    ExecutionId,
    TokenUsage,
    ModelExecution,
    MultiModelResult,
)

# Comparison models
from .comparison import (
    ComparisonId,
    SemanticSimilarity,
    ModelEvaluation,
    LLMAssessment,
    ComparisonResult,
    ModelMetrics,
    ComparisonSummary,
)

# Testing models
from .testing import (
    TestCaseId,
    TestRunId,
    AssertionType,
    TestStatus,
    TestAssertion,
    TestCase,
    AssertionResult,
    TestCaseResult,
    TestRun,
    TestRepository,
)

# Registry models (keep for deployment functionality)
from .registry import (
    DeploymentId,
    PromptName,
    ModelConfig,
    ModelParameters,
    VersionRecord,
    TrafficRoute,
    TrafficConfig,
    ExecutionMetrics,
    AggregatedMetrics,
    PromptDeployment,
    DeploymentStatus,
    PromptRegistry,
    MetricsStore,
)

__all__ = [
    # Prompt
    "PromptId",
    "ModelId",
    "Score",
    "Goal",
    "Prompt",
    "Fragment",
    "AnalysisResult",
    "PromptTestCase",
    "AnalysisStatus",
    "PromptRepository",
    "LLMProvider",
    # Analysis
    "AnalysisId",
    "AnalysisRecord",
    "AnalysisRepository",
    # Execution
    "ExecutionId",
    "TokenUsage",
    "ModelExecution",
    "MultiModelResult",
    # Comparison
    "ComparisonId",
    "SemanticSimilarity",
    "ModelEvaluation",
    "LLMAssessment",
    "ComparisonResult",
    "ModelMetrics",
    "ComparisonSummary",
    # Testing
    "TestCaseId",
    "TestRunId",
    "AssertionType",
    "TestStatus",
    "TestAssertion",
    "TestCase",
    "AssertionResult",
    "TestCaseResult",
    "TestRun",
    "TestRepository",
    # Registry
    "DeploymentId",
    "PromptName",
    "ModelConfig",
    "ModelParameters",
    "VersionRecord",
    "TrafficRoute",
    "TrafficConfig",
    "ExecutionMetrics",
    "AggregatedMetrics",
    "PromptDeployment",
    "DeploymentStatus",
    "PromptRegistry",
    "MetricsStore",
]
