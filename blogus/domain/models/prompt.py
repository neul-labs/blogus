"""
Unified domain models for prompts.

A Prompt is the core entity - it can be plain text or contain {{variables}}.
Templates are simply prompts with variables.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from enum import Enum
from abc import ABC, abstractmethod
import re
import uuid


class AnalysisStatus(Enum):
    """Status of an analysis operation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# =============================================================================
# Value Objects
# =============================================================================

@dataclass(frozen=True)
class PromptId:
    """Value object for prompt identification."""
    value: str

    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("PromptId value must be a non-empty string")

    @classmethod
    def generate(cls) -> 'PromptId':
        """Generate a new unique PromptId."""
        return cls(str(uuid.uuid4()))


@dataclass(frozen=True)
class ModelId:
    """Value object for model identification."""
    value: str

    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("ModelId value must be a non-empty string")


@dataclass(frozen=True)
class Score:
    """Value object for analysis scores (0-10 scale)."""
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
        """Get score as percentage (0-100)."""
        return (self.value / self.max_value) * 100

    @property
    def normalized(self) -> float:
        """Get score as 0-1 float."""
        return self.value / self.max_value


@dataclass(frozen=True)
class Goal:
    """Value object for prompt goals."""
    description: str

    def __post_init__(self):
        if not isinstance(self.description, str):
            raise ValueError("Goal description must be a string")
        if len(self.description.strip()) == 0:
            raise ValueError("Goal description cannot be empty")


# =============================================================================
# Unified Prompt Entity
# =============================================================================

@dataclass
class Prompt:
    """
    Unified prompt entity - templates are prompts with variables.

    A prompt can be:
    - Plain text: No {{variables}}, used as-is
    - Template: Contains {{variables}} that must be substituted before use

    This entity replaces both the old Prompt and PromptTemplate.
    """
    id: PromptId
    name: str
    description: str
    content: str                          # May contain {{variable}} placeholders
    goal: Optional[str] = None
    category: str = "general"
    tags: Set[str] = field(default_factory=set)
    author: str = "unknown"
    version: int = 1
    usage_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Variable pattern: {{variable_name}} with optional whitespace
    _VARIABLE_PATTERN = re.compile(r'\{\{\s*(\w+)\s*\}\}')

    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise ValueError("Prompt name cannot be empty")
        if not self.content or not self.content.strip():
            raise ValueError("Prompt content cannot be empty")
        if len(self.content) > 100000:
            raise ValueError("Prompt content is too long (max 100,000 characters)")

    @property
    def variables(self) -> List[str]:
        """Extract unique variable names from content."""
        matches = self._VARIABLE_PATTERN.findall(self.content)
        # Preserve order but remove duplicates
        seen = set()
        result = []
        for var in matches:
            if var not in seen:
                seen.add(var)
                result.append(var)
        return result

    @property
    def is_template(self) -> bool:
        """Check if this prompt contains template variables."""
        return len(self.variables) > 0

    def render(self, values: Dict[str, str]) -> str:
        """
        Render prompt with variable substitutions.

        Args:
            values: Dictionary mapping variable names to values

        Returns:
            Rendered prompt text with variables replaced

        Raises:
            ValueError: If required variables are missing
        """
        if not self.is_template:
            return self.content

        # Check for missing variables
        required = set(self.variables)
        provided = set(values.keys())
        missing = required - provided
        if missing:
            raise ValueError(f"Missing required variables: {missing}")

        # Substitute variables
        result = self.content
        for var_name, var_value in values.items():
            pattern = rf'\{{\{{\s*{re.escape(var_name)}\s*\}}\}}'
            result = re.sub(pattern, str(var_value), result)

        return result

    def update_content(self, new_content: str) -> None:
        """Update prompt content and increment version."""
        if not new_content or not new_content.strip():
            raise ValueError("Prompt content cannot be empty")
        self.content = new_content
        self.version += 1
        self.updated_at = datetime.now()

    def update_metadata(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        goal: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[Set[str]] = None,
        author: Optional[str] = None
    ) -> None:
        """Update prompt metadata."""
        if name is not None:
            if not name.strip():
                raise ValueError("Prompt name cannot be empty")
            self.name = name
        if description is not None:
            self.description = description
        if goal is not None:
            self.goal = goal
        if category is not None:
            self.category = category
        if tags is not None:
            self.tags = tags
        if author is not None:
            self.author = author
        self.updated_at = datetime.now()

    def increment_usage(self) -> None:
        """Increment usage counter."""
        self.usage_count += 1

    def validate(self) -> List[str]:
        """Validate prompt content and return list of issues."""
        issues = []

        # Check for basic issues
        if len(self.name) > 100:
            issues.append("Prompt name is too long (max 100 characters)")
        if len(self.description) > 500:
            issues.append("Description is too long (max 500 characters)")

        # Check for unclosed variable braces
        open_count = self.content.count('{{')
        close_count = self.content.count('}}')
        if open_count != close_count:
            issues.append("Mismatched variable braces {{ }}")

        # Check for suspicious patterns
        if '<script' in self.content.lower():
            issues.append("Content contains potentially unsafe script tags")

        return issues

    @classmethod
    def create(
        cls,
        name: str,
        content: str,
        description: str = "",
        goal: Optional[str] = None,
        category: str = "general",
        tags: Optional[Set[str]] = None,
        author: str = "unknown"
    ) -> 'Prompt':
        """Factory method to create a new Prompt."""
        return cls(
            id=PromptId.generate(),
            name=name,
            description=description or f"Prompt: {name}",
            content=content,
            goal=goal,
            category=category,
            tags=tags or set(),
            author=author
        )


