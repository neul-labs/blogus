"""
Tests for application layer.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from blogus.application.services.prompt_service import PromptService
from blogus.application.services.template_service import TemplateService
from blogus.application.dto import (
    AnalyzePromptRequest,
    ExecutePromptRequest,
    GenerateTestRequest,
    CreateTemplateRequest,
    RenderTemplateRequest
)
from blogus.domain.models.prompt import PromptId, Score, AnalysisResult, AnalysisStatus, Goal, Fragment, PromptTestCase
from blogus.domain.models.template import PromptTemplate, TemplateContent, TemplateId


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
            test_cases=[PromptTestCase(
                input_variables={"input": "test value"},
                expected_output="Expected test output",
                goal_relevance=Score(8, 10)
            )],
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

    @pytest.mark.asyncio
    async def test_analyze_prompt_with_goal(self):
        """Test prompt analysis with explicit goal."""
        request = AnalyzePromptRequest(
            prompt_text="Test prompt",
            judge_model="gpt-4o",
            goal="Test goal"
        )

        response = await self.service.analyze_prompt(request)

        assert response.analysis.goal_alignment == 8
        assert response.analysis.effectiveness == 7
        assert len(response.analysis.suggestions) > 0

    @pytest.mark.asyncio
    async def test_analyze_prompt_without_goal(self):
        """Test prompt analysis with goal inference."""
        request = AnalyzePromptRequest(
            prompt_text="Test prompt",
            judge_model="gpt-4o",
            goal=None  # No goal provided, should be inferred
        )

        response = await self.service.analyze_prompt(request)

        assert response.analysis.goal_alignment == 8
        assert response.analysis.effectiveness == 7
        # infer_goal should have been called
        self.mock_llm_provider.infer_goal.assert_called()

    @pytest.mark.asyncio
    async def test_generate_test_case(self):
        """Test test case generation."""
        request = GenerateTestRequest(
            prompt_text="Test prompt",
            judge_model="gpt-4o",
            goal="Test goal"
        )

        response = await self.service.generate_test_case(request)

        assert response.test_case.input_variables == {"input": "test value"}
        assert response.test_case.expected_output == "Expected test output"
        assert response.test_case.goal_relevance == 8

    @pytest.mark.asyncio
    async def test_analyze_prompt_returns_fragments(self):
        """Test that analysis returns fragments."""
        request = AnalyzePromptRequest(
            prompt_text="Test prompt with multiple parts",
            judge_model="gpt-4o",
            goal="Test goal"
        )

        response = await self.service.analyze_prompt(request)

        assert len(response.fragments) > 0
        assert response.fragments[0].text == "Test fragment"
        assert response.fragments[0].fragment_type == "instruction"


class TestTemplateService:
    """Test TemplateService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_repository = MagicMock()
        # Set up default return values for repository methods
        self.mock_repository.find_template.return_value = None
        self.mock_repository.find_all_templates.return_value = []
        self.service = TemplateService(self.mock_repository)

    @pytest.mark.asyncio
    async def test_create_template(self):
        """Test template creation."""
        request = CreateTemplateRequest(
            template_id="test-template",
            name="Test Template",
            description="A test template",
            content="Hello {{name}}",
            category="greeting",
            tags=["test"],
            author="test-author"
        )

        # Mock find_template to return None (template doesn't exist)
        self.mock_repository.find_template.return_value = None

        response = await self.service.create_template(request)

        assert response.template.id == "test-template"
        assert response.template.name == "Test Template"
        self.mock_repository.save_template.assert_called_once()

    @pytest.mark.asyncio
    async def test_render_template(self):
        """Test template rendering."""
        request = RenderTemplateRequest(
            template_id="test-template",
            variables={"name": "World"}
        )

        # Mock repository find_template
        template = PromptTemplate(
            id=TemplateId("test-template"),
            name="Test Template",
            description="A test template",
            content=TemplateContent("Hello {{name}}")
        )
        self.mock_repository.find_template.return_value = template

        response = await self.service.render_template(request)

        assert response.rendered_content == "Hello World"

    @pytest.mark.asyncio
    async def test_list_templates_with_filters(self):
        """Test listing templates with filters."""
        # Mock repository find_all_templates
        template1 = PromptTemplate(
            id=TemplateId("template1"),
            name="Template 1",
            description="First template",
            content=TemplateContent("Content 1"),
            category="test",
            tags={"tag1"}
        )
        template2 = PromptTemplate(
            id=TemplateId("template2"),
            name="Template 2",
            description="Second template",
            content=TemplateContent("Content 2"),
            category="test",
            tags={"tag2"}
        )
        self.mock_repository.find_all_templates.return_value = [template1, template2]

        # list_templates filters internally after calling find_all_templates
        templates = await self.service.list_templates(category="test", tag="tag1")

        # Only template1 has tag1, so only 1 template should be returned
        assert len(templates) == 1
        assert templates[0].id == "template1"
        self.mock_repository.find_all_templates.assert_called_once()
