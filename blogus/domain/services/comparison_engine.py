"""
Domain service for comparing LLM outputs using embeddings and LLM-as-judge.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import asyncio
import numpy as np

from ..models.comparison import (
    ComparisonId, SemanticSimilarity, ModelEvaluation, LLMAssessment,
    ComparisonResult, ModelMetrics, ComparisonSummary
)
from ..models.execution import MultiModelResult, ModelExecution
from ..models.prompt import LLMProvider, ModelId


class EmbeddingService:
    """Service for computing text embeddings using sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._model = None
        self._model_name = model_name

    def _ensure_model_loaded(self):
        """Lazy load the embedding model."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)

    def compute_embedding(self, text: str) -> np.ndarray:
        """Compute embedding for a single text."""
        self._ensure_model_loaded()
        return self._model.encode(text, convert_to_numpy=True)

    def compute_embeddings(self, texts: List[str]) -> np.ndarray:
        """Compute embeddings for multiple texts in batch."""
        self._ensure_model_loaded()
        return self._model.encode(texts, convert_to_numpy=True)

    def cosine_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Compute cosine similarity between two embeddings."""
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(dot_product / (norm1 * norm2))


class ComparisonEngine:
    """
    Engine for comparing outputs from multiple LLM models.

    Uses both:
    1. Semantic similarity via embeddings (fast, objective)
    2. LLM-as-judge evaluation (detailed, qualitative)
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        embedding_model: str = "all-MiniLM-L6-v2",
        judge_model: str = "gpt-4o-mini"
    ):
        self._llm_provider = llm_provider
        self._embedding_service = EmbeddingService(embedding_model)
        self._judge_model = ModelId(judge_model)

    async def compare_outputs(
        self,
        multi_model_result: MultiModelResult,
        prompt_goal: Optional[str] = None,
        reference_output: Optional[str] = None,
        include_llm_assessment: bool = True
    ) -> ComparisonResult:
        """
        Compare outputs from multiple models.

        Args:
            multi_model_result: Results from multi-model execution
            prompt_goal: Optional goal for evaluation context
            reference_output: Optional reference/expected output for comparison
            include_llm_assessment: Whether to include LLM-as-judge evaluation

        Returns:
            ComparisonResult with semantic and LLM-based comparisons
        """
        executions = multi_model_result.executions

        if len(executions) < 2:
            return self._create_single_model_result(
                multi_model_result, prompt_goal, reference_output
            )

        # Compute semantic similarities between all pairs
        semantic_similarities = await self._compute_semantic_similarities(
            executions, reference_output
        )

        # Get LLM-based assessment if requested
        llm_assessment = None
        if include_llm_assessment:
            llm_assessment = await self._compute_llm_assessment(
                executions, prompt_goal, reference_output
            )

        # Compute per-model metrics
        model_metrics = self._compute_model_metrics(
            executions, semantic_similarities, llm_assessment
        )

        # Generate summary
        summary = self._generate_summary(model_metrics, semantic_similarities)

        return ComparisonResult(
            id=ComparisonId.generate(),
            prompt_id=multi_model_result.prompt_id,
            executions=executions,
            semantic_similarities=semantic_similarities,
            llm_assessment=llm_assessment,
            model_metrics=model_metrics,
            summary=summary
        )

    async def _compute_semantic_similarities(
        self,
        executions: List[ModelExecution],
        reference_output: Optional[str] = None
    ) -> List[SemanticSimilarity]:
        """Compute pairwise semantic similarities between all outputs."""
        similarities = []

        # Extract outputs
        outputs = [e.output for e in executions]
        models = [e.model for e in executions]

        # Add reference if provided
        if reference_output:
            outputs.append(reference_output)
            models.append("reference")

        # Compute all embeddings in batch
        embeddings = self._embedding_service.compute_embeddings(outputs)

        # Compute pairwise similarities
        for i in range(len(outputs)):
            for j in range(i + 1, len(outputs)):
                similarity = self._embedding_service.cosine_similarity(
                    embeddings[i], embeddings[j]
                )
                similarities.append(SemanticSimilarity(
                    model_a=models[i],
                    model_b=models[j],
                    similarity_score=similarity,
                    method="cosine_similarity"
                ))

        return similarities

    async def _compute_llm_assessment(
        self,
        executions: List[ModelExecution],
        prompt_goal: Optional[str],
        reference_output: Optional[str]
    ) -> LLMAssessment:
        """Use LLM-as-judge to evaluate and compare outputs."""
        goal_text = prompt_goal or "produce a helpful and accurate response"

        # Build comparison prompt
        outputs_text = "\n\n".join([
            f"=== MODEL: {e.model} ===\n{e.output}"
            for e in executions
        ])

        reference_section = ""
        if reference_output:
            reference_section = f"\n\n=== REFERENCE OUTPUT ===\n{reference_output}"

        judge_prompt = f"""You are an expert evaluator comparing LLM outputs.
