"""
Tests for domain layer.
"""

import pytest
from blogus.domain.models.prompt import Prompt, PromptText, PromptId, Goal
from blogus.domain.models.template import PromptTemplate, TemplateContent, TemplateId


class TestPromptText:
    """Test PromptText value object."""

    def test_valid_prompt_text(self):
        """Test creating valid prompt text."""
        text = PromptText("This is a valid prompt")
        assert text.content == "This is a valid prompt"

    def test_empty_prompt_text_raises_error(self):
        """Test that empty prompt text raises error."""
        with pytest.raises(ValueError):
            PromptText("")

    def test_whitespace_prompt_text_raises_error(self):
        """Test that whitespace-only prompt text raises error."""
        with pytest.raises(ValueError):
            PromptText("   ")

    def test_non_string_prompt_text_raises_error(self):
        """Test that non-string prompt text raises error."""
        with pytest.raises(ValueError):
            PromptText(123)


class TestGoal:
    """Test Goal value object."""

    def test_valid_goal(self):
        """Test creating valid goal."""
        goal = Goal("Analyze user sentiment")
        assert goal.description == "Analyze user sentiment"

    def test_empty_goal_raises_error(self):
        """Test that empty goal raises error."""
        with pytest.raises(ValueError):
            Goal("")

    def test_whitespace_goal_raises_error(self):
        """Test that whitespace-only goal raises error."""
        with pytest.raises(ValueError):
            Goal("   ")


class TestPrompt:
    """Test Prompt entity."""

    def test_create_prompt_with_goal(self):
        """Test creating prompt with goal."""
        text = PromptText("Test prompt")
        goal = Goal("Test goal")
        prompt = Prompt(PromptId("test-id"), text, goal)

        assert prompt.id.value == "test-id"
        assert prompt.text == text
        assert prompt.goal == goal

    def test_create_prompt_without_goal(self):
        """Test creating prompt without goal."""
        text = PromptText("Test prompt")
        prompt = Prompt(PromptId("test-id"), text)

        assert prompt.id.value == "test-id"
        assert prompt.text == text
        assert prompt.goal is None


class TestTemplateContent:
    """Test TemplateContent value object."""

    def test_valid_template_content(self):
        """Test creating valid template content."""
        content = TemplateContent("Hello {{name}}, how are you?")
        assert content.template == "Hello {{name}}, how are you?"

    def test_extract_variables(self):
        """Test extracting variables from template."""
        content = TemplateContent("Hello {{name}}, your age is {{age}}")
        assert content.variables == frozenset({"name", "age"})

    def test_render_template(self):
        """Test rendering template with variables."""
        content = TemplateContent("Hello {{name}}, your age is {{age}}")
        rendered = content.render({"name": "Alice", "age": "25"})
        assert rendered == "Hello Alice, your age is 25"

    def test_empty_template_raises_error(self):
        """Test that empty template raises error."""
        with pytest.raises(ValueError):
            TemplateContent("")


class TestPromptTemplate:
    """Test PromptTemplate entity."""

    def test_create_template(self):
        """Test creating template."""
        content = TemplateContent("Hello {{name}}")
        template = PromptTemplate(
            id=TemplateId("test-template"),
            name="Test Template",
            description="A test template",
            content=content,
            category="test",
            tags={"tag1", "tag2"},
            author="test-author"
        )

        assert template.id.value == "test-template"
        assert template.name == "Test Template"
        assert template.content == content
        assert template.variables == frozenset({"name"})

    def test_template_render(self):
        """Test template rendering."""
        content = TemplateContent("Hello {{name}}")
        template = PromptTemplate(
            id=TemplateId("test-template"),
            name="Test Template",
            description="A test template",
            content=content
        )

        rendered = template.render({"name": "World"})
        assert rendered == "Hello World"
