"""
Application service for prompt operations.
"""

from typing import Optional, List, Dict
from datetime import datetime
import uuid
import asyncio

from ..dto import (
    PromptDto, AnalysisDto, FragmentDto, TestCaseDto,
    AnalyzePromptRequest, AnalyzePromptResponse,
    GenerateTestRequest, GenerateTestResponse,
    ExecutePromptRequest, ExecutePromptResponse
)
from ...domain.models.prompt import (
    Prompt, PromptId, PromptRepository, LLMProvider, ModelId
)
from ...domain.models.execution import (
    ExecutionId, TokenUsage, ModelExecution, MultiModelResult
)
from ...domain.models.comparison import ComparisonResult
from ...domain.services.prompt_analyzer import PromptAnalyzer
from ...domain.services.comparison_engine import ComparisonEngine


class PromptService:
    """Application service for prompt operations."""

    def __init__(self, prompt_repository: PromptRepository,
                 llm_provider: LLMProvider,
                 judge_model: str = "gpt-4o-mini"):
        self._repository = prompt_repository
        self._analyzer = PromptAnalyzer(llm_provider)
        self._llm_provider = llm_provider
        self._comparison_engine = ComparisonEngine(
            llm_provider=llm_provider,
            judge_model=judge_model
        )

    async def create_prompt(self, name: str, content: str, goal: Optional[str] = None,
                          description: str = "", category: str = "general",
                          tags: Optional[List[str]] = None, author: str = "unknown") -> PromptDto:
        """
        Create a new prompt.

        Args:
            name: Prompt name
            content: Prompt content (may contain {{variables}})
            goal: Optional goal description
            description: Optional description
            category: Category
            tags: Optional tags
            author: Author name

        Returns:
            PromptDto: Created prompt
        """
        prompt = Prompt.create(
            name=name,
            content=content,
            description=description or f"Prompt: {name}",
            goal=goal,
            category=category,
            tags=set(tags) if tags else set(),
            author=author
        )

        # Save prompt
        await self._repository.save(prompt)

        return self._to_prompt_dto(prompt)

    async def get_prompt(self, prompt_id: str) -> Optional[PromptDto]:
        """
        Get a prompt by ID.

        Args:
            prompt_id: Prompt identifier

        Returns:
            Optional[PromptDto]: Prompt if found
        """
        prompt = await self._repository.find_by_id(PromptId(prompt_id))
        return self._to_prompt_dto(prompt) if prompt else None

    async def list_prompts(self, category: Optional[str] = None,
                          has_variables: Optional[bool] = None) -> List[PromptDto]:
        """
        List all prompts with optional filtering.

        Args:
            category: Filter by category
            has_variables: Filter by whether prompts have template variables

        Returns:
            List[PromptDto]: List of prompts
        """
        prompts = await self._repository.find_all(
            category=category,
            has_variables=has_variables
        )
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
        prompt = Prompt.create(
            name="temp_analysis",
            content=request.prompt_text,
            goal=request.goal
        )

        # Perform analysis
        analysis_result = await self._analyzer.analyze_prompt(
            prompt, request.judge_model, request.goal
        )

        # Generate fragments analysis
        fragments = await self._analyzer.analyze_fragments(
            prompt, request.judge_model, request.goal
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
        prompt = Prompt.create(
            name="temp_test",
            content=request.prompt_text,
            goal=request.goal
        )

        # Generate test case
        test_case = await self._analyzer.generate_test_case(
            prompt, request.judge_model, request.goal
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
        start_time = datetime.now()

        # Execute prompt
        model_id = ModelId(request.target_model)
        result = await self._llm_provider.generate_response(model_id, request.prompt_text)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        return ExecutePromptResponse(
            result=result,
            model_used=request.target_model,
            duration=duration
        )

    async def render_prompt(self, prompt_id: str, variables: dict) -> str:
        """
        Render a prompt template with variables.

        Args:
            prompt_id: Prompt identifier
            variables: Variable values

        Returns:
            str: Rendered prompt content

        Raises:
            ValueError: If prompt not found or missing variables
        """
        prompt = await self._repository.find_by_id(PromptId(prompt_id))
        if not prompt:
            raise ValueError(f"Prompt '{prompt_id}' not found")

        return prompt.render(variables)

    def _to_prompt_dto(self, prompt: Prompt) -> PromptDto:
        """Convert domain prompt to DTO."""
        return PromptDto(
            id=prompt.id.value,
            text=prompt.content,  # Use 'text' for backward compatibility
            goal=prompt.goal,
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

    # =========================================================================
    # Multi-Model Execution and Comparison
    # =========================================================================

    async def execute_multi_model(
        self,
        prompt_text: str,
        models: List[str],
        prompt_id: Optional[str] = None,
        variables: Optional[Dict[str, str]] = None
    ) -> MultiModelResult:
        """
        Execute a prompt across multiple models in parallel.

        Args:
            prompt_text: The prompt text (or template)
            models: List of model IDs to execute against
            prompt_id: Optional prompt ID for tracking
            variables: Optional variables for template rendering

        Returns:
            MultiModelResult with all model executions
        """
        # Render template if variables provided
        final_prompt = prompt_text
        if variables:
            # Simple variable substitution
            import re
            for key, value in variables.items():
                pattern = rf'\{{\{{\s*{re.escape(key)}\s*\}}\}}'
                final_prompt = re.sub(pattern, str(value), final_prompt)

        # Execute in parallel
        model_ids = [ModelId(m) for m in models]
        start_time = datetime.now()

        results = await self._llm_provider.generate_responses(model_ids, final_prompt)

        total_duration = (datetime.now() - start_time).total_seconds() * 1000

        # Build executions
        executions = []
        for model, output in results.items():
            is_error = output.startswith("Error:")
            executions.append(ModelExecution(
                id=ExecutionId.generate(),
                model=model,
                output=output,
                latency_ms=total_duration / len(models),  # Approximate per-model
                success=not is_error,
                error=output if is_error else None
            ))

        return MultiModelResult(
            prompt_id=PromptId(prompt_id) if prompt_id else PromptId.generate(),
            prompt_text=final_prompt,
            executions=executions,
            total_duration_ms=total_duration
        )

    async def execute_and_compare(
        self,
        prompt_text: str,
        models: List[str],
        prompt_id: Optional[str] = None,
        goal: Optional[str] = None,
        reference_output: Optional[str] = None,
        variables: Optional[Dict[str, str]] = None,
        include_llm_assessment: bool = True
    ) -> Dict:
        """
        Execute prompt across multiple models and compare outputs.

        Args:
            prompt_text: The prompt text (or template)
            models: List of model IDs to execute against
            prompt_id: Optional prompt ID for tracking
            goal: Goal for LLM assessment context
            reference_output: Optional reference output for comparison
            variables: Optional variables for template rendering
            include_llm_assessment: Whether to include LLM-as-judge evaluation

        Returns:
            Dictionary with execution results and comparison
        """
        # Execute across models
        multi_result = await self.execute_multi_model(
            prompt_text=prompt_text,
            models=models,
            prompt_id=prompt_id,
            variables=variables
        )

        # Compare outputs
        comparison = await self._comparison_engine.compare_outputs(
            multi_model_result=multi_result,
            prompt_goal=goal,
            reference_output=reference_output,
            include_llm_assessment=include_llm_assessment
        )

        # Convert to response format
        return {
            "prompt_id": multi_result.prompt_id.value,
            "prompt_text": multi_result.prompt_text,
            "total_duration_ms": multi_result.total_duration_ms,
            "executions": [
                {
                    "id": e.id.value,
                    "model": e.model,
                    "output": e.output,
                    "latency_ms": e.latency_ms,
                    "success": e.success,
                    "error": e.error
                }
                for e in multi_result.executions
            ],
            "comparison": {
                "semantic_similarities": [
                    {
                        "model_a": s.model_a,
                        "model_b": s.model_b,
                        "similarity_score": s.similarity_score,
                        "method": s.method
                    }
                    for s in comparison.semantic_similarities
                ],
                "llm_assessment": self._format_llm_assessment(comparison.llm_assessment) if comparison.llm_assessment else None,
                "model_metrics": {
                    model: {
                        "output_length": m.output_length,
                        "latency_ms": m.latency_ms,
                        "token_count": m.token_count,
                        "semantic_similarity_avg": m.semantic_similarity_avg,
                        "llm_evaluation_score": m.llm_evaluation_score
                    }
                    for model, m in comparison.model_metrics.items()
                },
                "summary": {
                    "total_models": comparison.summary.total_models,
                    "best_performing_model": comparison.summary.best_performing_model,
                    "fastest_model": comparison.summary.fastest_model,
                    "average_agreement_score": comparison.summary.average_agreement_score,
                    "most_similar_pair": comparison.summary.most_similar_pair,
                    "least_similar_pair": comparison.summary.least_similar_pair
                }
            }
        }

    def _format_llm_assessment(self, assessment) -> Dict:
        """Format LLM assessment for response."""
        return {
            "judge_model": assessment.judge_model,
            "evaluations": [
                {
                    "model": e.model,
                    "scores": e.scores,
                    "overall_score": e.overall_score,
                    "strengths": e.strengths,
                    "weaknesses": e.weaknesses
                }
                for e in assessment.evaluations
            ],
            "recommendation": assessment.recommendation,
            "key_differences": assessment.key_differences
        }

    def get_available_models(self) -> List[str]:
        """Get list of available models for execution."""
        return self._llm_provider.get_available_models()
