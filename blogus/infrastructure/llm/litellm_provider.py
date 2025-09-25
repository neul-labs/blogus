"""
LiteLLM implementation of LLMProvider interface.
"""

import json
from typing import Optional, Dict, Any
from litellm import completion
import time

from ...domain.models.prompt import LLMProvider, ModelId, PromptText, Goal, AnalysisResult, Score, Fragment, TestCase, PromptId
from ...shared.exceptions import LLMAPIError, RateLimitError, AuthenticationError, ModelNotAvailableError


class LiteLLMProvider(LLMProvider):
    """LiteLLM implementation of the LLM provider interface."""

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self._available_models = {
            "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo",
            "claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307",
            "groq/llama3-70b-8192", "groq/mixtral-8x7b-32768", "groq/gemma-7b-it"
        }

    async def generate_response(self, model: ModelId, prompt: PromptText) -> str:
        """Generate response from LLM."""
        return await self._call_llm(model.value, prompt.content)

    async def analyze_prompt(self, model: ModelId, prompt: PromptText, goal: Optional[Goal]) -> AnalysisResult:
        """Analyze prompt using LLM."""
        goal_text = goal.description if goal else "general effectiveness"

        analysis_prompt = f"""Analyze the following prompt for effectiveness and goal alignment:

Prompt: {prompt.content}

Goal: {goal_text}

Provide analysis in this JSON format:
{{
    "goal_alignment": <score 1-10>,
    "effectiveness": <score 1-10>,
    "suggestions": ["suggestion1", "suggestion2", ...],
    "fragments": [
        {{
            "text": "fragment text",
            "type": "instruction|context|example|constraint",
            "goal_alignment": <score 1-5>,
            "improvement_suggestion": "suggestion"
        }}
    ]
}}
"""

        response = await self._call_llm(model.value, analysis_prompt)

        try:
            data = json.loads(response)

            # Create fragments
            fragments = []
            for frag_data in data.get("fragments", []):
                fragments.append(Fragment(
                    text=frag_data["text"],
                    fragment_type=frag_data["type"],
                    goal_alignment=Score(frag_data["goal_alignment"], 5),
                    improvement_suggestion=frag_data["improvement_suggestion"]
                ))

            # Create test case (placeholder for now)
            test_cases = [TestCase(
                input_variables={"input": "sample"},
                expected_output="Expected output based on prompt analysis",
                goal_relevance=Score(8, 10)
            )]

            return AnalysisResult(
                prompt_id=PromptId("temp"),  # This would be set by the caller
                goal_alignment=Score(data["goal_alignment"]),
                effectiveness=Score(data["effectiveness"]),
                suggestions=data["suggestions"],
                fragments=fragments,
                test_cases=test_cases
            )

        except (json.JSONDecodeError, KeyError) as e:
            # Fallback to basic analysis if JSON parsing fails
            return AnalysisResult(
                prompt_id=PromptId("temp"),
                goal_alignment=Score(7),
                effectiveness=Score(7),
                suggestions=["Consider more specific instructions"],
                fragments=[],
                test_cases=[]
            )

    def is_model_available(self, model: ModelId) -> bool:
        """Check if model is available."""
        return model.value in self._available_models

    async def _call_llm(self, model: str, prompt: str, max_tokens: int = 1000) -> str:
        """Make LLM API call with error handling and retries."""
        for attempt in range(self.max_retries + 1):
            try:
                response = completion(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                )

                if not response or not hasattr(response, 'choices') or not response.choices:
                    raise LLMAPIError(f"Invalid response from model {model}")

                content = response.choices[0].message.content
                if not content:
                    raise LLMAPIError(f"Empty response from model {model}")

                return content

            except Exception as e:
                error_msg = str(e).lower()

                # Handle specific error types
                if 'rate limit' in error_msg or 'quota' in error_msg:
                    if attempt < self.max_retries:
                        wait_time = min(2 ** attempt, 60)
                        time.sleep(wait_time)
                        continue
                    raise RateLimitError(f"Rate limit exceeded for model {model}")

                elif 'authentication' in error_msg or 'unauthorized' in error_msg:
                    raise AuthenticationError(f"Authentication failed for model {model}")

                elif 'model not found' in error_msg or 'invalid model' in error_msg:
                    raise ModelNotAvailableError(f"Model {model} is not available")

                elif attempt < self.max_retries:
                    wait_time = min(1 * (attempt + 1), 10)
                    time.sleep(wait_time)
                    continue

                raise LLMAPIError(f"Unexpected error for model {model}: {str(e)}")

        raise LLMAPIError(f"Failed to get response from model {model} after {self.max_retries} retries")