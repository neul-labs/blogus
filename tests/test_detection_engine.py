"""
Tests for detection engine.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from blogus.domain.services.detection_engine import (
    DetectionEngine, UnifiedDetectedPrompt, ScanResult
)


class TestUnifiedDetectedPrompt:
    """Test UnifiedDetectedPrompt dataclass."""

    def test_creation(self):
        """Test creating a detected prompt."""
        prompt = UnifiedDetectedPrompt(
            file_path=Path("/test/file.py"),
            line_number=10,
            end_line=15,
            prompt_text="You are a helpful assistant",
            detection_type="llm_call",
            language="python",
            api_type="openai",
            function_name="get_response",
            variable_name="prompt",
            linked_prompt=None,
            version_info=None,
            content_hash="abc123"
        )

        assert prompt.file_path == Path("/test/file.py")
        assert prompt.line_number == 10
        assert prompt.detection_type == "llm_call"
        assert prompt.language == "python"

    def test_is_linked_true(self):
        """Test is_linked returns True when linked."""
        prompt = UnifiedDetectedPrompt(
            file_path=Path("/test/file.py"),
            line_number=10,
            end_line=15,
            prompt_text="Test",
            detection_type="llm_call",
            language="python",
            api_type="openai",
            function_name=None,
            variable_name=None,
            linked_prompt="my-prompt",  # Linked
            version_info="abc123",
            content_hash="def456"
        )

        assert prompt.is_linked is True

    def test_is_linked_false(self):
        """Test is_linked returns False when not linked."""
        prompt = UnifiedDetectedPrompt(
            file_path=Path("/test/file.py"),
            line_number=10,
            end_line=15,
            prompt_text="Test",
            detection_type="llm_call",
            language="python",
            api_type="openai",
            function_name=None,
            variable_name=None,
            linked_prompt=None,  # Not linked
            version_info=None,
            content_hash="def456"
        )

        assert prompt.is_linked is False

    def test_is_versioned(self):
        """Test is_versioned property."""
        prompt_versioned = UnifiedDetectedPrompt(
            file_path=Path("/test/file.py"),
            line_number=10,
            end_line=15,
            prompt_text="Test",
            detection_type="llm_call",
            language="python",
            api_type="openai",
            function_name=None,
            variable_name=None,
            linked_prompt="my-prompt",
            version_info="v1-abc123",  # Has version info
            content_hash="def456"
        )

        prompt_unversioned = UnifiedDetectedPrompt(
            file_path=Path("/test/file.py"),
            line_number=10,
            end_line=15,
            prompt_text="Test",
            detection_type="llm_call",
            language="python",
            api_type="openai",
            function_name=None,
            variable_name=None,
            linked_prompt=None,
            version_info=None,  # No version info
            content_hash="def456"
        )

        assert prompt_versioned.is_versioned is True
        assert prompt_unversioned.is_versioned is False

    def test_status_managed(self):
        """Test status for managed prompt file."""
        prompt = UnifiedDetectedPrompt(
            file_path=Path("/test/prompt.prompt"),
            line_number=1,
            end_line=10,
            prompt_text="Test",
            detection_type="prompt_file",  # Managed prompt file
            language="prompt",
            api_type=None,
            function_name=None,
            variable_name=None,
            linked_prompt=None,
            version_info=None,
            content_hash="abc123"
        )

        assert prompt.status == "managed"

    def test_status_linked(self):
        """Test status for linked and versioned prompt."""
        prompt = UnifiedDetectedPrompt(
            file_path=Path("/test/file.py"),
            line_number=10,
            end_line=15,
            prompt_text="Test",
            detection_type="llm_call",
            language="python",
            api_type="openai",
            function_name=None,
            variable_name=None,
            linked_prompt="my-prompt",
            version_info="abc123",
            content_hash="def456"
        )

        assert prompt.status == "linked"

    def test_status_linked_outdated(self):
        """Test status for linked but not versioned prompt."""
        prompt = UnifiedDetectedPrompt(
            file_path=Path("/test/file.py"),
            line_number=10,
            end_line=15,
            prompt_text="Test",
            detection_type="llm_call",
            language="python",
            api_type="openai",
            function_name=None,
            variable_name=None,
            linked_prompt="my-prompt",  # Linked
            version_info=None,  # But no version
            content_hash="def456"
        )

        assert prompt.status == "linked_outdated"

    def test_status_untracked(self):
        """Test status for untracked prompt."""
        prompt = UnifiedDetectedPrompt(
            file_path=Path("/test/file.py"),
            line_number=10,
            end_line=15,
            prompt_text="Test",
            detection_type="llm_call",
            language="python",
            api_type="openai",
            function_name=None,
            variable_name=None,
            linked_prompt=None,
            version_info=None,
            content_hash="def456"
        )

        assert prompt.status == "untracked"


class TestScanResult:
    """Test ScanResult dataclass."""

    def test_creation(self):
        """Test creating a scan result."""
        result = ScanResult(
            project_path=Path("/test/project"),
            scan_time=datetime.now(),
            prompt_files=[],
            python_prompts=[],
            js_prompts=[],
            markers=[],
            errors=[]
        )

        assert result.project_path == Path("/test/project")
        assert len(result.all_prompts) == 0

    def test_all_prompts(self):
        """Test all_prompts property."""
        python_prompt = UnifiedDetectedPrompt(
            file_path=Path("/test/file.py"),
            line_number=10,
            end_line=15,
            prompt_text="Python prompt",
            detection_type="llm_call",
            language="python",
            api_type="openai",
            function_name=None,
            variable_name=None,
            linked_prompt=None,
            version_info=None,
            content_hash="abc123"
        )

        js_prompt = UnifiedDetectedPrompt(
            file_path=Path("/test/file.js"),
            line_number=20,
            end_line=25,
            prompt_text="JS prompt",
            detection_type="llm_call",
            language="javascript",
            api_type="openai",
            function_name=None,
            variable_name=None,
            linked_prompt=None,
            version_info=None,
            content_hash="def456"
        )

        result = ScanResult(
            project_path=Path("/test/project"),
            scan_time=datetime.now(),
            prompt_files=[],
            python_prompts=[python_prompt],
            js_prompts=[js_prompt],
            markers=[],
            errors=[]
        )

        assert len(result.all_prompts) == 2

    def test_untracked_prompts(self):
        """Test untracked_prompts property."""
        tracked = UnifiedDetectedPrompt(
            file_path=Path("/test/file.py"),
            line_number=10,
            end_line=15,
            prompt_text="Tracked",
            detection_type="llm_call",
            language="python",
            api_type="openai",
            function_name=None,
            variable_name=None,
            linked_prompt="my-prompt",
            version_info="v1",
            content_hash="abc123"
        )

        untracked = UnifiedDetectedPrompt(
            file_path=Path("/test/file2.py"),
            line_number=20,
            end_line=25,
            prompt_text="Untracked",
            detection_type="llm_call",
            language="python",
            api_type="openai",
            function_name=None,
            variable_name=None,
            linked_prompt=None,
            version_info=None,
            content_hash="def456"
        )

        result = ScanResult(
            project_path=Path("/test/project"),
            scan_time=datetime.now(),
            prompt_files=[],
            python_prompts=[tracked, untracked],
            js_prompts=[],
            markers=[],
            errors=[]
        )

        assert len(result.untracked_prompts) == 1
        assert result.untracked_prompts[0].prompt_text == "Untracked"

    def test_stats(self):
        """Test stats property."""
        python_prompt = UnifiedDetectedPrompt(
            file_path=Path("/test/file.py"),
            line_number=10,
            end_line=15,
            prompt_text="Python",
            detection_type="llm_call",
            language="python",
            api_type="openai",
            function_name=None,
            variable_name=None,
            linked_prompt=None,
            version_info=None,
            content_hash="abc123"
        )

        result = ScanResult(
            project_path=Path("/test/project"),
            scan_time=datetime.now(),
            prompt_files=[],
            python_prompts=[python_prompt],
            js_prompts=[],
            markers=[],
            errors=["Some error"]
        )

        stats = result.stats

        assert stats["python_detections"] == 1
        assert stats["js_detections"] == 0
        assert stats["total_detections"] == 1
        assert stats["untracked"] == 1
        assert stats["errors"] == 1

    def test_to_dict(self):
        """Test to_dict serialization."""
        result = ScanResult(
            project_path=Path("/test/project"),
            scan_time=datetime(2024, 1, 15, 10, 30, 0),
            prompt_files=[],
            python_prompts=[],
            js_prompts=[],
            markers=[],
            errors=[]
        )

        data = result.to_dict()

        assert data["project_path"] == "/test/project"
        assert "2024-01-15" in data["scan_time"]
        assert "stats" in data


class TestDetectionEngine:
    """Test DetectionEngine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test engine initialization."""
        engine = DetectionEngine(self.project_path)

        assert engine.project_path == self.project_path

    def test_scan_empty_project(self):
        """Test scanning an empty project."""
        engine = DetectionEngine(self.project_path)

        result = engine.scan()

        assert result.project_path == self.project_path
        assert len(result.all_prompts) == 0

    def test_scan_with_prompt_files(self):
        """Test scanning project with .prompt files."""
        # Create prompts directory and file
        prompts_dir = self.project_path / "prompts"
        prompts_dir.mkdir()

        prompt_file = prompts_dir / "test.prompt"
        prompt_file.write_text("""---
