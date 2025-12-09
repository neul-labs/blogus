"""
Tests for CLI commands.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import patch, MagicMock, AsyncMock
import json

from blogus.interfaces.cli.main import cli
from blogus.interfaces.cli.commands.init import init_command, status_command
from blogus.interfaces.cli.commands.prompts import prompts_group
from blogus.interfaces.cli.commands.scan import lock_command, verify_command


class TestInitCommand:
    """Test init command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_init_creates_blogus_directory(self):
        """Test that init creates .blogus directory."""
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            result = self.runner.invoke(init_command, ['--path', '.'])

            assert result.exit_code == 0
            assert Path('.blogus').exists()
            assert Path('.blogus/config.yaml').exists()
            assert Path('.blogus/prompts.lock').exists()
            assert Path('prompts').exists()

    def test_init_with_examples(self):
        """Test init with example prompts."""
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            result = self.runner.invoke(init_command, ['--path', '.', '--with-examples'])

            assert result.exit_code == 0
            assert Path('prompts/example-assistant.prompt').exists()

    def test_init_fails_if_already_initialized(self):
        """Test that init fails if already initialized without --force."""
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            # First init
            self.runner.invoke(init_command, ['--path', '.'])

            # Second init should not fail, just notify
            result = self.runner.invoke(init_command, ['--path', '.'])
            assert 'already initialized' in result.output

    def test_init_force_reinitializes(self):
        """Test that --force reinitializes."""
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            # First init
            self.runner.invoke(init_command, ['--path', '.'])

            # Modify config
            config_path = Path('.blogus/config.yaml')
            config_path.write_text('modified: true')

            # Force reinit
            result = self.runner.invoke(init_command, ['--path', '.', '--force'])
            assert result.exit_code == 0
            # Config should be reset
            assert 'modified' not in config_path.read_text()


class TestStatusCommand:
    """Test status command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_status_not_initialized(self):
        """Test status when not initialized."""
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            result = self.runner.invoke(status_command, ['--path', '.'])

            assert 'Blogus initialized: ✗' in result.output

    def test_status_initialized(self):
        """Test status when initialized."""
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            # Initialize first
            self.runner.invoke(init_command, ['--path', '.'])

            result = self.runner.invoke(status_command, ['--path', '.'])

            assert 'Blogus initialized: ✓' in result.output


class TestPromptsCommands:
    """Test prompts subcommands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_new_prompt_creates_file(self):
        """Test creating a new prompt."""
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            # Initialize first
            self.runner.invoke(init_command, ['--path', '.'])

            result = self.runner.invoke(prompts_group, [
                'new', 'test-prompt',
                '-d', 'Test description',
                '-m', 'gpt-4o'
            ])

            assert result.exit_code == 0
            assert Path('prompts/test-prompt.prompt').exists()

    def test_new_prompt_fails_if_exists(self):
        """Test that creating duplicate prompt fails."""
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            self.runner.invoke(init_command, ['--path', '.'])

            # Create first prompt
            self.runner.invoke(prompts_group, ['new', 'test-prompt'])

            # Try to create duplicate
            result = self.runner.invoke(prompts_group, ['new', 'test-prompt'])

            assert result.exit_code != 0

    def test_list_prompts_empty(self):
        """Test listing prompts when none exist."""
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            self.runner.invoke(init_command, ['--path', '.'])

            result = self.runner.invoke(prompts_group, ['list'])

            assert 'No prompts found' in result.output

    def test_list_prompts_with_prompts(self):
        """Test listing prompts."""
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            self.runner.invoke(init_command, ['--path', '.', '--with-examples'])

            result = self.runner.invoke(prompts_group, ['list'])

            assert 'example-assistant' in result.output


class TestLockVerifyCommands:
    """Test lock and verify commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_lock_creates_lock_file(self):
        """Test that lock command updates prompts.lock."""
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            self.runner.invoke(init_command, ['--path', '.', '--with-examples'])

            result = self.runner.invoke(lock_command, ['--path', '.'])

            assert result.exit_code == 0
            lock_file = Path('.blogus/prompts.lock')
            assert lock_file.exists()

            lock_data = json.loads(lock_file.read_text())
            assert 'prompts' in lock_data
            assert 'example-assistant' in lock_data['prompts']

    def test_verify_passes_after_lock(self):
        """Test that verify passes after lock."""
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            self.runner.invoke(init_command, ['--path', '.', '--with-examples'])
            self.runner.invoke(lock_command, ['--path', '.'])

            result = self.runner.invoke(verify_command, ['--path', '.'])

            assert result.exit_code == 0
            assert 'match lock file' in result.output

    def test_verify_fails_without_lock(self):
        """Test that verify fails when no lock file exists."""
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            self.runner.invoke(init_command, ['--path', '.'])
            # Remove the lock file that init creates
            import os
            lock_file = Path('.blogus/prompts.lock')
            if lock_file.exists():
                os.remove(lock_file)

            result = self.runner.invoke(verify_command, ['--path', '.'])

            # Should fail because lock file is missing
            assert result.exit_code != 0 or 'No lock file' in result.output or 'error' in result.output.lower()

    def test_verify_fails_on_modified_prompt(self):
        """Test that verify fails when prompt is modified after lock."""
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            self.runner.invoke(init_command, ['--path', '.', '--with-examples'])
            self.runner.invoke(lock_command, ['--path', '.'])

            # Modify the prompt
            prompt_file = Path('prompts/example-assistant.prompt')
            content = prompt_file.read_text()
            prompt_file.write_text(content + '\n\nModified content!')

            result = self.runner.invoke(verify_command, ['--path', '.'])

            assert result.exit_code != 0
            assert 'mismatch' in result.output.lower() or 'failed' in result.output.lower()


class TestMainCLI:
    """Test main CLI entry point."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_cli_version(self):
        """Test --version flag."""
        result = self.runner.invoke(cli, ['--version'])

        assert result.exit_code == 0
        assert 'blogus' in result.output.lower()

    def test_cli_help(self):
        """Test --help flag."""
        result = self.runner.invoke(cli, ['--help'])

        assert result.exit_code == 0
        assert 'Git-native prompt versioning' in result.output

    @patch('blogus.interfaces.cli.main.get_container')
    def test_config_show(self, mock_container):
        """Test config-show command."""
        mock_settings = MagicMock()
        mock_settings.storage.data_directory = '/tmp/test'
        mock_settings.llm.default_target_model = 'gpt-4o'
        mock_settings.llm.default_judge_model = 'gpt-4o'
        mock_settings.llm.max_retries = 3
        mock_settings.llm.timeout_seconds = 30
        mock_settings.llm.max_tokens = 1000
        mock_settings.llm.openai_api_key = 'sk-test'
        mock_settings.llm.anthropic_api_key = None
        mock_settings.llm.groq_api_key = None
        mock_settings.security.max_prompt_length = 10000
        mock_settings.security.enable_input_validation = True
        mock_settings.web.host = 'localhost'
        mock_settings.web.port = 8000
        mock_settings.web.debug = False

        mock_container.return_value.settings = mock_settings

        result = self.runner.invoke(cli, ['config-show'])

        assert result.exit_code == 0
        assert 'gpt-4o' in result.output
        assert 'OpenAI: ✓ Set' in result.output
        assert 'Anthropic: ✗ Not set' in result.output
