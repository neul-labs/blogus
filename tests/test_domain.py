"""
Tests for domain layer.
"""

import pytest
from blogus.domain.models.prompt import Prompt, PromptText, PromptGoal
from blogus.domain.models.template import Template, TemplateContent, TemplateVariable
from blogus.shared.exceptions import ValidationError


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

    def test_none_prompt_text_raises_error(self):
        """Test that None prompt text raises error."""
        with pytest.raises(ValueError):
            PromptText(None)

    def test_non_string_prompt_text_raises_error(self):
        """Test that non-string prompt text raises error."""
        with pytest.raises(ValueError):
            PromptText(123)


class TestPromptGoal:
    """Test PromptGoal value object."""

    def test_valid_prompt_goal(self):
        """Test creating valid prompt goal."""
        goal = PromptGoal("Analyze user sentiment")
        assert goal.description == "Analyze user sentiment"

    def test_none_prompt_goal_is_valid(self):
        """Test that None prompt goal is valid."""
        goal = PromptGoal(None)
        assert goal.description is None


class TestPrompt:
    """Test Prompt entity."""

    def test_create_prompt_with_goal(self):
        """Test creating prompt with goal."""
        text = PromptText("Test prompt")
        goal = PromptGoal("Test goal")
        prompt = Prompt("test-id", text, goal)

        assert prompt.id == "test-id"
        assert prompt.text == text
        assert prompt.goal == goal

    def test_create_prompt_without_goal(self):
        """Test creating prompt without goal."""
        text = PromptText("Test prompt")
        prompt = Prompt("test-id", text)

        assert prompt.id == "test-id"
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
        variables = content.extract_variables()
        assert set(variables) == {"name", "age"}

    def test_render_template(self):
        """Test rendering template with variables."""
        content = TemplateContent("Hello {{name}}, your age is {{age}}")
        rendered = content.render({"name": "Alice", "age": "25"})
        assert rendered == "Hello Alice, your age is 25"


class TestTemplateVariable:
    """Test TemplateVariable value object."""

    def test_valid_template_variable(self):
        """Test creating valid template variable."""
        var = TemplateVariable("user_name")
        assert var.name == "user_name"

    def test_invalid_template_variable_raises_error(self):
        """Test that invalid variable name raises error."""
        with pytest.raises(ValueError):
            TemplateVariable("user-name")  # Hyphens not allowed

    def test_empty_template_variable_raises_error(self):
        """Test that empty variable name raises error."""
        with pytest.raises(ValueError):
            TemplateVariable("")


class TestTemplate:
    """Test Template entity."""

    def test_create_template(self):
        """Test creating template."""
        content = TemplateContent("Hello {{name}}")
        template = Template(
            id="test-template",
            name="Test Template",
            description="A test template",
            content=content,
            category="test",
            tags=["tag1", "tag2"],
            author="test-author"
        )

        assert template.id == "test-template"
        assert template.name == "Test Template"
        assert template.content == content
        assert template.get_variables() == ["name"]

    def test_template_render(self):
        """Test template rendering."""
        content = TemplateContent("Hello {{name}}")
        template = Template(
            id="test-template",
            name="Test Template",
            description="A test template",
            content=content
        )

        rendered = template.render({"name": "World"})
        assert rendered == "Hello World"