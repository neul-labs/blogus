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
from blogus.domain.models.prompt import Prompt, PromptText, PromptId, Goal
from blogus.domain.models.template import PromptTemplate, TemplateContent, TemplateId


class TestSettings:
    """Test Settings configuration."""

    def test_default_settings(self):
        """Test default settings values."""
        settings = Settings.default()
        assert settings.llm.default_target_model == "gpt-4o"
        assert settings.llm.default_judge_model == "gpt-4o"
        assert settings.web.host == "localhost"
        assert settings.web.port == 8000


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

            prompt = PromptText("Test prompt")
            from blogus.domain.models.prompt import ModelId
            result = await self.provider.generate_response(ModelId("gpt-4"), prompt)

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

            prompt = PromptText("Test prompt")
            from blogus.domain.models.prompt import ModelId
            result = await self.provider.generate_response(ModelId("gpt-4"), prompt)

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
            id=PromptId("test-prompt"),
            text=PromptText("Test prompt content"),
            goal=Goal("Test goal")
        )

        # Save prompt
        repo.save(prompt)

        # Verify file exists
        prompt_file = self.storage_path / "prompts" / "test-prompt.json"
        assert prompt_file.exists()

        # Retrieve prompt
        retrieved = repo.find_by_id(PromptId("test-prompt"))
        assert retrieved is not None
        assert retrieved.id.value == "test-prompt"
        assert retrieved.text.content == "Test prompt content"

    def test_file_template_repository_save_and_get(self):
        """Test saving and retrieving templates."""
        repo = FileTemplateRepository(self.storage_path)

        template = PromptTemplate(
            id=TemplateId("test-template"),
            name="Test Template",
            description="A test template",
            content=TemplateContent("Hello {{name}}"),
            category="greeting",
            tags={"test"},
            author="test-author"
        )

        # Save template
        repo.save_template(template)

        # Verify file exists
        template_file = self.storage_path / "templates" / "test-template.json"
        assert template_file.exists()

        # Retrieve template
        retrieved = repo.find_template("test-template")
        assert retrieved is not None
        assert retrieved.id.value == "test-template"
        assert retrieved.name == "Test Template"

    def test_file_template_repository_find_all(self):
        """Test listing all templates."""
        repo = FileTemplateRepository(self.storage_path)

        # Create templates in different categories
        template1 = PromptTemplate(
            id=TemplateId("greeting-1"),
            name="Greeting 1",
            description="First greeting",
            content=TemplateContent("Hello {{name}}"),
            category="greeting"
        )
        template2 = PromptTemplate(
            id=TemplateId("greeting-2"),
            name="Greeting 2",
            description="Second greeting",
            content=TemplateContent("Hi {{name}}"),
            category="greeting"
        )
        template3 = PromptTemplate(
            id=TemplateId("farewell-1"),
            name="Farewell 1",
            description="First farewell",
            content=TemplateContent("Goodbye {{name}}"),
            category="farewell"
        )

        repo.save_template(template1)
        repo.save_template(template2)
        repo.save_template(template3)

        # Find all templates
        all_templates = repo.find_all_templates()
        assert len(all_templates) == 3

        # Filter by category manually
        greetings = [t for t in all_templates if t.category == "greeting"]
        farewells = [t for t in all_templates if t.category == "farewell"]

        assert len(greetings) == 2
        assert len(farewells) == 1
