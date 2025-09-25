"""
Core domain models for prompts and analysis.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
from abc import ABC, abstractmethod


class AnalysisStatus(Enum):
    """Status of an analysis operation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class PromptId:
    """Value object for prompt identification."""
    value: str

    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("PromptId value must be a non-empty string")


@dataclass(frozen=True)
class ModelId:
    """Value object for model identification."""
    value: str

    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("ModelId value must be a non-empty string")


@dataclass(frozen=True)
class PromptText:
    """Value object for prompt content with validation."""
    content: str

    def __post_init__(self):
        if not isinstance(self.content, str):
            raise ValueError("Prompt content must be a string")
        if len(self.content.strip()) == 0:
            raise ValueError("Prompt content cannot be empty")
        if len(self.content) > 100000:  # Reasonable limit
            raise ValueError("Prompt content is too long")


@dataclass(frozen=True)
class Goal:
    """Value object for prompt goals."""
    description: str

    def __post_init__(self):
        if not isinstance(self.description, str):
            raise ValueError("Goal description must be a string")
        if len(self.description.strip()) == 0:
            raise ValueError("Goal description cannot be empty")


@dataclass(frozen=True)
class Score:
    """Value object for analysis scores."""
    value: int
    max_value: int = 10

    def __post_init__(self):
        if not isinstance(self.value, int):
            raise ValueError("Score value must be an integer")
        if not isinstance(self.max_value, int):
            raise ValueError("Max score value must be an integer")
        if self.value < 0 or self.value > self.max_value:
            raise ValueError(f"Score must be between 0 and {self.max_value}")

    @property
    def percentage(self) -> float:
        """Get score as percentage."""
        return (self.value / self.max_value) * 100


@dataclass
class Fragment:
    """Domain entity for prompt fragments."""
    text: str
    fragment_type: str
    goal_alignment: Score
    improvement_suggestion: str

    def __post_init__(self):
        if not self.text.strip():
            raise ValueError("Fragment text cannot be empty")
        if not self.fragment_type.strip():
            raise ValueError("Fragment type cannot be empty")


@dataclass
class TestCase:
    """Domain entity for test cases."""
    input_variables: Dict[str, str]
    expected_output: str
    goal_relevance: Score

    def __post_init__(self):
        if not isinstance(self.input_variables, dict):
            raise ValueError("Input variables must be a dictionary")
        if not self.expected_output.strip():
            raise ValueError("Expected output cannot be empty")


@dataclass
class AnalysisResult:
    """Domain entity for prompt analysis results."""
    prompt_id: PromptId
    goal_alignment: Score
    effectiveness: Score
    suggestions: List[str]
    fragments: List[Fragment] = field(default_factory=list)
    test_cases: List[TestCase] = field(default_factory=list)
    inferred_goal: Optional[Goal] = None
    status: AnalysisStatus = AnalysisStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def mark_completed(self):
        """Mark analysis as completed."""
        self.status = AnalysisStatus.COMPLETED
        self.updated_at = datetime.now()

    def mark_failed(self, error: str):
        """Mark analysis as failed."""
        self.status = AnalysisStatus.FAILED
        self.updated_at = datetime.now()
        # Could add error field if needed


@dataclass
class Prompt:
    """Core domain entity for prompts."""
    id: PromptId
    text: PromptText
    goal: Optional[Goal] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Analysis results
    _analysis: Optional[AnalysisResult] = field(default=None, init=False)

    def update_text(self, new_text: PromptText):
        """Update prompt text."""
        self.text = new_text
        self.updated_at = datetime.now()
        # Invalidate existing analysis
        self._analysis = None

    def set_goal(self, goal: Goal):
        """Set or update the goal."""
        self.goal = goal
        self.updated_at = datetime.now()

    def set_analysis(self, analysis: AnalysisResult):
        """Set analysis results."""
        if analysis.prompt_id != self.id:
            raise ValueError("Analysis prompt ID must match prompt ID")
        self._analysis = analysis

    @property
    def analysis(self) -> Optional[AnalysisResult]:
        """Get analysis results."""
        return self._analysis

    @property
    def has_analysis(self) -> bool:
        """Check if prompt has completed analysis."""
        return self._analysis is not None and self._analysis.status == AnalysisStatus.COMPLETED


# Domain interfaces (ports)
class PromptRepository(ABC):
    """Abstract repository for prompt persistence."""

    @abstractmethod
    def save(self, prompt: Prompt) -> None:
        """Save a prompt."""
        pass

    @abstractmethod
    def find_by_id(self, prompt_id: PromptId) -> Optional[Prompt]:
        """Find prompt by ID."""
        pass

    @abstractmethod
    def find_all(self) -> List[Prompt]:
        """Find all prompts."""
        pass

    @abstractmethod
    def delete(self, prompt_id: PromptId) -> bool:
        """Delete a prompt."""
        pass


class LLMProvider(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    async def generate_response(self, model: ModelId, prompt: PromptText) -> str:
        """Generate response from LLM."""
        pass

    @abstractmethod
    async def analyze_prompt(self, model: ModelId, prompt: PromptText, goal: Optional[Goal]) -> AnalysisResult:
        """Analyze prompt using LLM."""
        pass

    @abstractmethod
    def is_model_available(self, model: ModelId) -> bool:
        """Check if model is available."""
        pass


class TemplateRepository(ABC):
    """Abstract repository for prompt templates."""

    @abstractmethod
    def save_template(self, template: 'PromptTemplate') -> None:
        """Save a template."""
        pass

    @abstractmethod
    def find_template(self, name: str) -> Optional['PromptTemplate']:
        """Find template by name."""
        pass

    @abstractmethod
    def find_all_templates(self) -> List['PromptTemplate']:
        """Find all templates."""
        pass