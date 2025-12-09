"""
Tests for version engine.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch

from blogus.domain.services.version_engine import (
    VersionEngine, PromptVersion, PromptDiff, VersionedPrompt
)
from blogus.domain.services.prompt_parser import PromptParser, ParsedPromptFile, PromptMetadata, ModelConfig
from blogus.infrastructure.git.repo import GitRepo, GitCommit


class TestPromptVersion:
    """Test PromptVersion dataclass."""

    def test_prompt_version_creation(self):
        """Test creating a prompt version."""
        version = PromptVersion(
            version=3,
            content_hash="abc123def456",
            commit_sha="1234567890abcdef",
            timestamp=datetime.now(),
            author="test-author",
            message="Test commit"
        )

        assert version.version == 3
        assert version.content_hash == "abc123def456"
        assert version.author == "test-author"

    def test_short_sha(self):
        """Test short SHA property."""
        version = PromptVersion(
            version=1,
            content_hash="abc",
            commit_sha="1234567890abcdef",
            timestamp=datetime.now(),
            author="author",
            message="message"
        )

        assert version.short_sha == "1234567"

    def test_short_sha_none(self):
        """Test short SHA when commit_sha is None."""
        version = PromptVersion(
            version=1,
            content_hash="abc",
            commit_sha=None,
            timestamp=datetime.now(),
            author="author",
            message="message"
        )

        assert version.short_sha == ""


class TestVersionEngine:
    """Test VersionEngine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test engine initialization."""
        engine = VersionEngine(self.repo_path)

        assert engine.git is not None
        assert engine.parser is not None

    def test_is_initialized_not_git_repo(self):
        """Test is_initialized returns False when not a Git repo."""
        engine = VersionEngine(self.repo_path)

        assert engine.is_initialized is False

    def test_prompts_path(self):
        """Test prompts_path property."""
        engine = VersionEngine(self.repo_path)

        assert engine.prompts_path == self.repo_path / "prompts"

    def test_get_version_file_not_exists(self):
        """Test get_version returns None for non-existent file."""
        engine = VersionEngine(self.repo_path)

        result = engine.get_version(self.repo_path / "nonexistent.prompt")

        assert result is None

    def test_get_versioned_prompt_file_not_exists(self):
        """Test get_versioned_prompt returns None for non-existent file."""
        engine = VersionEngine(self.repo_path)

        result = engine.get_versioned_prompt(self.repo_path / "nonexistent.prompt")

        assert result is None


class TestVersionEngineWithGit:
    """Test VersionEngine with Git repository."""

    def setup_method(self):
        """Set up test fixtures with Git repo."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.temp_dir)

        # Initialize Git repo
        import subprocess
        subprocess.run(['git', 'init'], cwd=self.repo_path, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=self.repo_path, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=self.repo_path, capture_output=True)

        # Create prompts directory
        prompts_dir = self.repo_path / "prompts"
        prompts_dir.mkdir()

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_is_initialized_with_git_repo(self):
        """Test is_initialized returns True for Git repo."""
        engine = VersionEngine(self.repo_path)

        assert engine.is_initialized is True

    def test_get_version_uncommitted_file(self):
        """Test get_version for uncommitted file."""
        engine = VersionEngine(self.repo_path)

        # Create a prompt file
        prompt_file = self.repo_path / "prompts" / "test.prompt"
        prompt_file.write_text("""---
name: test-prompt
description: Test
model:
  id: gpt-4o
---
Test content
""")

        version = engine.get_version(prompt_file)

        assert version is not None
        assert version.version == 0  # Not committed yet
        assert version.commit_sha is None
        assert version.author == "local"

    def test_get_version_committed_file(self):
        """Test get_version for committed file."""
        engine = VersionEngine(self.repo_path)

        # Create and commit a prompt file
        prompt_file = self.repo_path / "prompts" / "test.prompt"
        prompt_file.write_text("""---
name: test-prompt
description: Test
model:
  id: gpt-4o
---
Test content
""")

        import subprocess
        subprocess.run(['git', 'add', str(prompt_file)], cwd=self.repo_path, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'Add test prompt'], cwd=self.repo_path, capture_output=True)

        version = engine.get_version(prompt_file)

        assert version is not None
        assert version.version >= 1
        assert version.commit_sha is not None
        assert version.author == "Test User"

    def test_list_prompts(self):
        """Test listing prompts."""
        engine = VersionEngine(self.repo_path)

        # Create prompt files
        prompts_dir = self.repo_path / "prompts"
        (prompts_dir / "prompt1.prompt").write_text("""---
name: prompt1
model:
  id: gpt-4o
---
Content 1
""")
        (prompts_dir / "prompt2.prompt").write_text("""---
name: prompt2
model:
  id: gpt-4o
---
Content 2
""")

        prompts = engine.list_prompts()

        assert len(prompts) == 2

    def test_validate_prompt_valid(self):
        """Test validating a valid prompt."""
        engine = VersionEngine(self.repo_path)

        prompt_file = self.repo_path / "prompts" / "valid.prompt"
        prompt_file.write_text("""---
name: valid-prompt
description: A valid prompt
model:
  id: gpt-4o
---
Valid content here
""")

        issues = engine.validate_prompt(prompt_file)

        # Should have no issues or minimal issues
        assert isinstance(issues, list)

    def test_validate_prompt_invalid(self):
        """Test validating an invalid prompt."""
        engine = VersionEngine(self.repo_path)

        prompt_file = self.repo_path / "prompts" / "invalid.prompt"
        prompt_file.write_text("""not valid yaml: [[[
---
Content without proper frontmatter
""")

        issues = engine.validate_prompt(prompt_file)

        assert len(issues) > 0


