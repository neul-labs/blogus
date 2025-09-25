"""
Tests for infrastructure layer.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import AsyncMock, patch
from blogus.infrastructure.config.settings import Settings, get_settings
from blogus.infrastructure.llm.litellm_provider import LiteLLMProvider
from blogus.infrastructure.storage.file_repositories import FilePromptRepository, FileTemplateRepository
from blogus.domain.models.prompt import Prompt, PromptText, PromptGoal
from blogus.domain.models.template import Template, TemplateContent


class TestSettings:
    """Test Settings configuration."""

    def test_default_settings(self):
        """Test default settings values."""
        settings = Settings()
        assert settings.llm.default_target_model == "gpt-4"
        assert settings.llm.default_judge_model == "gpt-4"
        assert settings.storage.data_directory == "./data"
        assert settings.web.host == "0.0.0.0"
        assert settings.web.port == 8000

    def test_settings_with_env_vars(self):
        """Test settings with environment variables."""
        with patch.dict(os.environ, {
            'BLOGUS_DEFAULT_TARGET_MODEL': 'claude-3-opus-20240229',
            'BLOGUS_WEB_PORT': '8080'
        }):
            settings = Settings()
            assert settings.llm.default_target_model == "claude-3-opus-20240229"
            assert settings.web.port == 8080


class TestLiteLLMProvider:
    """Test LiteLLMProvider."""

    def setup_method(self):
        """Set up test fixtures."""
        self.provider = LiteLLMProvider(max_retries=2)

    @pytest.mark.asyncio
    async def test_generate_response(self):
        """Test generating response from LLM."""
        with patch('blogus.infrastructure.llm.litellm_provider.completion') as mock_completion:
            # Mock the response
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message.content = "Test response"
            mock_completion.return_value = mock_response

            from blogus.domain.models.prompt import PromptText
            prompt = PromptText("Test prompt")
            result = await self.provider.generate_response("gpt-4", prompt)

            assert result == "Test response"

    @pytest.mark.asyncio
    async def test_generate_response_with_retry(self):
        """Test generating response with retry on failure."""
        with patch('blogus.infrastructure.llm.litellm_provider.completion') as mock_completion:
            # First call fails, second succeeds
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message.content = "Test response"

            mock_completion.side_effect = [Exception("API Error"), mock_response]

            from blogus.domain.models.prompt import PromptText
            prompt = PromptText("Test prompt")
            result = await self.provider.generate_response("gpt-4", prompt)

            assert result == "Test response"
            assert mock_completion.call_count == 2


class TestFileRepositories:
    """Test file-based repositories."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_file_prompt_repository_save_and_get(self):
        """Test saving and retrieving prompts."""
        repo = FilePromptRepository(self.storage_path)

        prompt = Prompt(
            id="test-prompt",
            text=PromptText("Test prompt content"),
            goal=PromptGoal("Test goal")
        )

        # Save prompt
        repo.save(prompt)

        # Verify file exists
        prompt_file = self.storage_path / "prompts" / "test-prompt.json"
        assert prompt_file.exists()

        # Retrieve prompt
        retrieved = repo.get_by_id("test-prompt")
        assert retrieved is not None
        assert retrieved.id == "test-prompt"
        assert retrieved.text.content == "Test prompt content"

    def test_file_template_repository_save_and_get(self):
        """Test saving and retrieving templates."""
        repo = FileTemplateRepository(self.storage_path)

        template = Template(
            id="test-template",
            name="Test Template",
            description="A test template",
            content=TemplateContent("Hello {{name}}"),
            category="greeting",
            tags=["test"],
            author="test-author"
        )

        # Save template
        repo.save(template)

        # Verify file exists
        template_file = self.storage_path / "templates" / "test-template.json"
        assert template_file.exists()

        # Retrieve template
        retrieved = repo.get_by_id("test-template")
        assert retrieved is not None
        assert retrieved.id == "test-template"
        assert retrieved.name == "Test Template"

    def test_file_template_repository_list_by_category(self):
        """Test listing templates by category."""
        repo = FileTemplateRepository(self.storage_path)

        # Create templates in different categories
        template1 = Template(
            id="greeting-1",
            name="Greeting 1",
            description="First greeting",
            content=TemplateContent("Hello {{name}}"),
            category="greeting"
        )
        template2 = Template(
            id="greeting-2",
            name="Greeting 2",
            description="Second greeting",
            content=TemplateContent("Hi {{name}}"),
            category="greeting"
        )
        template3 = Template(
            id="farewell-1",
            name="Farewell 1",
            description="First farewell",
            content=TemplateContent("Goodbye {{name}}"),
            category="farewell"
        )

        repo.save(template1)
        repo.save(template2)
        repo.save(template3)

        # List by category
        greetings = repo.list_by_filters(category="greeting")
        farewells = repo.list_by_filters(category="farewell")

        assert len(greetings) == 2
        assert len(farewells) == 1
        assert all(t.category == "greeting" for t in greetings)
        assert all(t.category == "farewell" for t in farewells)

    def test_file_template_repository_list_by_tag(self):
        """Test listing templates by tag."""
        repo = FileTemplateRepository(self.storage_path)

        template1 = Template(
            id="template-1",
            name="Template 1",
            description="First template",
            content=TemplateContent("Content 1"),
            tags=["tag1", "common"]
        )
        template2 = Template(
            id="template-2",
            name="Template 2",
            description="Second template",
            content=TemplateContent("Content 2"),
            tags=["tag2", "common"]
        )

        repo.save(template1)
        repo.save(template2)

        # List by tag
        common_templates = repo.list_by_filters(tag="common")
        tag1_templates = repo.list_by_filters(tag="tag1")

        assert len(common_templates) == 2
        assert len(tag1_templates) == 1
        assert all("common" in t.tags for t in common_templates)