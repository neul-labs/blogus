"""
Domain models for persisted analysis records.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from abc import ABC, abstractmethod
import uuid

from .prompt import PromptId, Score, Fragment, Goal, AnalysisStatus


@dataclass(frozen=True)
class AnalysisId:
    """Value object for analysis identification."""
    value: str

    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("AnalysisId value must be a non-empty string")

    @classmethod
    def generate(cls) -> 'AnalysisId':
        """Generate a new unique AnalysisId."""
        return cls(str(uuid.uuid4()))


@dataclass
class AnalysisRecord:
    """
    Persisted analysis record linked to a specific prompt version.

    Unlike AnalysisResult (transient), this is stored permanently
    and linked to the prompt_id and prompt_version.
    """
    id: AnalysisId
    prompt_id: PromptId
    prompt_version: int
    judge_model: str

    # Scores
    goal_alignment: Score
    effectiveness: Score

    # Analysis details
    suggestions: List[str]
    fragments: List[Fragment]
    inferred_goal: Optional[str] = None

    # Status and timestamps
    status: AnalysisStatus = AnalysisStatus.COMPLETED
    error_message: Optional[str] = None
    analyzed_at: datetime = field(default_factory=datetime.now)

    # Optional: mark as baseline for comparison
    is_baseline: bool = False

    def __post_init__(self):
        if not self.judge_model:
            raise ValueError("Judge model must be specified")

    @classmethod
    def create(
        cls,
        prompt_id: PromptId,
        prompt_version: int,
        judge_model: str,
        goal_alignment: Score,
        effectiveness: Score,
        suggestions: List[str],
        fragments: List[Fragment],
        inferred_goal: Optional[str] = None
    ) -> 'AnalysisRecord':
        """Factory method to create a new AnalysisRecord."""
        return cls(
            id=AnalysisId.generate(),
            prompt_id=prompt_id,
            prompt_version=prompt_version,
            judge_model=judge_model,
            goal_alignment=goal_alignment,
            effectiveness=effectiveness,
            suggestions=suggestions,
            fragments=fragments,
            inferred_goal=inferred_goal
        )

    @classmethod
    def create_failed(
        cls,
        prompt_id: PromptId,
        prompt_version: int,
        judge_model: str,
        error_message: str
    ) -> 'AnalysisRecord':
        """Factory method for failed analysis."""
        return cls(
            id=AnalysisId.generate(),
            prompt_id=prompt_id,
            prompt_version=prompt_version,
            judge_model=judge_model,
            goal_alignment=Score(0),
            effectiveness=Score(0),
            suggestions=[],
            fragments=[],
            status=AnalysisStatus.FAILED,
            error_message=error_message
        )

    def set_as_baseline(self) -> None:
        """Mark this analysis as the baseline for comparison."""
        self.is_baseline = True


# =============================================================================
# Repository Interface
# =============================================================================

class AnalysisRepository(ABC):
    """Abstract repository for analysis record persistence."""

    @abstractmethod
    async def save(self, analysis: AnalysisRecord) -> None:
        """Save an analysis record."""
        pass

    @abstractmethod
    async def find_by_id(self, analysis_id: AnalysisId) -> Optional[AnalysisRecord]:
        """Find analysis by ID."""
        pass

    @abstractmethod
    async def find_by_prompt(
        self,
        prompt_id: PromptId,
        limit: int = 10
    ) -> List[AnalysisRecord]:
        """Find all analyses for a prompt, newest first."""
        pass

    @abstractmethod
    async def find_latest(self, prompt_id: PromptId) -> Optional[AnalysisRecord]:
        """Find the most recent analysis for a prompt."""
        pass

    @abstractmethod
    async def find_baseline(self, prompt_id: PromptId) -> Optional[AnalysisRecord]:
        """Find the baseline analysis for a prompt."""
        pass

    @abstractmethod
    async def delete(self, analysis_id: AnalysisId) -> bool:
        """Delete an analysis record."""
        pass