Evaluate each response based on the stated goal.

GOAL: {goal_text}
{reference_section}

OUTPUTS TO COMPARE:
{outputs_text}

Evaluate each model's output on these criteria (score 1-10 for each):
1. Goal Achievement: How well does the output achieve the stated goal?
2. Accuracy: Is the information correct and reliable?
3. Clarity: Is the output clear, well-organized, and easy to understand?
4. Completeness: Does the output cover all relevant aspects?

Also provide:
- An overall recommendation for which model(s) performed best
- Key differences between the outputs
- Specific strengths and weaknesses for each model

Respond with ONLY a JSON object in this exact format (no markdown, no extra text):
{{
    "evaluations": [
        {{
            "model": "<model_name>",
            "scores": {{
                "goal_achievement": <1-10>,
                "accuracy": <1-10>,
                "clarity": <1-10>,
                "completeness": <1-10>
            }},
            "strengths": ["strength1", "strength2"],
            "weaknesses": ["weakness1", "weakness2"]
        }}
    ],
    "recommendation": "Brief explanation of which model(s) performed best and why",
    "key_differences": ["difference1", "difference2", "difference3"]
}}
"""

        try:
            response = await self._llm_provider.generate_response(
                self._judge_model, judge_prompt
            )
            return self._parse_llm_assessment(response, executions)

        except Exception as e:
            # Return a default assessment on failure
            return LLMAssessment(
                judge_model=self._judge_model.value,
                evaluations=[
                    ModelEvaluation(
                        model=e.model,
                        scores={
                            "goal_achievement": 5,
                            "accuracy": 5,
                            "clarity": 5,
                            "completeness": 5
                        },
                        overall_score=5.0,
                        strengths=["Unable to evaluate"],
                        weaknesses=["LLM assessment failed"]
                    )
                    for e in executions
                ],
                recommendation=f"Assessment failed: {str(e)}",
                key_differences=[]
            )

    def _parse_llm_assessment(
        self,
        response: str,
        executions: List[ModelExecution]
    ) -> LLMAssessment:
        """Parse LLM judge response into structured assessment."""
        import json
        import re

        # Try to extract JSON from response
        response = response.strip()
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            response = json_match.group(0)

        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            # Return default on parse failure
            return self._create_default_assessment(executions)

        evaluations = []
        for eval_data in data.get("evaluations", []):
            scores = eval_data.get("scores", {})
            overall = sum(scores.values()) / len(scores) if scores else 5.0

            evaluations.append(ModelEvaluation(
                model=eval_data.get("model", "unknown"),
                scores=scores,
                overall_score=overall,
                strengths=eval_data.get("strengths", []),
                weaknesses=eval_data.get("weaknesses", [])
            ))

        return LLMAssessment(
            judge_model=self._judge_model.value,
            evaluations=evaluations,
            recommendation=data.get("recommendation", "No recommendation"),
            key_differences=data.get("key_differences", [])
        )

    def _create_default_assessment(
        self,
        executions: List[ModelExecution]
    ) -> LLMAssessment:
        """Create default assessment when parsing fails."""
        return LLMAssessment(
            judge_model=self._judge_model.value,
            evaluations=[
                ModelEvaluation(
                    model=e.model,
                    scores={
                        "goal_achievement": 5,
                        "accuracy": 5,
                        "clarity": 5,
                        "completeness": 5
                    },
                    overall_score=5.0,
                    strengths=[],
                    weaknesses=[]
                )
                for e in executions
            ],
            recommendation="Unable to parse evaluation",
            key_differences=[]
        )

    def _compute_model_metrics(
        self,
        executions: List[ModelExecution],
        similarities: List[SemanticSimilarity],
        llm_assessment: Optional[LLMAssessment]
    ) -> Dict[str, ModelMetrics]:
        """Compute aggregated metrics for each model."""
        metrics = {}

        for execution in executions:
            model = execution.model

            # Get average similarity to other models
            model_similarities = [
                s.similarity_score for s in similarities
                if s.model_a == model or s.model_b == model
            ]
            avg_similarity = (
                sum(model_similarities) / len(model_similarities)
                if model_similarities else 0.0
            )

            # Get LLM evaluation scores
            llm_score = None
            if llm_assessment:
                for eval in llm_assessment.evaluations:
                    if eval.model == model:
                        llm_score = eval.overall_score
                        break

            metrics[model] = ModelMetrics(
                model=model,
                output_length=len(execution.output),
                latency_ms=execution.latency_ms,
                token_count=execution.token_usage.total if execution.token_usage else 0,
                semantic_similarity_avg=avg_similarity,
                llm_evaluation_score=llm_score
            )

        return metrics

    def _generate_summary(
        self,
        model_metrics: Dict[str, ModelMetrics],
        similarities: List[SemanticSimilarity]
    ) -> ComparisonSummary:
        """Generate high-level summary of the comparison."""
        # Find best model by LLM score if available
        best_model = None
        best_score = -1
        fastest_model = None
        fastest_time = float('inf')

        for model, metrics in model_metrics.items():
            if metrics.llm_evaluation_score and metrics.llm_evaluation_score > best_score:
                best_score = metrics.llm_evaluation_score
                best_model = model
            if metrics.latency_ms < fastest_time:
                fastest_time = metrics.latency_ms
                fastest_model = model

        # Calculate average agreement
        avg_agreement = (
            sum(s.similarity_score for s in similarities) / len(similarities)
            if similarities else 0.0
        )

        # Find most and least similar pairs
        most_similar = max(similarities, key=lambda s: s.similarity_score) if similarities else None
        least_similar = min(similarities, key=lambda s: s.similarity_score) if similarities else None

        return ComparisonSummary(
            total_models=len(model_metrics),
            best_performing_model=best_model,
            fastest_model=fastest_model,
            average_agreement_score=avg_agreement,
            most_similar_pair=(most_similar.model_a, most_similar.model_b) if most_similar else None,
            least_similar_pair=(least_similar.model_a, least_similar.model_b) if least_similar else None
        )

    def _create_single_model_result(
        self,
        multi_model_result: MultiModelResult,
        prompt_goal: Optional[str],
        reference_output: Optional[str]
    ) -> ComparisonResult:
        """Create a comparison result for single model (no comparison needed)."""
        executions = multi_model_result.executions
        execution = executions[0] if executions else None

        if not execution:
            return ComparisonResult(
                id=ComparisonId.generate(),
                prompt_id=multi_model_result.prompt_id,
                executions=[],
                semantic_similarities=[],
                llm_assessment=None,
                model_metrics={},
                summary=ComparisonSummary(
                    total_models=0,
                    best_performing_model=None,
                    fastest_model=None,
                    average_agreement_score=0.0,
                    most_similar_pair=None,
                    least_similar_pair=None
                )
            )

        # If reference output provided, compute similarity
        similarities = []
        if reference_output:
            embeddings = self._embedding_service.compute_embeddings(
                [execution.output, reference_output]
            )
            similarity = self._embedding_service.cosine_similarity(
                embeddings[0], embeddings[1]
            )
            similarities.append(SemanticSimilarity(
                model_a=execution.model,
                model_b="reference",
                similarity_score=similarity,
                method="cosine_similarity"
            ))

        metrics = {
            execution.model: ModelMetrics(
                model=execution.model,
                output_length=len(execution.output),
                latency_ms=execution.latency_ms,
                token_count=execution.token_usage.total if execution.token_usage else 0,
                semantic_similarity_avg=similarities[0].similarity_score if similarities else 1.0,
                llm_evaluation_score=None
            )
        }

        return ComparisonResult(
            id=ComparisonId.generate(),
            prompt_id=multi_model_result.prompt_id,
            executions=executions,
            semantic_similarities=similarities,
            llm_assessment=None,
            model_metrics=metrics,
            summary=ComparisonSummary(
                total_models=1,
                best_performing_model=execution.model,
                fastest_model=execution.model,
                average_agreement_score=1.0,
                most_similar_pair=None,
                least_similar_pair=None
            )
        )
