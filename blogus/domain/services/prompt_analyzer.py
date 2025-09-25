"""
Domain service for prompt analysis.
"""

from typing import Optional, List
from datetime import datetime
from ..models.prompt import (
    Prompt, PromptId, ModelId, AnalysisResult, LLMProvider, Goal,
    Score, Fragment, TestCase, AnalysisStatus
)


class PromptAnalyzer:
    """Domain service for analyzing prompts."""

    def __init__(self, llm_provider: LLMProvider):
        self._llm_provider = llm_provider

    async def analyze_prompt(self, prompt: Prompt, judge_model_id: str,
                           goal: Optional[Goal] = None) -> AnalysisResult:
        """
        Analyze a prompt for effectiveness and goal alignment.

        Args:
            prompt: The prompt to analyze
            judge_model_id: Model to use for analysis
            goal: Optional goal, will be inferred if not provided

        Returns:
            AnalysisResult: Analysis results
        """
        from ..models.prompt import ModelId

        model = ModelId(judge_model_id)

        # Validate model availability
        if not self._llm_provider.is_model_available(model):
            raise ValueError(f"Model {judge_model_id} is not available")

        # Use provided goal or infer from prompt
        analysis_goal = goal or await self._infer_goal(prompt, model)

        # Create analysis result
        analysis = AnalysisResult(
            prompt_id=prompt.id,
            goal_alignment=Score(1),  # Placeholder
            effectiveness=Score(1),   # Placeholder
            suggestions=[],
            inferred_goal=analysis_goal if goal is None else None,
            status=AnalysisStatus.IN_PROGRESS
        )

        try:
            # Perform actual analysis using LLM
            analysis_result = await self._llm_provider.analyze_prompt(
                model, prompt.text, analysis_goal
            )

            # Update analysis with results
            analysis.goal_alignment = analysis_result.goal_alignment
            analysis.effectiveness = analysis_result.effectiveness
            analysis.suggestions = analysis_result.suggestions
            analysis.fragments = analysis_result.fragments
            analysis.test_cases = analysis_result.test_cases
            analysis.mark_completed()

            return analysis

        except Exception as e:
            analysis.mark_failed(str(e))
            raise

    async def _infer_goal(self, prompt: Prompt, model: ModelId) -> Goal:
        """Infer goal from prompt content."""
        # This would use the LLM to infer the goal
        # For now, return a placeholder
        return Goal("Inferred goal from prompt analysis")

    async def analyze_fragments(self, prompt: Prompt, judge_model_id: str,
                              goal: Optional[Goal] = None) -> List[Fragment]:
        """
        Analyze prompt fragments for goal alignment.

        Args:
            prompt: The prompt to analyze
            judge_model_id: Model to use for analysis
            goal: Goal for analysis

        Returns:
            List[Fragment]: List of analyzed fragments
        """
        from ..models.prompt import ModelId

        model = ModelId(judge_model_id)

        if not self._llm_provider.is_model_available(model):
            raise ValueError(f"Model {judge_model_id} is not available")

        analysis_goal = goal or await self._infer_goal(prompt, model)

        # This would implement fragment analysis logic
        # For now, return a placeholder
        return [
            Fragment(
                text=prompt.text.content[:100],
                fragment_type="instruction",
                goal_alignment=Score(7),
                improvement_suggestion="Consider adding more specific guidance"
            )
        ]

    async def generate_test_case(self, prompt: Prompt, judge_model_id: str,
                               goal: Optional[Goal] = None) -> TestCase:
        """
        Generate a test case for the prompt.

        Args:
            prompt: The prompt to generate test for
            judge_model_id: Model to use for generation
            goal: Goal for test relevance

        Returns:
            TestCase: Generated test case
        """
        from ..models.prompt import ModelId

        model = ModelId(judge_model_id)

        if not self._llm_provider.is_model_available(model):
            raise ValueError(f"Model {judge_model_id} is not available")

        analysis_goal = goal or await self._infer_goal(prompt, model)

        # This would implement test case generation logic
        # For now, return a placeholder
        return TestCase(
            input_variables={"input": "sample input"},
            expected_output="Expected response for the given input",
            goal_relevance=Score(8)
        )