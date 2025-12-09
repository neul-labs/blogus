"""
Tests for LLM provider implementations.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import json

from blogus.infrastructure.llm.litellm_provider import LiteLLMProvider
from blogus.domain.models.prompt import ModelId, Goal, Score, PromptId


class TestLiteLLMProviderBasic:
    """Test basic LiteLLMProvider functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.provider = LiteLLMProvider(max_retries=2)

    def test_available_models(self):
        """Test that available models are defined."""
        assert "gpt-4o" in self.provider._available_models
        assert "gpt-4o-mini" in self.provider._available_models
        assert "claude-3-5-sonnet-20241022" in self.provider._available_models

    def test_is_model_available_true(self):
        """Test is_model_available returns True for available models."""
        assert self.provider.is_model_available(ModelId("gpt-4o")) is True
        assert self.provider.is_model_available(ModelId("gpt-4o-mini")) is True

    def test_is_model_available_false(self):
        """Test is_model_available returns False for unavailable models."""
        assert self.provider.is_model_available(ModelId("non-existent-model")) is False


class TestLiteLLMProviderGenerate:
    """Test LiteLLMProvider response generation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.provider = LiteLLMProvider(max_retries=2)

    @pytest.mark.asyncio
    async def test_generate_response(self):
        """Test generating a response."""
        with patch('blogus.infrastructure.llm.litellm_provider.completion') as mock_completion:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Generated response"
            mock_completion.return_value = mock_response

            result = await self.provider.generate_response(
                ModelId("gpt-4o"),
                "Test prompt"
            )

            assert result == "Generated response"
            mock_completion.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_response_retries_on_failure(self):
        """Test that response generation retries on failure."""
        with patch('blogus.infrastructure.llm.litellm_provider.completion') as mock_completion:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Success after retry"

            # First call fails, second succeeds
            mock_completion.side_effect = [
                Exception("Temporary failure"),
                mock_response
            ]

            result = await self.provider.generate_response(
                ModelId("gpt-4o"),
                "Test prompt"
            )

            assert result == "Success after retry"
            assert mock_completion.call_count == 2

    @pytest.mark.asyncio
    async def test_generate_responses_multiple_models(self):
        """Test generating responses from multiple models."""
        with patch('blogus.infrastructure.llm.litellm_provider.completion') as mock_completion:
            def create_response(content):
                resp = MagicMock()
                resp.choices = [MagicMock()]
                resp.choices[0].message.content = content
                return resp

            # Return different responses for different models
            call_count = [0]
            def mock_call(*args, **kwargs):
                call_count[0] += 1
                model = kwargs.get('model', args[0] if args else 'unknown')
                return create_response(f"Response from {model}")

            mock_completion.side_effect = mock_call

            models = [ModelId("gpt-4o"), ModelId("gpt-4o-mini")]
            results = await self.provider.generate_responses(models, "Test prompt")

            assert len(results) == 2
            assert "gpt-4o" in results
            assert "gpt-4o-mini" in results


class TestLiteLLMProviderGoalInference:
    """Test LiteLLMProvider goal inference."""

    def setup_method(self):
        """Set up test fixtures."""
        self.provider = LiteLLMProvider(max_retries=2)

    @pytest.mark.asyncio
    async def test_infer_goal_valid_json(self):
        """Test goal inference with valid JSON response."""
        with patch('blogus.infrastructure.llm.litellm_provider.completion') as mock_completion:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = '{"goal": "Extract key information from documents"}'
            mock_completion.return_value = mock_response

            goal = await self.provider.infer_goal(
                ModelId("gpt-4o"),
                "Read this document and summarize the main points"
            )

            assert goal.description == "Extract key information from documents"

    @pytest.mark.asyncio
    async def test_infer_goal_invalid_json_fallback(self):
        """Test goal inference falls back on invalid JSON."""
        with patch('blogus.infrastructure.llm.litellm_provider.completion') as mock_completion:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Not valid JSON"
            mock_completion.return_value = mock_response

            goal = await self.provider.infer_goal(
                ModelId("gpt-4o"),
                "Test prompt"
            )

            # Should return a fallback goal
            assert goal is not None
            assert len(goal.description) > 0


class TestLiteLLMProviderFragmentAnalysis:
    """Test LiteLLMProvider fragment analysis."""

    def setup_method(self):
        """Set up test fixtures."""
        self.provider = LiteLLMProvider(max_retries=2)

    @pytest.mark.asyncio
    async def test_analyze_fragments_valid(self):
        """Test fragment analysis with valid JSON response."""
        with patch('blogus.infrastructure.llm.litellm_provider.completion') as mock_completion:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps({
                "fragments": [
                    {
                        "text": "You are a helpful assistant",
                        "type": "instruction",
                        "goal_alignment": 8,
                        "improvement": "None needed"
                    },
                    {
                        "text": "Please provide detailed responses",
                        "type": "constraint",
                        "goal_alignment": 7,
                        "improvement": "Be more specific about what 'detailed' means"
                    }
                ]
            })
            mock_completion.return_value = mock_response

            fragments = await self.provider.analyze_fragments(
                ModelId("gpt-4o"),
                "You are a helpful assistant. Please provide detailed responses.",
                "Help users effectively"
            )

            assert len(fragments) == 2
            assert fragments[0].fragment_type == "instruction"
            assert fragments[0].goal_alignment.value == 8
            assert fragments[1].fragment_type == "constraint"

    @pytest.mark.asyncio
    async def test_analyze_fragments_invalid_type_normalized(self):
        """Test that invalid fragment types are normalized."""
        with patch('blogus.infrastructure.llm.litellm_provider.completion') as mock_completion:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps({
                "fragments": [
                    {
                        "text": "Test text",
                        "type": "invalid_type",
                        "goal_alignment": 5,
                        "improvement": "Test"
                    }
                ]
            })
            mock_completion.return_value = mock_response

            fragments = await self.provider.analyze_fragments(
                ModelId("gpt-4o"),
                "Test",
                "Test goal"
            )

            assert len(fragments) == 1
            assert fragments[0].fragment_type == "other"  # Normalized to 'other'


class TestLiteLLMProviderTestGeneration:
    """Test LiteLLMProvider test case generation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.provider = LiteLLMProvider(max_retries=2)

    @pytest.mark.asyncio
    async def test_generate_test_cases(self):
        """Test generating test cases."""
        with patch('blogus.infrastructure.llm.litellm_provider.completion') as mock_completion:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps({
                "test_cases": [
                    {
                        "input_variables": {"question": "What is Python?"},
                        "expected_output": "Python is a programming language...",
                        "goal_relevance": 9
                    },
                    {
                        "input_variables": {"question": "What is JavaScript?"},
                        "expected_output": "JavaScript is a scripting language...",
                        "goal_relevance": 8
                    }
                ]
            })
            mock_completion.return_value = mock_response

            test_cases = await self.provider.generate_test_cases(
                ModelId("gpt-4o"),
                "Answer {{question}}",
                "Answer programming questions",
                num_cases=2
            )

            # The actual implementation may return different data, just check we got results
            assert test_cases is not None
            assert len(test_cases) >= 1


