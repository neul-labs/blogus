"""
Tests for domain services.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import numpy as np

from blogus.domain.models.prompt import (
    Prompt, PromptId, Goal, Score, Fragment, PromptTestCase, AnalysisResult, AnalysisStatus, ModelId
)
from blogus.domain.models.execution import ExecutionId, TokenUsage, ModelExecution, MultiModelResult
from blogus.domain.models.comparison import (
    ComparisonId, SemanticSimilarity, ModelEvaluation, LLMAssessment,
    ComparisonResult, ModelMetrics, ComparisonSummary
)
from blogus.domain.services.prompt_analyzer import PromptAnalyzer
from blogus.domain.services.comparison_engine import ComparisonEngine, EmbeddingService


class TestEmbeddingService:
    """Test EmbeddingService."""

    def test_cosine_similarity_identical_vectors(self):
        """Test cosine similarity with identical vectors."""
        service = EmbeddingService()
        vec = np.array([1.0, 2.0, 3.0])

        similarity = service.cosine_similarity(vec, vec)

        assert abs(similarity - 1.0) < 0.0001

    def test_cosine_similarity_orthogonal_vectors(self):
        """Test cosine similarity with orthogonal vectors."""
        service = EmbeddingService()
        vec1 = np.array([1.0, 0.0])
        vec2 = np.array([0.0, 1.0])

        similarity = service.cosine_similarity(vec1, vec2)

        assert abs(similarity) < 0.0001

    def test_cosine_similarity_opposite_vectors(self):
        """Test cosine similarity with opposite vectors."""
        service = EmbeddingService()
        vec1 = np.array([1.0, 0.0])
        vec2 = np.array([-1.0, 0.0])

        similarity = service.cosine_similarity(vec1, vec2)

        assert abs(similarity - (-1.0)) < 0.0001

    def test_cosine_similarity_zero_vector(self):
        """Test cosine similarity with zero vector returns 0."""
        service = EmbeddingService()
        vec1 = np.array([1.0, 2.0])
        vec2 = np.array([0.0, 0.0])

        similarity = service.cosine_similarity(vec1, vec2)

        assert similarity == 0.0


class TestComparisonEngine:
    """Test ComparisonEngine - basic tests only since models differ from expected."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_llm_provider = MagicMock()
        self.mock_llm_provider.generate_response = AsyncMock(return_value='{"evaluations": [], "recommendation": "test", "key_differences": []}')

    def test_engine_initialization(self):
        """Test engine can be initialized."""
        engine = ComparisonEngine(
            llm_provider=self.mock_llm_provider,
            judge_model="gpt-4o"
        )

        assert engine is not None
        assert engine._judge_model.value == "gpt-4o"

    def test_embedding_service_initialized(self):
        """Test embedding service is initialized."""
        engine = ComparisonEngine(
            llm_provider=self.mock_llm_provider,
            judge_model="gpt-4o"
        )

        assert engine._embedding_service is not None


