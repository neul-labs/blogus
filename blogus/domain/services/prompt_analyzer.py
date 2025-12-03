"""
Domain service for prompt analysis.
"""

from typing import Optional, List
from ..models.prompt import (
    Prompt, PromptId, ModelId, AnalysisResult, LLMProvider, Goal,
    Score, Fragment, PromptTestCase, AnalysisStatus
)


class PromptAnalyzer:
    """Domain service for analyzing prompts."""

    def __init__(self, llm_provider: LLMProvider):
        self._llm_provider = llm_provider

    async def analyze_prompt(self, prompt: Prompt, judge_model_id: str,
                           goal: Optional[str] = None) -> AnalysisResult:
        """
        Analyze a prompt for effectiveness and goal alignment.

        Args:
            prompt: The prompt to analyze
            judge_model_id: Model to use for analysis
            goal: Optional goal string, will be inferred if not provided

        Returns:
            AnalysisResult: Analysis results
        """
        model = ModelId(judge_model_id)

        # Validate model availability
        if not self._llm_provider.is_model_available(model):
            raise ValueError(f"Model {judge_model_id} is not available")

        # Use provided goal or infer from prompt
        analysis_goal = goal or prompt.goal
        inferred_goal = None
        if not analysis_goal:
            inferred = await self._llm_provider.infer_goal(model, prompt.content)
            analysis_goal = inferred.description
            inferred_goal = inferred

        # Create initial analysis result
        analysis = AnalysisResult(
            prompt_id=prompt.id,
            goal_alignment=Score(1),
            effectiveness=Score(1),
            suggestions=[],
            inferred_goal=inferred_goal,
            status=AnalysisStatus.IN_PROGRESS
        )

        try:
            # Perform comprehensive analysis using LLM
            analysis_result = await self._llm_provider.analyze_prompt(
                model, prompt.content, analysis_goal, prompt.id
            )

            # Update analysis with results
            analysis.goal_alignment = analysis_result.goal_alignment
            analysis.effectiveness = analysis_result.effectiveness
            analysis.suggestions = analysis_result.suggestions
            analysis.fragments = analysis_result.fragments
            analysis.mark_completed()

            return analysis

        except Exception as e:
            analysis.mark_failed(str(e))
            raise

    async def infer_goal(self, prompt: Prompt, judge_model_id: str) -> Goal:
        """
        Infer the goal from a prompt using LLM analysis.

        Args:
            prompt: The prompt to analyze
            judge_model_id: Model to use for inference

        Returns:
            Goal: Inferred goal
        """
        model = ModelId(judge_model_id)

        if not self._llm_provider.is_model_available(model):
            raise ValueError(f"Model {judge_model_id} is not available")

        return await self._llm_provider.infer_goal(model, prompt.content)

    async def analyze_fragments(self, prompt: Prompt, judge_model_id: str,
                              goal: Optional[str] = None) -> List[Fragment]:
        """
        Analyze prompt fragments for goal alignment.

        Args:
            prompt: The prompt to analyze
            judge_model_id: Model to use for analysis
            goal: Goal string for analysis (will be inferred if not provided)

        Returns:
            List[Fragment]: List of analyzed fragments
        """
        model = ModelId(judge_model_id)

        if not self._llm_provider.is_model_available(model):
            raise ValueError(f"Model {judge_model_id} is not available")

        # Get or infer goal
        analysis_goal = goal or prompt.goal
        if not analysis_goal:
            inferred = await self._llm_provider.infer_goal(model, prompt.content)
            analysis_goal = inferred.description

        return await self._llm_provider.analyze_fragments(model, prompt.content, analysis_goal)

    async def generate_test_case(self, prompt: Prompt, judge_model_id: str,
                               goal: Optional[str] = None) -> PromptTestCase:
        """
        Generate a single test case for the prompt.

        Args:
            prompt: The prompt to generate test for
            judge_model_id: Model to use for generation
            goal: Goal for test relevance (will be inferred if not provided)

        Returns:
            PromptTestCase: Generated test case
        """
        test_cases = await self.generate_test_cases(prompt, judge_model_id, goal, num_cases=1)
        return test_cases[0]

    async def generate_test_cases(self, prompt: Prompt, judge_model_id: str,
                                 goal: Optional[str] = None,
                                 num_cases: int = 3) -> List[PromptTestCase]:
        """
        Generate multiple test cases for the prompt.

        Args:
            prompt: The prompt to generate tests for
            judge_model_id: Model to use for generation
            goal: Goal string for test relevance (will be inferred if not provided)
            num_cases: Number of test cases to generate

        Returns:
            List[PromptTestCase]: Generated test cases
        """
        model = ModelId(judge_model_id)

        if not self._llm_provider.is_model_available(model):
            raise ValueError(f"Model {judge_model_id} is not available")

        # Get or infer goal
        analysis_goal = goal or prompt.goal
        if not analysis_goal:
            inferred = await self._llm_provider.infer_goal(model, prompt.content)
            analysis_goal = inferred.description

        return await self._llm_provider.generate_test_cases(
            model, prompt.content, analysis_goal, num_cases
        )

    async def quick_score(self, prompt: Prompt, judge_model_id: str,
                         goal: Optional[str] = None) -> tuple[int, int]:
        """
        Get quick effectiveness and goal alignment scores without full analysis.

        Args:
            prompt: The prompt to score
            judge_model_id: Model to use
            goal: Goal for alignment scoring

        Returns:
            tuple[int, int]: (goal_alignment_score, effectiveness_score)
        """
        result = await self.analyze_prompt(prompt, judge_model_id, goal)
        return (result.goal_alignment.value, result.effectiveness.value)