# =============================================================================
# Analysis-Related Entities
# =============================================================================

@dataclass
class Fragment:
    """A fragment/segment of a prompt with analysis."""
    text: str
    fragment_type: str  # instruction, context, example, constraint, output_format, other
    goal_alignment: Score
    improvement_suggestion: str

    def __post_init__(self):
        if not self.text.strip():
            raise ValueError("Fragment text cannot be empty")
        if not self.fragment_type.strip():
            raise ValueError("Fragment type cannot be empty")


@dataclass
class AnalysisResult:
    """
    Transient analysis result (for backward compatibility).
    For persisted analysis, use AnalysisRecord in analysis.py.
    """
    prompt_id: PromptId
    goal_alignment: Score
    effectiveness: Score
    suggestions: List[str]
    fragments: List[Fragment] = field(default_factory=list)
    inferred_goal: Optional[Goal] = None
    status: AnalysisStatus = AnalysisStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def mark_completed(self) -> None:
        """Mark analysis as completed."""
        self.status = AnalysisStatus.COMPLETED
        self.updated_at = datetime.now()

    def mark_failed(self, error: str = "") -> None:
        """Mark analysis as failed."""
        self.status = AnalysisStatus.FAILED
        self.updated_at = datetime.now()


@dataclass
class PromptTestCase:
    """A test case for validating prompt behavior."""
    input_variables: Dict[str, str]
    expected_output: str
    goal_relevance: Score

    def __post_init__(self):
        if not isinstance(self.input_variables, dict):
            raise ValueError("Input variables must be a dictionary")
        if not self.expected_output.strip():
            raise ValueError("Expected output cannot be empty")


# =============================================================================
# Repository Interfaces (Ports)
# =============================================================================

class PromptRepository(ABC):
    """Abstract repository for prompt persistence."""

    @abstractmethod
    async def save(self, prompt: Prompt) -> None:
        """Save a prompt."""
        pass

    @abstractmethod
    async def find_by_id(self, prompt_id: PromptId) -> Optional[Prompt]:
        """Find prompt by ID."""
        pass

    @abstractmethod
    async def find_all(
        self,
        category: Optional[str] = None,
        has_variables: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Prompt]:
        """Find all prompts with optional filtering."""
        pass

    @abstractmethod
    async def search(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        author: Optional[str] = None
    ) -> List[Prompt]:
        """Search prompts."""
        pass

    @abstractmethod
    async def delete(self, prompt_id: PromptId) -> bool:
        """Delete a prompt."""
        pass


class LLMProvider(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    async def generate_response(self, model: ModelId, prompt: str) -> str:
        """Generate response from LLM."""
        pass

    @abstractmethod
    async def generate_responses(
        self,
        models: List[ModelId],
        prompt: str
    ) -> Dict[str, str]:
        """Generate responses from multiple models in parallel."""
        pass

    @abstractmethod
    async def analyze_prompt(
        self,
        model: ModelId,
        prompt: str,
        goal: Optional[str],
        prompt_id: PromptId
    ) -> AnalysisResult:
        """Analyze prompt using LLM."""
        pass

    @abstractmethod
    async def infer_goal(self, model: ModelId, prompt: str) -> Goal:
        """Infer the goal/purpose of a prompt."""
        pass

    @abstractmethod
    async def analyze_fragments(
        self,
        model: ModelId,
        prompt: str,
        goal: str
    ) -> List[Fragment]:
        """Analyze prompt fragments for goal alignment."""
        pass

    @abstractmethod
    async def generate_test_cases(
        self,
        model: ModelId,
        prompt: str,
        goal: str,
        num_cases: int = 3
    ) -> List[PromptTestCase]:
        """Generate test cases for the prompt."""
        pass

    @abstractmethod
    def is_model_available(self, model: ModelId) -> bool:
        """Check if model is available."""
        pass

    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available model IDs."""
        pass
