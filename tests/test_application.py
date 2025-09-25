"""
Tests for application layer.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from blogus.application.services.prompt_service import PromptService
from blogus.application.services.template_service import TemplateService
from blogus.application.dto import (
    AnalyzePromptRequest,
    ExecutePromptRequest,
    GenerateTestRequest,
    CreateTemplateRequest,
    RenderTemplateRequest
)
from blogus.domain.models.template import Template, TemplateContent
from blogus.shared.exceptions import ValidationError


class TestPromptService:
    """Test PromptService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_repository = AsyncMock()
        self.mock_llm_provider = AsyncMock()
        self.service = PromptService(self.mock_repository, self.mock_llm_provider)

    @pytest.mark.asyncio
    async def test_execute_prompt(self):
        """Test prompt execution."""
        request = ExecutePromptRequest(
            prompt_text="Test prompt",
            target_model="gpt-4"
        )

        self.mock_llm_provider.generate_response.return_value = "Test response"

        response = await self.service.execute_prompt(request)

        assert response.result == "Test response"
        assert response.model_used == "gpt-4"
        assert response.duration > 0

    @pytest.mark.asyncio
    async def test_analyze_prompt_with_goal(self):
        """Test prompt analysis with explicit goal."""
        request = AnalyzePromptRequest(
            prompt_text="Test prompt",
            judge_model="gpt-4",
            goal="Test goal"
        )

        mock_analysis = {
            "goal_alignment": 8,
            "effectiveness": 7,
            "suggestions": ["Improve clarity"],
            "status": "completed"
        }
        self.mock_llm_provider.generate_response.return_value = str(mock_analysis)

        # Mock the LLM response parsing
        self.service._parse_analysis_response = MagicMock(return_value=mock_analysis)
        self.service._parse_fragments_response = MagicMock(return_value=[])

        response = await self.service.analyze_prompt(request)

        assert response.analysis.goal_alignment == 8
        assert response.analysis.effectiveness == 7

    @pytest.mark.asyncio
    async def test_generate_test_case(self):
        """Test test case generation."""
        request = GenerateTestRequest(
            prompt_text="Test prompt",
            judge_model="gpt-4",
            goal="Test goal"
        )

        mock_test = {
            "input_variables": {"question": "What is AI?"},
            "expected_output": "AI stands for Artificial Intelligence",
            "goal_relevance": 9
        }
        self.mock_llm_provider.generate_response.return_value = str(mock_test)
        self.service._parse_test_response = MagicMock(return_value=mock_test)

        response = await self.service.generate_test_case(request)

        assert response.test_case.input_variables == {"question": "What is AI?"}
        assert response.test_case.goal_relevance == 9


class TestTemplateService:
    """Test TemplateService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_repository = AsyncMock()
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

        # Mock repository save
        saved_template = Template(
            id="test-template",
            name="Test Template",
            description="A test template",
            content=TemplateContent("Hello {{name}}"),
            category="greeting",
            tags=["test"],
            author="test-author"
        )
        self.mock_repository.save.return_value = saved_template

        response = await self.service.create_template(request)

        assert response.template.id == "test-template"
        assert response.template.name == "Test Template"
        self.mock_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_render_template(self):
        """Test template rendering."""
        request = RenderTemplateRequest(
            template_id="test-template",
            variables={"name": "World"}
        )

        # Mock repository get
        template = Template(
            id="test-template",
            name="Test Template",
            description="A test template",
            content=TemplateContent("Hello {{name}}")
        )
        self.mock_repository.get_by_id.return_value = template

        response = await self.service.render_template(request)

        assert response.rendered_content == "Hello World"

    @pytest.mark.asyncio
    async def test_list_templates_with_filters(self):
        """Test listing templates with filters."""
        # Mock repository list
        template1 = Template(
            id="template1",
            name="Template 1",
            description="First template",
            content=TemplateContent("Content 1"),
            category="test",
            tags=["tag1"]
        )
        template2 = Template(
            id="template2",
            name="Template 2",
            description="Second template",
            content=TemplateContent("Content 2"),
            category="test",
            tags=["tag2"]
        )
        self.mock_repository.list_by_filters.return_value = [template1, template2]

        templates = await self.service.list_templates(category="test", tag="tag1")

        assert len(templates) == 2
        self.mock_repository.list_by_filters.assert_called_once_with(
            category="test", tag="tag1"
        )