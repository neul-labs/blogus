"""
Tests for infrastructure layer.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, patch
from blogus.infrastructure.config.settings import Settings
from blogus.infrastructure.llm.litellm_provider import LiteLLMProvider
from blogus.infrastructure.storage.file_repositories import FilePromptRepository
from blogus.domain.models.prompt import Prompt, PromptId, Goal, ModelId


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

            result = await self.provider.generate_response(ModelId("gpt-4"), "Test prompt")

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

            result = await self.provider.generate_response(ModelId("gpt-4"), "Test prompt")

            assert result == "Test response"
            assert mock_completion.call_count == 2


class TestFilePromptRepository:
    """Test file-based prompt repository."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    @pytest.mark.asyncio
    async def test_save_and_find_prompt(self):
        """Test saving and retrieving prompts."""
        repo = FilePromptRepository(self.storage_path)

        prompt = Prompt.create(
            name="Test Prompt",
            content="Test prompt content",
            goal="Test goal"
        )

        # Save prompt
        await repo.save(prompt)

        # Verify file exists
        prompt_file = self.storage_path / "prompts" / f"{prompt.id.value}.json"
        assert prompt_file.exists()

        # Retrieve prompt
        retrieved = await repo.find_by_id(prompt.id)
        assert retrieved is not None
        assert retrieved.id.value == prompt.id.value
        assert retrieved.content == "Test prompt content"

    @pytest.mark.asyncio
    async def test_find_all_prompts(self):
        """Test listing all prompts."""
        repo = FilePromptRepository(self.storage_path)

        # Create prompts in different categories
        prompt1 = Prompt.create(
            name="Greeting 1",
            content="Hello {{name}}",
            category="greeting"
        )
        prompt2 = Prompt.create(
            name="Greeting 2",
            content="Hi {{name}}",
            category="greeting"
        )
        prompt3 = Prompt.create(
            name="Farewell 1",
            content="Goodbye {{name}}",
            category="farewell"
        )

        await repo.save(prompt1)
        await repo.save(prompt2)
        await repo.save(prompt3)

        # Find all prompts
        all_prompts = await repo.find_all()
        assert len(all_prompts) == 3

        # Filter by category
        greetings = await repo.find_all(category="greeting")
        assert len(greetings) == 2

        farewells = await repo.find_all(category="farewell")
        assert len(farewells) == 1

    @pytest.mark.asyncio
    async def test_find_prompts_with_variables(self):
        """Test filtering prompts by whether they have variables."""
        repo = FilePromptRepository(self.storage_path)

        # Create template prompt (has variables)
        template_prompt = Prompt.create(
            name="Template",
            content="Hello {{name}}"
        )

        # Create plain prompt (no variables)
        plain_prompt = Prompt.create(
            name="Plain",
            content="Hello world"
        )

        await repo.save(template_prompt)
        await repo.save(plain_prompt)

        # Filter by has_variables
        templates = await repo.find_all(has_variables=True)
        assert len(templates) == 1
        assert templates[0].name == "Template"

        plains = await repo.find_all(has_variables=False)
        assert len(plains) == 1
        assert plains[0].name == "Plain"

    @pytest.mark.asyncio
    async def test_delete_prompt(self):
        """Test deleting a prompt."""
        repo = FilePromptRepository(self.storage_path)

        prompt = Prompt.create(
            name="To Delete",
            content="Delete me"
        )

        await repo.save(prompt)

        # Verify prompt exists
        retrieved = await repo.find_by_id(prompt.id)
        assert retrieved is not None

        # Delete prompt
        deleted = await repo.delete(prompt.id)
        assert deleted is True

        # Verify prompt no longer exists
        retrieved = await repo.find_by_id(prompt.id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_search_prompts(self):
        """Test searching prompts."""
        repo = FilePromptRepository(self.storage_path)

        prompt1 = Prompt.create(
            name="Code Review",
            content="Review this code",
            category="development",
            tags={"code", "review"}
        )
        prompt2 = Prompt.create(
            name="Code Analysis",
            content="Analyze this code",
            category="development",
            tags={"code", "analysis"}
        )
        prompt3 = Prompt.create(
            name="Write Story",
            content="Write a story",
            category="creative",
            tags={"writing"}
        )

        await repo.save(prompt1)
        await repo.save(prompt2)
        await repo.save(prompt3)

        # Search by query
        results = await repo.search(query="code")
        assert len(results) == 2

        # Search by category
        results = await repo.search(category="development")
        assert len(results) == 2

        # Search by tags
        results = await repo.search(tags=["review"])
        assert len(results) == 1
        assert results[0].name == "Code Review"
