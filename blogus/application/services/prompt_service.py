"""
Application service for prompt operations.
"""

from typing import Optional, List
from datetime import datetime
import uuid

from ..dto import (
    PromptDto, AnalysisDto, FragmentDto, TestCaseDto,
    AnalyzePromptRequest, AnalyzePromptResponse,
    GenerateTestRequest, GenerateTestResponse,
    ExecutePromptRequest, ExecutePromptResponse
)
from ...domain.models.prompt import (
    Prompt, PromptId, PromptText, Goal, PromptRepository, LLMProvider
)
from ...domain.services.prompt_analyzer import PromptAnalyzer


class PromptService:
    """Application service for prompt operations."""

    def __init__(self, prompt_repository: PromptRepository,
                 llm_provider: LLMProvider):
        self._repository = prompt_repository
        self._analyzer = PromptAnalyzer(llm_provider)
        self._llm_provider = llm_provider

    async def create_prompt(self, text: str, goal: Optional[str] = None) -> PromptDto:
        """
        Create a new prompt.

        Args:
            text: Prompt text
            goal: Optional goal description

        Returns:
            PromptDto: Created prompt
        """
        # Create domain objects
        prompt_id = PromptId(str(uuid.uuid4()))
        prompt_text = PromptText(text)
        prompt_goal = Goal(goal) if goal else None

        prompt = Prompt(
            id=prompt_id,
            text=prompt_text,
            goal=prompt_goal
        )

        # Save prompt
        self._repository.save(prompt)

        return self._to_prompt_dto(prompt)

    async def get_prompt(self, prompt_id: str) -> Optional[PromptDto]:
        """
        Get a prompt by ID.

        Args:
            prompt_id: Prompt identifier

        Returns:
            Optional[PromptDto]: Prompt if found
        """
        prompt = self._repository.find_by_id(PromptId(prompt_id))
        return self._to_prompt_dto(prompt) if prompt else None

    async def list_prompts(self) -> List[PromptDto]:
        """
        List all prompts.

        Returns:
            List[PromptDto]: List of prompts
        """
        prompts = self._repository.find_all()
        return [self._to_prompt_dto(prompt) for prompt in prompts]

    async def analyze_prompt(self, request: AnalyzePromptRequest) -> AnalyzePromptResponse:
        """
        Analyze a prompt for effectiveness.

        Args:
            request: Analysis request

        Returns:
            AnalyzePromptResponse: Analysis results
        """
        # Create temporary prompt for analysis
        prompt_id = PromptId(str(uuid.uuid4()))
        prompt_text = PromptText(request.prompt_text)
        goal = Goal(request.goal) if request.goal else None

        prompt = Prompt(
            id=prompt_id,
            text=prompt_text,
            goal=goal
        )

        # Perform analysis
        analysis_result = await self._analyzer.analyze_prompt(
            prompt, request.judge_model, goal
        )

        # Generate fragments analysis
        fragments = await self._analyzer.analyze_fragments(
            prompt, request.judge_model, goal
        )

        # Convert to DTOs
        analysis_dto = self._to_analysis_dto(analysis_result)
        fragment_dtos = [self._to_fragment_dto(f) for f in fragments]

        return AnalyzePromptResponse(
            analysis=analysis_dto,
            fragments=fragment_dtos
        )

    async def generate_test_case(self, request: GenerateTestRequest) -> GenerateTestResponse:
        """
        Generate a test case for a prompt.

        Args:
            request: Test generation request

        Returns:
            GenerateTestResponse: Generated test case
        """
        # Create temporary prompt
        prompt_id = PromptId(str(uuid.uuid4()))
        prompt_text = PromptText(request.prompt_text)
        goal = Goal(request.goal) if request.goal else None

        prompt = Prompt(
            id=prompt_id,
            text=prompt_text,
            goal=goal
        )

        # Generate test case
        test_case = await self._analyzer.generate_test_case(
            prompt, request.judge_model, goal
        )

        return GenerateTestResponse(
            test_case=self._to_test_case_dto(test_case)
        )

    async def execute_prompt(self, request: ExecutePromptRequest) -> ExecutePromptResponse:
        """
        Execute a prompt with a target model.

        Args:
            request: Execution request

        Returns:
            ExecutePromptResponse: Execution result
        """
        from ...domain.models.prompt import ModelId

        start_time = datetime.now()

        # Execute prompt
        prompt_text = PromptText(request.prompt_text)
        model_id = ModelId(request.target_model)

        result = await self._llm_provider.generate_response(model_id, prompt_text)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        return ExecutePromptResponse(
            result=result,
            model_used=request.target_model,
            duration=duration
        )

    def _to_prompt_dto(self, prompt: Prompt) -> PromptDto:
        """Convert domain prompt to DTO."""
        return PromptDto(
            id=prompt.id.value,
            text=prompt.text.content,
            goal=prompt.goal.description if prompt.goal else None,
            created_at=prompt.created_at,
            updated_at=prompt.updated_at
        )

    def _to_analysis_dto(self, analysis) -> AnalysisDto:
        """Convert domain analysis to DTO."""
        return AnalysisDto(
            prompt_id=analysis.prompt_id.value,
            goal_alignment=analysis.goal_alignment.value,
            effectiveness=analysis.effectiveness.value,
            suggestions=analysis.suggestions,
            status=analysis.status.value,
            inferred_goal=analysis.inferred_goal.description if analysis.inferred_goal else None,
            created_at=analysis.created_at
        )

    def _to_fragment_dto(self, fragment) -> FragmentDto:
        """Convert domain fragment to DTO."""
        return FragmentDto(
            text=fragment.text,
            fragment_type=fragment.fragment_type,
            goal_alignment=fragment.goal_alignment.value,
            improvement_suggestion=fragment.improvement_suggestion
        )

    def _to_test_case_dto(self, test_case) -> TestCaseDto:
        """Convert domain test case to DTO."""
        return TestCaseDto(
            input_variables=test_case.input_variables,
            expected_output=test_case.expected_output,
            goal_relevance=test_case.goal_relevance.value
        )