"""
Tests for domain layer.
"""

import pytest
from blogus.domain.models.prompt import Prompt, PromptId, Goal, Score


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


class TestPromptId:
    """Test PromptId value object."""

    def test_valid_prompt_id(self):
        """Test creating valid prompt ID."""
        prompt_id = PromptId("test-id")
        assert prompt_id.value == "test-id"

    def test_empty_prompt_id_raises_error(self):
        """Test that empty prompt ID raises error."""
        with pytest.raises(ValueError):
            PromptId("")

    def test_generate_prompt_id(self):
        """Test generating unique prompt IDs."""
        id1 = PromptId.generate()
        id2 = PromptId.generate()
        assert id1.value != id2.value


class TestScore:
    """Test Score value object."""

    def test_valid_score(self):
        """Test creating valid score."""
        score = Score(8, 10)
        assert score.value == 8
        assert score.max_value == 10

    def test_score_percentage(self):
        """Test score percentage calculation."""
        score = Score(8, 10)
        assert score.percentage == 80.0

    def test_score_out_of_range_raises_error(self):
        """Test that out of range score raises error."""
        with pytest.raises(ValueError):
            Score(11, 10)

    def test_negative_score_raises_error(self):
        """Test that negative score raises error."""
        with pytest.raises(ValueError):
            Score(-1, 10)


class TestPrompt:
    """Test Prompt entity."""

    def test_create_prompt(self):
        """Test creating prompt."""
        prompt = Prompt.create(
            name="Test Prompt",
            content="This is a test prompt",
            goal="Test goal"
        )

        assert prompt.name == "Test Prompt"
        assert prompt.content == "This is a test prompt"
        assert prompt.goal == "Test goal"
        assert prompt.id is not None

    def test_create_prompt_with_variables(self):
        """Test creating prompt with template variables."""
        prompt = Prompt.create(
            name="Template Prompt",
            content="Hello {{name}}, how are you?",
            goal="Greeting"
        )

        assert prompt.is_template is True
        assert "name" in prompt.variables

    def test_create_prompt_without_variables(self):
        """Test creating prompt without template variables."""
        prompt = Prompt.create(
            name="Plain Prompt",
            content="This is a plain prompt",
        )

        assert prompt.is_template is False
        assert len(prompt.variables) == 0

    def test_prompt_render(self):
        """Test template rendering."""
        prompt = Prompt.create(
            name="Template",
            content="Hello {{name}}, your age is {{age}}"
        )

        rendered = prompt.render({"name": "Alice", "age": "25"})
        assert rendered == "Hello Alice, your age is 25"

    def test_prompt_render_missing_variables_raises_error(self):
        """Test that rendering with missing variables raises error."""
        prompt = Prompt.create(
            name="Template",
            content="Hello {{name}}, your age is {{age}}"
        )

        with pytest.raises(ValueError):
            prompt.render({"name": "Alice"})  # Missing 'age'

    def test_empty_content_raises_error(self):
        """Test that empty content raises error."""
        with pytest.raises(ValueError):
            Prompt.create(
                name="Test",
                content=""
            )

    def test_empty_name_raises_error(self):
        """Test that empty name raises error."""
        with pytest.raises(ValueError):
            Prompt.create(
                name="",
                content="Some content"
            )

    def test_prompt_update_content(self):
        """Test updating prompt content."""
        prompt = Prompt.create(
            name="Test",
            content="Original content"
        )
        original_version = prompt.version

        prompt.update_content("New content")

        assert prompt.content == "New content"
        assert prompt.version == original_version + 1

    def test_prompt_validate(self):
        """Test prompt validation."""
        prompt = Prompt.create(
            name="Test",
            content="Hello {{name}"  # Mismatched braces
        )

        issues = prompt.validate()
        assert len(issues) > 0
        assert any("brace" in issue.lower() for issue in issues)

    def test_extract_multiple_variables(self):
        """Test extracting multiple variables from template."""
        prompt = Prompt.create(
            name="Multi-var",
            content="{{greeting}} {{name}}, your code is {{code}}. {{greeting}} again!"
        )

        # Should have unique variables in order
        assert prompt.variables == ["greeting", "name", "code"]
