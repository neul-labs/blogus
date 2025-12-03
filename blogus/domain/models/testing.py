"""
Domain models for test suites and regression testing.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum
from abc import ABC, abstractmethod
import uuid

from .prompt import PromptId, Score


class AssertionType(Enum):
    """Types of assertions for test cases."""
    CONTAINS = "contains"           # Output contains string
    NOT_CONTAINS = "not_contains"   # Output doesn't contain string
    REGEX = "regex"                 # Output matches regex
    SEMANTIC_SIMILAR = "semantic"   # Semantically similar to expected
    LLM_JUDGE = "llm_judge"         # LLM evaluates correctness


class TestStatus(Enum):
    """Status of a test run."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"


@dataclass(frozen=True)
class TestCaseId:
    """Value object for test case identification."""
    value: str

    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("TestCaseId value must be a non-empty string")

    @classmethod
    def generate(cls) -> 'TestCaseId':
        return cls(str(uuid.uuid4()))


@dataclass(frozen=True)
class TestRunId:
    """Value object for test run identification."""
    value: str

    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("TestRunId value must be a non-empty string")

    @classmethod
    def generate(cls) -> 'TestRunId':
        return cls(str(uuid.uuid4()))


@dataclass
class TestAssertion:
    """
    An assertion to validate test case output.
    """
    assertion_type: AssertionType
    value: str                    # Expected value or pattern
    threshold: float = 0.8        # For semantic/llm_judge (0-1)

    def describe(self) -> str:
        """Human-readable description of the assertion."""
        if self.assertion_type == AssertionType.CONTAINS:
            return f"Output contains '{self.value}'"
        elif self.assertion_type == AssertionType.NOT_CONTAINS:
            return f"Output does not contain '{self.value}'"
        elif self.assertion_type == AssertionType.REGEX:
            return f"Output matches pattern '{self.value}'"
        elif self.assertion_type == AssertionType.SEMANTIC_SIMILAR:
            return f"Output is semantically similar to expected (threshold: {self.threshold})"
        elif self.assertion_type == AssertionType.LLM_JUDGE:
            return f"LLM judges output as correct (threshold: {self.threshold})"
        return f"Unknown assertion: {self.assertion_type}"


@dataclass
class TestCase:
    """
    A test case for validating prompt behavior.

    Can be auto-generated or manually created.
    Supports template variables for prompts with {{variables}}.
    """
    id: TestCaseId
    prompt_id: PromptId
    name: str
    description: str

    # Input
    input_variables: Dict[str, str]  # Variables to substitute

    # Expected behavior
    expected_behavior: str            # Description of expected output
    assertions: List[TestAssertion]   # Programmatic checks

    # Metadata
    tags: List[str] = field(default_factory=list)  # edge_case, typical, regression
    goal_relevance: Optional[Score] = None
    created_by: str = "auto"          # "auto" or author name
    created_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def create(
        cls,
        prompt_id: PromptId,
        name: str,
        input_variables: Dict[str, str],
        expected_behavior: str,
        assertions: Optional[List[TestAssertion]] = None,
        description: str = "",
        tags: Optional[List[str]] = None,
        goal_relevance: Optional[Score] = None,
        created_by: str = "auto"
    ) -> 'TestCase':
        """Factory method to create a TestCase."""
        return cls(
            id=TestCaseId.generate(),
            prompt_id=prompt_id,
            name=name,
            description=description or f"Test case: {name}",
            input_variables=input_variables,
            expected_behavior=expected_behavior,
            assertions=assertions or [],
            tags=tags or [],
            goal_relevance=goal_relevance,
            created_by=created_by
        )


@dataclass
class AssertionResult:
    """Result of evaluating a single assertion."""
    assertion: TestAssertion
    passed: bool
    actual_value: Optional[str] = None  # What was actually matched
    details: str = ""                   # Explanation


@dataclass
class TestCaseResult:
    """
    Result of running a single test case on a model.
    """
    test_case_id: TestCaseId
    model: str
    passed: bool
    score: float                        # 0-1 overall score
    actual_output: str
    assertion_results: List[AssertionResult]
    latency_ms: float
    executed_at: datetime = field(default_factory=datetime.now)

    @property
    def failed_assertions(self) -> List[AssertionResult]:
        """Get assertions that failed."""
        return [r for r in self.assertion_results if not r.passed]


@dataclass
class TestRun:
    """
    A complete test run executing all test cases against models.
    """
    id: TestRunId
    prompt_id: PromptId
    prompt_version: int
    models: List[str]                  # Models tested
    status: TestStatus
    results: Dict[str, List[TestCaseResult]]  # model -> results
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    @property
    def total_tests(self) -> int:
        """Total number of test case executions."""
        return sum(len(r) for r in self.results.values())

    @property
    def passed_tests(self) -> int:
        """Number of passed tests."""
        return sum(
            1 for results in self.results.values()
            for r in results if r.passed
        )

    @property
    def failed_tests(self) -> int:
        """Number of failed tests."""
        return self.total_tests - self.passed_tests

    @property
    def pass_rate(self) -> float:
        """Overall pass rate (0-1)."""
        if self.total_tests == 0:
            return 0.0
        return self.passed_tests / self.total_tests

    def get_model_pass_rate(self, model: str) -> float:
        """Get pass rate for a specific model."""
        if model not in self.results or not self.results[model]:
            return 0.0
        passed = sum(1 for r in self.results[model] if r.passed)
        return passed / len(self.results[model])

    def mark_completed(self) -> None:
        """Mark test run as completed."""
        self.status = TestStatus.PASSED if self.failed_tests == 0 else TestStatus.FAILED
        self.completed_at = datetime.now()

    def mark_error(self, error: str) -> None:
        """Mark test run as errored."""
        self.status = TestStatus.ERROR
        self.error_message = error
        self.completed_at = datetime.now()

    @classmethod
    def create(
        cls,
        prompt_id: PromptId,
        prompt_version: int,
        models: List[str]
    ) -> 'TestRun':
        """Factory method to create a TestRun."""
        return cls(
            id=TestRunId.generate(),
            prompt_id=prompt_id,
            prompt_version=prompt_version,
            models=models,
            status=TestStatus.PENDING,
            results={}
        )


# =============================================================================
# Repository Interface
# =============================================================================

class TestRepository(ABC):
    """Abstract repository for test case and test run persistence."""

    # Test Cases
    @abstractmethod
    async def save_test_case(self, test_case: TestCase) -> None:
        """Save a test case."""
        pass

    @abstractmethod
    async def find_test_case_by_id(self, test_case_id: TestCaseId) -> Optional[TestCase]:
        """Find test case by ID."""
        pass

    @abstractmethod
    async def find_test_cases_by_prompt(self, prompt_id: PromptId) -> List[TestCase]:
        """Find all test cases for a prompt."""
        pass

    @abstractmethod
    async def delete_test_case(self, test_case_id: TestCaseId) -> bool:
        """Delete a test case."""
        pass

    # Test Runs
    @abstractmethod
    async def save_test_run(self, test_run: TestRun) -> None:
        """Save a test run."""
        pass

    @abstractmethod
    async def find_test_run_by_id(self, test_run_id: TestRunId) -> Optional[TestRun]:
        """Find test run by ID."""
        pass

    @abstractmethod
    async def find_test_runs_by_prompt(
        self,
        prompt_id: PromptId,
        limit: int = 10
    ) -> List[TestRun]:
        """Find test runs for a prompt, newest first."""
        pass

    @abstractmethod
    async def find_latest_test_run(self, prompt_id: PromptId) -> Optional[TestRun]:
        """Find the most recent test run for a prompt."""
        pass