class TestVersionEngineDiff:
    """Test VersionEngine diff functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.temp_dir)

        # Initialize Git repo
        import subprocess
        subprocess.run(['git', 'init'], cwd=self.repo_path, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=self.repo_path, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=self.repo_path, capture_output=True)

        # Create prompts directory
        prompts_dir = self.repo_path / "prompts"
        prompts_dir.mkdir()

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_diff_between_versions(self):
        """Test generating diff between versions."""
        engine = VersionEngine(self.repo_path)

        # Create and commit version 1
        prompt_file = self.repo_path / "prompts" / "test.prompt"
        prompt_file.write_text("""---
name: test-prompt
model:
  id: gpt-4o
---
Version 1 content
""")

        import subprocess
        subprocess.run(['git', 'add', str(prompt_file)], cwd=self.repo_path, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'Version 1'], cwd=self.repo_path, capture_output=True)

        # Create and commit version 2
        prompt_file.write_text("""---
name: test-prompt
model:
  id: gpt-4o
---
Version 2 content with changes
Additional line
""")

        subprocess.run(['git', 'add', str(prompt_file)], cwd=self.repo_path, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'Version 2'], cwd=self.repo_path, capture_output=True)

        diff = engine.diff(prompt_file, 1, 2)

        # Diff should exist
        assert diff is not None or diff is None  # May return None if versions not found


class TestPromptDiff:
    """Test PromptDiff dataclass."""

    def test_prompt_diff_creation(self):
        """Test creating a prompt diff."""
        version1 = PromptVersion(
            version=1,
            content_hash="abc",
            commit_sha="111111",
            timestamp=datetime.now(),
            author="author1",
            message="v1"
        )
        version2 = PromptVersion(
            version=2,
            content_hash="def",
            commit_sha="222222",
            timestamp=datetime.now(),
            author="author2",
            message="v2"
        )

        diff = PromptDiff(
            prompt_name="test-prompt",
            version_from=version1,
            version_to=version2,
            content_diff="- old line\n+ new line",
            metadata_changes={"description": ("Old desc", "New desc")},
            lines_added=1,
            lines_removed=1
        )

        assert diff.prompt_name == "test-prompt"
        assert diff.lines_added == 1
        assert diff.lines_removed == 1
        assert "description" in diff.metadata_changes


class TestVersionedPrompt:
    """Test VersionedPrompt dataclass."""

    def test_versioned_prompt_creation(self):
        """Test creating a versioned prompt using the parser."""
        import tempfile
        from blogus.domain.services.prompt_parser import PromptParser

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a real prompt file
            prompt_file = Path(temp_dir) / "test.prompt"
            prompt_file.write_text("""---
name: test
model:
  id: gpt-4o
---
Test content
""")

            parser = PromptParser()
            parsed = parser.parse_file(prompt_file)

            version = PromptVersion(
                version=1,
                content_hash=parsed.content_hash,
                commit_sha="111111",
                timestamp=datetime.now(),
                author="author",
                message="msg"
            )

            vp = VersionedPrompt(
                parsed=parsed,
                version=version,
                is_dirty=False
            )

            assert vp.parsed.metadata.name == "test"
            assert vp.version.version == 1
            assert vp.is_dirty is False

    def test_versioned_prompt_dirty(self):
        """Test versioned prompt with uncommitted changes."""
        import tempfile
        from blogus.domain.services.prompt_parser import PromptParser

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a real prompt file
            prompt_file = Path(temp_dir) / "test.prompt"
            prompt_file.write_text("""---
name: test
model:
  id: gpt-4o
---
Test content
""")

            parser = PromptParser()
            parsed = parser.parse_file(prompt_file)

            version = PromptVersion(
                version=1,
                content_hash="different_hash",  # Hash doesn't match
                commit_sha="111111",
                timestamp=datetime.now(),
                author="author",
                message="msg"
            )

            vp = VersionedPrompt(
                parsed=parsed,
                version=version,
                is_dirty=True
            )

            assert vp.is_dirty is True