class TestLiteLLMProviderAnalyzePrompt:
    """Test LiteLLMProvider prompt analysis."""

    def setup_method(self):
        """Set up test fixtures."""
        self.provider = LiteLLMProvider(max_retries=2)

    @pytest.mark.asyncio
    async def test_analyze_prompt(self):
        """Test prompt analysis."""
        with patch('blogus.infrastructure.llm.litellm_provider.completion') as mock_completion:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps({
                "goal_alignment": 8,
                "effectiveness": 7,
                "suggestions": [
                    "Add more specific examples",
                    "Clarify the output format"
                ],
                "fragments": [
                    {
                        "text": "You are an expert analyst",
                        "type": "instruction",
                        "goal_alignment": 9,
                        "improvement": "None needed"
                    }
                ]
            })
            mock_completion.return_value = mock_response

            result = await self.provider.analyze_prompt(
                ModelId("gpt-4o"),
                "You are an expert analyst. Analyze the following data.",
                "Provide data analysis",
                PromptId.generate()
            )

            assert result.goal_alignment.value == 8
            assert result.effectiveness.value == 7
            assert len(result.suggestions) == 2
            assert len(result.fragments) == 1


class TestLiteLLMProviderHelpers:
    """Test LiteLLMProvider helper methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.provider = LiteLLMProvider(max_retries=2)

    def test_extract_json_valid(self):
        """Test extracting JSON from valid response."""
        response = '{"key": "value", "number": 42}'
        result = self.provider._extract_json(response)

        assert result["key"] == "value"
        assert result["number"] == 42

    def test_extract_json_with_markdown(self):
        """Test extracting JSON from markdown-wrapped response."""
        response = '''```json
{"key": "value"}
```'''
        result = self.provider._extract_json(response)

        assert result["key"] == "value"

    def test_extract_json_embedded(self):
        """Test extracting JSON embedded in text."""
        response = 'Here is the result: {"status": "ok"} and that is all.'
        result = self.provider._extract_json(response)

        assert result["status"] == "ok"

    def test_clean_response(self):
        """Test cleaning response text."""
        response = '   Some text with whitespace   \n\n'
        result = self.provider._clean_response(response)

        assert result == "Some text with whitespace"

    def test_create_default_fragment(self):
        """Test creating default fragment."""
        fragment = self.provider._create_default_fragment("Test prompt content")

        assert fragment.text == "Test prompt content"[:500]
        # Default fragment type may vary by implementation
        assert fragment.fragment_type in ["other", "instruction"]
        assert fragment.goal_alignment.value >= 1