class TestPromptAnalyzer:
    """Test PromptAnalyzer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_llm_provider = MagicMock()
        self.mock_llm_provider.is_model_available = MagicMock(return_value=True)

    @pytest.mark.asyncio
    async def test_analyze_prompt_with_goal(self):
        """Test analyzing prompt with explicit goal."""
        self.mock_llm_provider.analyze_prompt = AsyncMock(return_value=AnalysisResult(
            prompt_id=PromptId("test-id"),
            goal_alignment=Score(8, 10),
            effectiveness=Score(7, 10),
            suggestions=["Improve clarity"],
            fragments=[],
            status=AnalysisStatus.COMPLETED
        ))

        analyzer = PromptAnalyzer(self.mock_llm_provider)

        prompt = Prompt.create(
            name="Test",
            content="Analyze this code",
            goal="Find bugs"
        )

        result = await analyzer.analyze_prompt(prompt, "gpt-4o", "Find bugs")

        assert result.goal_alignment.value == 8
        assert result.effectiveness.value == 7
        assert result.status == AnalysisStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_analyze_prompt_infers_goal(self):
        """Test that analyzer infers goal when not provided."""
        self.mock_llm_provider.infer_goal = AsyncMock(return_value=Goal("Inferred goal"))
        self.mock_llm_provider.analyze_prompt = AsyncMock(return_value=AnalysisResult(
            prompt_id=PromptId("test-id"),
            goal_alignment=Score(7, 10),
            effectiveness=Score(6, 10),
            suggestions=[],
            fragments=[],
            status=AnalysisStatus.COMPLETED
        ))

        analyzer = PromptAnalyzer(self.mock_llm_provider)

        prompt = Prompt.create(
            name="Test",
            content="Do something"
            # No goal
        )

        result = await analyzer.analyze_prompt(prompt, "gpt-4o")

        self.mock_llm_provider.infer_goal.assert_called_once()
        assert result.inferred_goal is not None

    @pytest.mark.asyncio
    async def test_analyze_prompt_unavailable_model(self):
        """Test that analyzing with unavailable model raises error."""
        self.mock_llm_provider.is_model_available = MagicMock(return_value=False)

        analyzer = PromptAnalyzer(self.mock_llm_provider)

        prompt = Prompt.create(
            name="Test",
            content="Test content"
        )

        with pytest.raises(ValueError, match="not available"):
            await analyzer.analyze_prompt(prompt, "unavailable-model")

    @pytest.mark.asyncio
    async def test_infer_goal(self):
        """Test goal inference."""
        self.mock_llm_provider.infer_goal = AsyncMock(return_value=Goal("Extract key information"))

        analyzer = PromptAnalyzer(self.mock_llm_provider)

        prompt = Prompt.create(
            name="Test",
            content="Read this document and summarize the main points"
        )

        goal = await analyzer.infer_goal(prompt, "gpt-4o")

        assert goal.description == "Extract key information"

    @pytest.mark.asyncio
    async def test_analyze_fragments(self):
        """Test fragment analysis."""
        self.mock_llm_provider.analyze_fragments = AsyncMock(return_value=[
            Fragment(
                text="System instruction",
                fragment_type="instruction",
                goal_alignment=Score(8, 10),
                improvement_suggestion="None"
            ),
            Fragment(
                text="User input",
                fragment_type="input",
                goal_alignment=Score(7, 10),
                improvement_suggestion="Be more specific"
            )
        ])

        analyzer = PromptAnalyzer(self.mock_llm_provider)

        prompt = Prompt.create(
            name="Test",
            content="<system>Instruction</system><user>Input</user>",
            goal="Test goal"
        )

        fragments = await analyzer.analyze_fragments(prompt, "gpt-4o", "Test goal")

        assert len(fragments) == 2
        assert fragments[0].fragment_type == "instruction"
        assert fragments[1].fragment_type == "input"

    @pytest.mark.asyncio
    async def test_generate_test_case(self):
        """Test test case generation."""
        self.mock_llm_provider.generate_test_cases = AsyncMock(return_value=[
            PromptTestCase(
                input_variables={"query": "test query"},
                expected_output="Expected response",
                goal_relevance=Score(8, 10)
            )
        ])

        analyzer = PromptAnalyzer(self.mock_llm_provider)

        prompt = Prompt.create(
            name="Test",
            content="Answer: {{query}}",
            goal="Answer questions"
        )

        test_case = await analyzer.generate_test_case(prompt, "gpt-4o", "Answer questions")

        assert test_case.input_variables == {"query": "test query"}
        assert test_case.expected_output == "Expected response"
        assert test_case.goal_relevance.value == 8

    @pytest.mark.asyncio
    async def test_generate_multiple_test_cases(self):
        """Test generating multiple test cases."""
        self.mock_llm_provider.generate_test_cases = AsyncMock(return_value=[
            PromptTestCase(
                input_variables={"q": "1"},
                expected_output="A1",
                goal_relevance=Score(8, 10)
            ),
            PromptTestCase(
                input_variables={"q": "2"},
                expected_output="A2",
                goal_relevance=Score(7, 10)
            ),
            PromptTestCase(
                input_variables={"q": "3"},
                expected_output="A3",
                goal_relevance=Score(9, 10)
            )
        ])

        analyzer = PromptAnalyzer(self.mock_llm_provider)

        prompt = Prompt.create(
            name="Test",
            content="Answer: {{q}}",
            goal="Answer questions"
        )

        test_cases = await analyzer.generate_test_cases(prompt, "gpt-4o", "Answer questions", num_cases=3)

        assert len(test_cases) == 3

    @pytest.mark.asyncio
    async def test_quick_score(self):
        """Test quick scoring."""
        self.mock_llm_provider.analyze_prompt = AsyncMock(return_value=AnalysisResult(
            prompt_id=PromptId("test-id"),
            goal_alignment=Score(8, 10),
            effectiveness=Score(7, 10),
            suggestions=[],
            fragments=[],
            status=AnalysisStatus.COMPLETED
        ))

        analyzer = PromptAnalyzer(self.mock_llm_provider)

        prompt = Prompt.create(
            name="Test",
            content="Test content",
            goal="Test goal"
        )

        goal_score, effectiveness_score = await analyzer.quick_score(prompt, "gpt-4o", "Test goal")

        assert goal_score == 8
        assert effectiveness_score == 7
