"""
Domain models for multi-model output comparison.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
import uuid


@dataclass(frozen=True)
class ComparisonId:
    """Value object for comparison identification."""
    value: str

    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("ComparisonId value must be a non-empty string")

    @classmethod
    def generate(cls) -> 'ComparisonId':
        """Generate a new unique ComparisonId."""
        return cls(str(uuid.uuid4()))


@dataclass
class SemanticSimilarity:
    """
    Semantic similarity between two model outputs.

    Uses embedding-based cosine similarity (0-1 scale).
    """
    model_a: str
    model_b: str
    score: float  # 0.0 to 1.0

    def __post_init__(self):
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("Similarity score must be between 0.0 and 1.0")


@dataclass
class ModelEvaluation:
    """
    LLM judge evaluation of a single model's output.
    """
    model: str
    score: int          # 0-100
    rank: int           # 1 = best
    strengths: List[str]
    weaknesses: List[str]


@dataclass
class LLMAssessment:
    """
    LLM-as-judge assessment comparing multiple model outputs.

    A judge model evaluates all outputs against criteria like:
    - Accuracy/correctness
    - Helpfulness
    - Clarity
    - Completeness
    """
    judge_model: str
    summary: str                      # Overall comparison narrative
    evaluations: List[ModelEvaluation]
    criteria_used: List[str]          # What criteria were evaluated
    assessed_at: datetime = field(default_factory=datetime.now)

    @property
    def winner(self) -> Optional[str]:
        """Get the model with rank 1 (best)."""
        for e in self.evaluations:
            if e.rank == 1:
                return e.model
        return None

    @property
    def rankings(self) -> List[str]:
        """Get models in order of rank."""
        return [e.model for e in sorted(self.evaluations, key=lambda x: x.rank)]


@dataclass
class ComparisonResult:
    """
    Complete comparison result for multi-model execution.

    Combines semantic similarity analysis with LLM judge assessment.
    """
    id: ComparisonId
    execution_id: str                 # Link to MultiModelResult
    prompt_text: str                  # The prompt that was compared

    # Pairwise semantic similarities
    similarities: List[SemanticSimilarity]

    # LLM judge assessment (optional - requires extra API call)
    llm_assessment: Optional[LLMAssessment] = None

    # Metadata
    compared_at: datetime = field(default_factory=datetime.now)

    def get_similarity(self, model_a: str, model_b: str) -> Optional[float]:
        """Get similarity score between two models."""
        for sim in self.similarities:
            if (sim.model_a == model_a and sim.model_b == model_b) or \
               (sim.model_a == model_b and sim.model_b == model_a):
                return sim.score
        return None

    @property
    def average_similarity(self) -> float:
        """Get average similarity across all pairs."""
        if not self.similarities:
            return 0.0
        return sum(s.score for s in self.similarities) / len(self.similarities)

    @property
    def most_similar_pair(self) -> Optional[tuple]:
        """Get the two most similar models."""
        if not self.similarities:
            return None
        best = max(self.similarities, key=lambda s: s.score)
        return (best.model_a, best.model_b, best.score)

    @property
    def least_similar_pair(self) -> Optional[tuple]:
        """Get the two least similar models."""
        if not self.similarities:
            return None
        worst = min(self.similarities, key=lambda s: s.score)
        return (worst.model_a, worst.model_b, worst.score)

    @classmethod
    def create(
        cls,
        execution_id: str,
        prompt_text: str,
        similarities: List[SemanticSimilarity],
        llm_assessment: Optional[LLMAssessment] = None
    ) -> 'ComparisonResult':
        """Factory method to create ComparisonResult."""
        return cls(
            id=ComparisonId.generate(),
            execution_id=execution_id,
            prompt_text=prompt_text,
            similarities=similarities,
            llm_assessment=llm_assessment
        )


# =============================================================================
# Comparison Metrics Aggregation
# =============================================================================

@dataclass
class ModelMetrics:
    """
    Aggregated metrics for a single model across comparisons.
    """
    model: str
    total_executions: int
    avg_latency_ms: float
    avg_cost_usd: float
    avg_score: float           # From LLM assessments
    win_count: int             # Times ranked #1
    similarity_to_consensus: float  # Avg similarity to other models


@dataclass
class ComparisonSummary:
    """
    Summary of multiple comparisons for analytics.
    """
    total_comparisons: int
    models_compared: List[str]
    model_metrics: List[ModelMetrics]
    overall_consensus: float   # How similar are models on average
    recommended_model: Optional[str]  # Best balance of quality/cost/speed
