"""
Tests for application layer.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from blogus.application.services.prompt_service import PromptService
from blogus.application.dto import (
    AnalyzePromptRequest,
    ExecutePromptRequest,
    GenerateTestRequest,
)
from blogus.domain.models.prompt import PromptId, Score, AnalysisResult, AnalysisStatus, Goal, Fragment, PromptTestCase


class TestPromptService:
    """Test PromptService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_repository = MagicMock()
        self.mock_llm_provider = MagicMock()

        # Make async methods return coroutines
        self.mock_llm_provider.generate_response = AsyncMock(return_value="Test response")
        self.mock_llm_provider.is_model_available = MagicMock(return_value=True)

        # Mock the new LLM provider methods
        self.mock_llm_provider.infer_goal = AsyncMock(return_value=Goal("Inferred test goal"))
        self.mock_llm_provider.analyze_fragments = AsyncMock(return_value=[
            Fragment(
                text="Test fragment",
                fragment_type="instruction",
                goal_alignment=Score(8, 10),
                improvement_suggestion="None needed"
            )
        ])
        self.mock_llm_provider.generate_test_cases = AsyncMock(return_value=[
            PromptTestCase(
                input_variables={"input": "test value"},
                expected_output="Expected test output",
                goal_relevance=Score(8, 10)
            )
        ])

        # Mock analyze_prompt to return a complete result
        self.mock_llm_provider.analyze_prompt = AsyncMock(return_value=AnalysisResult(
            prompt_id=PromptId("test-id"),
            goal_alignment=Score(8, 10),
            effectiveness=Score(7, 10),
            suggestions=["Improve clarity"],
            fragments=[Fragment(
                text="Test fragment",
                fragment_type="instruction",
                goal_alignment=Score(8, 10),
                improvement_suggestion="None needed"
            )],
            inferred_goal=None,
            status=AnalysisStatus.COMPLETED
        ))

        self.service = PromptService(self.mock_repository, self.mock_llm_provider)

    @pytest.mark.asyncio
    async def test_execute_prompt(self):
        """Test prompt execution."""
        request = ExecutePromptRequest(
            prompt_text="Test prompt",
            target_model="gpt-4o"
        )

        self.mock_llm_provider.generate_response.return_value = "Test response"

        response = await self.service.execute_prompt(request)

        assert response.result == "Test response"
        assert response.model_used == "gpt-4o"
        assert response.duration >= 0