name: test-prompt
description: A test prompt
model:
  id: gpt-4o
---
You are a helpful assistant.
""")

        engine = DetectionEngine(self.project_path)
        result = engine.scan(include_python=False, include_js=False)

        assert len(result.prompt_files) == 1
        assert result.prompt_files[0].parsed.metadata.name == "test-prompt"

    def test_scan_excludes_node_modules(self):
        """Test that scan excludes node_modules."""
        # Create node_modules with a Python file (shouldn't happen, but test exclusion)
        node_modules = self.project_path / "node_modules"
        node_modules.mkdir()

        fake_file = node_modules / "test.py"
        fake_file.write_text("# Should be excluded")

        engine = DetectionEngine(self.project_path)
        result = engine.scan()

        # Should not scan files in node_modules
        for prompt in result.python_prompts:
            assert "node_modules" not in str(prompt.file_path)

    def test_generate_report_text(self):
        """Test generating text report."""
        engine = DetectionEngine(self.project_path)
        result = engine.scan()

        report = engine.generate_report(result, "text")

        assert isinstance(report, str)
        assert "Scan" in report or "scan" in report or "Project" in report

    def test_generate_report_json(self):
        """Test generating JSON report."""
        engine = DetectionEngine(self.project_path)
        result = engine.scan()

        report = engine.generate_report(result, "json")

        # Should be valid JSON
        import json
        data = json.loads(report)
        assert "project_path" in data or "stats" in data

    def test_generate_report_markdown(self):
        """Test generating Markdown report."""
        engine = DetectionEngine(self.project_path)
        result = engine.scan()

        report = engine.generate_report(result, "markdown")

        assert isinstance(report, str)
        assert "#" in report  # Markdown headers

    def test_validate_empty_project(self):
        """Test validating empty project."""
        engine = DetectionEngine(self.project_path)

        is_valid, issues = engine.validate()

        assert is_valid is True
        assert len(issues) == 0

    def test_validate_strict_mode(self):
        """Test validation in strict mode."""
        engine = DetectionEngine(self.project_path)

        is_valid, issues = engine.validate(strict=True)

        # Empty project should pass even in strict mode
        assert is_valid is True
