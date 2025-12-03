"""
LiteLLM implementation of LLMProvider interface.
"""

import json
import re
from typing import Optional, List, Dict
from litellm import completion
import time
import asyncio

from ...domain.models.prompt import (
    LLMProvider, ModelId, Goal, AnalysisResult,
    Score, Fragment, PromptTestCase, PromptId
)
from ...shared.exceptions import LLMAPIError, RateLimitError, AuthenticationError, ModelNotAvailableError


class LiteLLMProvider(LLMProvider):
    """LiteLLM implementation of the LLM provider interface."""

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self._available_models = {
            "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo",
            "claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307",
            "claude-3-5-sonnet-20241022",
            "groq/llama3-70b-8192", "groq/mixtral-8x7b-32768", "groq/gemma-7b-it"
        }

    async def generate_response(self, model: ModelId, prompt: str) -> str:
        """Generate response from LLM."""
        return await self._call_llm(model.value, prompt)

    async def generate_responses(self, models: List[ModelId], prompt: str) -> Dict[str, str]:
        """Generate responses from multiple models in parallel."""
        async def call_model(model_id: ModelId) -> tuple[str, str]:
            try:
                response = await self._call_llm(model_id.value, prompt)
                return (model_id.value, response)
            except Exception as e:
                return (model_id.value, f"Error: {str(e)}")

        tasks = [call_model(m) for m in models]
        results = await asyncio.gather(*tasks)
        return dict(results)

    async def infer_goal(self, model: ModelId, prompt: str) -> Goal:
        """Infer the goal/purpose of a prompt using LLM."""
        inference_prompt = f"""Analyze the following prompt and infer its primary goal or purpose.
Be specific and concise. Focus on what the prompt is trying to achieve.

Prompt to analyze:
\"\"\"
{prompt}
\"\"\"

Respond with ONLY a JSON object in this exact format (no markdown, no extra text):
{{"goal": "A clear, specific description of what this prompt aims to achieve"}}
"""

        response = await self._call_llm(model.value, inference_prompt, max_tokens=500)

        try:
            # Try to extract JSON from the response
            data = self._extract_json(response)
            goal_text = data.get("goal", "").strip()

            if not goal_text:
                # Fallback: use the response directly if it's reasonable
                goal_text = self._clean_response(response)

            if not goal_text:
                goal_text = "Generate a helpful and accurate response based on the given instructions"

            return Goal(goal_text)

        except (json.JSONDecodeError, KeyError, ValueError):
            # Fallback: try to use the raw response as the goal
            cleaned = self._clean_response(response)
            if cleaned:
                return Goal(cleaned)
            return Goal("Generate a helpful and accurate response based on the given instructions")

    async def analyze_fragments(self, model: ModelId, prompt: str, goal: str) -> List[Fragment]:
        """Analyze prompt fragments for goal alignment."""
        analysis_prompt = f"""Analyze the following prompt by breaking it into logical fragments/sections.
For each fragment, evaluate how well it aligns with the stated goal.

Prompt to analyze:
\"\"\"
{prompt}
\"\"\"

Goal: {goal}

Identify distinct parts of the prompt such as:
- Instructions (what the AI should do)
- Context (background information)
- Examples (demonstrations or samples)
- Constraints (limitations or requirements)
- Output format (how to structure the response)

Respond with ONLY a JSON object in this exact format (no markdown, no extra text):
{{
    "fragments": [
        {{
            "text": "The exact text of this fragment from the prompt",
            "type": "instruction|context|example|constraint|output_format|other",
            "goal_alignment": <score 1-10 where 10 is perfectly aligned>,
            "improvement": "Specific suggestion to improve this fragment, or 'None needed' if good"
        }}
    ]
}}

Identify at least 2-5 meaningful fragments. Be thorough but don't over-fragment.
"""

        response = await self._call_llm(model.value, analysis_prompt, max_tokens=2000)

        try:
            data = self._extract_json(response)
            fragments = []

            for frag_data in data.get("fragments", []):
                text = frag_data.get("text", "").strip()
                if not text:
                    continue

                frag_type = frag_data.get("type", "other").strip().lower()
                if frag_type not in ["instruction", "context", "example", "constraint", "output_format", "other"]:
                    frag_type = "other"

                alignment = int(frag_data.get("goal_alignment", 5))
                alignment = max(1, min(10, alignment))

                improvement = frag_data.get("improvement", "Consider reviewing this section").strip()
                if not improvement:
                    improvement = "No specific improvements identified"

                fragments.append(Fragment(
                    text=text[:500],  # Limit fragment text length
                    fragment_type=frag_type,
                    goal_alignment=Score(alignment, 10),
                    improvement_suggestion=improvement
                ))

            # If no fragments were parsed, create a default one
            if not fragments:
                fragments = [self._create_default_fragment(prompt)]

            return fragments

        except (json.JSONDecodeError, KeyError, ValueError):
            # Return a default fragment on parse failure
            return [self._create_default_fragment(prompt)]

    async def generate_test_cases(self, model: ModelId, prompt: str, goal: str, num_cases: int = 3) -> List[PromptTestCase]:
        """Generate test cases for the prompt."""
        # Detect if the prompt has template variables
        template_vars = re.findall(r'\{\{(\w+)\}\}', prompt)

        if template_vars:
            return await self._generate_template_test_cases(model, prompt, goal, template_vars, num_cases)
        else:
            return await self._generate_standard_test_cases(model, prompt, goal, num_cases)

    async def _generate_template_test_cases(
        self, model: ModelId, prompt: str, goal: str,
        template_vars: List[str], num_cases: int
    ) -> List[PromptTestCase]:
        """Generate test cases for template prompts with variables."""
        vars_list = ", ".join(template_vars)

        generation_prompt = f"""Generate {num_cases} diverse test cases for the following prompt template.

Prompt template:
\"\"\"
{prompt}
\"\"\"

Template variables to fill: {vars_list}
Goal of this prompt: {goal}

For each test case, provide realistic values for the variables and describe what a good response should contain.

Respond with ONLY a JSON object in this exact format (no markdown, no extra text):
{{
    "test_cases": [
        {{
            "variables": {{"var_name": "value", ...}},
            "expected_output_description": "Description of what a correct response should contain or achieve",
            "goal_relevance": <score 1-10 indicating how well this test case evaluates the goal>
        }}
    ]
}}

Make test cases diverse - include edge cases, typical cases, and challenging scenarios.
"""

        response = await self._call_llm(model.value, generation_prompt, max_tokens=2000)

        try:
            data = self._extract_json(response)
            test_cases = []

            for tc_data in data.get("test_cases", []):
                variables = tc_data.get("variables", {})
                if not isinstance(variables, dict):
                    continue

                # Convert all values to strings
                variables = {k: str(v) for k, v in variables.items()}

                expected = tc_data.get("expected_output_description", "").strip()
                if not expected:
                    expected = "Response should address the prompt appropriately"

                relevance = int(tc_data.get("goal_relevance", 7))
                relevance = max(1, min(10, relevance))

                test_cases.append(PromptTestCase(
                    input_variables=variables,
                    expected_output=expected,
                    goal_relevance=Score(relevance, 10)
                ))

            if not test_cases:
                test_cases = [self._create_default_test_case(template_vars)]

            return test_cases[:num_cases]

        except (json.JSONDecodeError, KeyError, ValueError):
            return [self._create_default_test_case(template_vars)]

    async def _generate_standard_test_cases(
        self, model: ModelId, prompt: str, goal: str, num_cases: int
    ) -> List[PromptTestCase]:
        """Generate test cases for standard (non-template) prompts."""
        generation_prompt = f"""Generate {num_cases} diverse test scenarios for evaluating responses to the following prompt.

Prompt:
\"\"\"
{prompt}
\"\"\"

Goal of this prompt: {goal}

For each test scenario, describe:
1. A specific input or context variation
2. What a successful response should contain or achieve

Respond with ONLY a JSON object in this exact format (no markdown, no extra text):
{{
    "test_cases": [
        {{
            "scenario": "Description of the test scenario or input variation",
            "expected_output_description": "Description of what a correct response should contain",
            "goal_relevance": <score 1-10 indicating how well this test evaluates the goal>
        }}
    ]
}}

Include diverse scenarios: typical use, edge cases, and challenging inputs.
"""

        response = await self._call_llm(model.value, generation_prompt, max_tokens=2000)

        try:
            data = self._extract_json(response)
            test_cases = []

            for tc_data in data.get("test_cases", []):
                scenario = tc_data.get("scenario", "").strip()
                expected = tc_data.get("expected_output_description", "").strip()

                if not expected:
                    expected = "Response should appropriately address the prompt"

                relevance = int(tc_data.get("goal_relevance", 7))
                relevance = max(1, min(10, relevance))

                test_cases.append(PromptTestCase(
                    input_variables={"scenario": scenario} if scenario else {"input": "standard"},
                    expected_output=expected,
                    goal_relevance=Score(relevance, 10)
                ))

            if not test_cases:
                test_cases = [PromptTestCase(
                    input_variables={"scenario": "Standard use case"},
                    expected_output="Response should address the prompt goals effectively",
                    goal_relevance=Score(7, 10)
                )]

            return test_cases[:num_cases]

        except (json.JSONDecodeError, KeyError, ValueError):
            return [PromptTestCase(
                input_variables={"scenario": "Standard evaluation"},
                expected_output="Response should meet the stated objectives",
                goal_relevance=Score(7, 10)
            )]

    async def analyze_prompt(self, model: ModelId, prompt: str, goal: Optional[str], prompt_id: PromptId) -> AnalysisResult:
        """Comprehensive prompt analysis using LLM."""
        goal_text = goal if goal else "general effectiveness and clarity"

        analysis_prompt = f"""You are an expert prompt engineer. Analyze the following prompt for effectiveness and quality.

Prompt to analyze:
\"\"\"
{prompt}
\"\"\"

Evaluation goal: {goal_text}

Evaluate the prompt on these criteria:
1. Goal Alignment (1-10): How well does the prompt guide toward achieving the stated goal?
2. Effectiveness (1-10): How likely is this prompt to produce high-quality, useful responses?

Consider factors like:
- Clarity and specificity of instructions
- Appropriate context and constraints
- Good examples (if applicable)
- Output format guidance
- Potential for misinterpretation
- Completeness of information

Respond with ONLY a JSON object in this exact format (no markdown, no extra text):
{{
    "goal_alignment": <score 1-10>,
    "effectiveness": <score 1-10>,
    "suggestions": [
        "Specific, actionable suggestion 1",
        "Specific, actionable suggestion 2",
        "Specific, actionable suggestion 3"
    ],
    "strengths": ["strength 1", "strength 2"],
    "weaknesses": ["weakness 1", "weakness 2"]
}}

Be critical but constructive. Provide specific, actionable suggestions.
"""

        response = await self._call_llm(model.value, analysis_prompt, max_tokens=1500)

        try:
            data = self._extract_json(response)

            goal_alignment = int(data.get("goal_alignment", 5))
            goal_alignment = max(1, min(10, goal_alignment))

            effectiveness = int(data.get("effectiveness", 5))
            effectiveness = max(1, min(10, effectiveness))

            suggestions = data.get("suggestions", [])
            if not isinstance(suggestions, list):
                suggestions = [str(suggestions)]
            suggestions = [str(s).strip() for s in suggestions if s]

            if not suggestions:
                suggestions = ["Review the prompt for clarity and specificity"]

            # Get fragments and test cases
            fragments = await self.analyze_fragments(model, prompt, goal_text)
            test_cases = await self.generate_test_cases(model, prompt, goal_text, num_cases=2)

            return AnalysisResult(
                prompt_id=prompt_id,
                goal_alignment=Score(goal_alignment, 10),
                effectiveness=Score(effectiveness, 10),
                suggestions=suggestions[:5],  # Limit to 5 suggestions
                fragments=fragments
            )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Fallback with reasonable defaults
            return AnalysisResult(
                prompt_id=prompt_id,
                goal_alignment=Score(5, 10),
                effectiveness=Score(5, 10),
                suggestions=[
                    "Unable to fully analyze - consider reviewing prompt structure",
                    "Ensure the prompt has clear instructions",
                    "Add specific examples if applicable"
                ],
                fragments=[self._create_default_fragment(prompt)]
            )

    def is_model_available(self, model: ModelId) -> bool:
        """Check if model is available."""
        return model.value in self._available_models

    def get_available_models(self) -> List[str]:
        """Get list of available model IDs."""
        return list(self._available_models)

    def _extract_json(self, response: str) -> dict:
        """Extract JSON from response, handling markdown code blocks."""
        # Remove markdown code blocks if present
        response = response.strip()

        # Try to find JSON in code blocks
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response)
        if json_match:
            response = json_match.group(1).strip()

        # Try to find JSON object directly
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            response = json_match.group(0)

        return json.loads(response)

    def _clean_response(self, response: str) -> str:
        """Clean and extract meaningful text from a response."""
        # Remove JSON artifacts
        response = re.sub(r'[\{\}\[\]"]', '', response)
        response = re.sub(r'goal\s*:', '', response, flags=re.IGNORECASE)
        response = response.strip()

        # Limit length
        if len(response) > 200:
            response = response[:200].rsplit(' ', 1)[0] + "..."

        return response

    def _create_default_fragment(self, prompt_content: str) -> Fragment:
        """Create a default fragment when parsing fails."""
        text = prompt_content[:200] + "..." if len(prompt_content) > 200 else prompt_content
        return Fragment(
            text=text,
            fragment_type="instruction",
            goal_alignment=Score(5, 10),
            improvement_suggestion="Review this section for clarity and alignment with goals"
        )

    def _create_default_test_case(self, template_vars: List[str] = None) -> PromptTestCase:
        """Create a default test case when generation fails."""
        if template_vars:
            variables = {var: f"sample_{var}" for var in template_vars}
        else:
            variables = {"input": "sample input"}

        return PromptTestCase(
            input_variables=variables,
            expected_output="Response should appropriately address the prompt",
            goal_relevance=Score(5, 10)
        )

    async def _call_llm(self, model: str, prompt: str, max_tokens: int = 1000) -> str:
        """Make LLM API call with error handling and retries."""
        for attempt in range(self.max_retries + 1):
            try:
                response = completion(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=0.7,
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
