"""
Detection Engine for finding prompts in codebases.

Scans projects for:
- .prompt files
- LLM API calls in Python (OpenAI, Anthropic, LiteLLM)
- LLM API calls in JavaScript/TypeScript
- @blogus: comment markers

Provides functionality for:
- Full project scanning
- Version marker injection
- CI/CD validation
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Set, Union
import json

from blogus.infrastructure.parsers.python_parser import (
    PythonPromptParser,
    DetectedPrompt,
    scan_python_files,
)
from blogus.infrastructure.parsers.js_parser import (
    JSPromptParser,
    JSDetectedPrompt,
    scan_js_files,
)
from blogus.domain.services.prompt_parser import PromptParser, ParsedPromptFile
from blogus.domain.services.version_engine import VersionEngine, VersionedPrompt


@dataclass
class UnifiedDetectedPrompt:
    """Unified representation of a detected prompt across languages."""
    file_path: Path
    line_number: int
    end_line: int
    prompt_text: str
    detection_type: str          # 'prompt_file', 'llm_call', 'marker', 'string_variable'
    language: str                # 'python', 'javascript', 'typescript', 'prompt'
    api_type: Optional[str]      # 'openai', 'anthropic', 'litellm', etc.
    function_name: Optional[str]
    variable_name: Optional[str]
    linked_prompt: Optional[str] # Reference to .prompt file
    version_info: Optional[str]  # Embedded version hash
    content_hash: str            # Hash of the prompt content

    @property
    def is_linked(self) -> bool:
        """Check if prompt is linked to a .prompt file."""
        return bool(self.linked_prompt)

    @property
    def is_versioned(self) -> bool:
        """Check if prompt has version info."""
        return bool(self.version_info)

    @property
    def status(self) -> str:
        """Get the status of this prompt."""
        if self.detection_type == 'prompt_file':
            return 'managed'
        elif self.is_linked and self.is_versioned:
            return 'linked'
        elif self.is_linked:
            return 'linked_outdated'
        else:
            return 'untracked'


@dataclass
class ScanResult:
    """Result of scanning a project for prompts."""
    project_path: Path
    scan_time: datetime
    prompt_files: List[VersionedPrompt] = field(default_factory=list)
    python_prompts: List[UnifiedDetectedPrompt] = field(default_factory=list)
    js_prompts: List[UnifiedDetectedPrompt] = field(default_factory=list)
    markers: List[UnifiedDetectedPrompt] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def all_prompts(self) -> List[UnifiedDetectedPrompt]:
        """Get all detected prompts."""
        return self.python_prompts + self.js_prompts + self.markers

    @property
    def untracked_prompts(self) -> List[UnifiedDetectedPrompt]:
        """Get prompts without version tracking."""
        return [p for p in self.all_prompts if not p.is_versioned]

    @property
    def linked_prompts(self) -> List[UnifiedDetectedPrompt]:
        """Get prompts linked to .prompt files."""
        return [p for p in self.all_prompts if p.is_linked]

    @property
    def stats(self) -> Dict[str, int]:
        """Get scan statistics."""
        return {
            'prompt_files': len(self.prompt_files),
            'python_detections': len(self.python_prompts),
            'js_detections': len(self.js_prompts),
            'total_detections': len(self.all_prompts),
            'linked': len(self.linked_prompts),
            'untracked': len(self.untracked_prompts),
            'errors': len(self.errors)
        }

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'project_path': str(self.project_path),
            'scan_time': self.scan_time.isoformat(),
            'stats': self.stats,
            'prompt_files': [
                {
                    'name': vp.parsed.metadata.name,
                    'path': str(vp.parsed.file_path),
                    'version': vp.version.version,
                    'hash': vp.version.content_hash,
                    'is_dirty': vp.is_dirty
                }
                for vp in self.prompt_files
            ],
            'detections': [
                {
                    'file': str(p.file_path),
                    'line': p.line_number,
                    'type': p.detection_type,
                    'language': p.language,
                    'api': p.api_type,
                    'linked_to': p.linked_prompt,
                    'status': p.status,
                    'hash': p.content_hash
                }
                for p in self.all_prompts
            ],
            'errors': self.errors
        }


class DetectionEngine:
    """
    Engine for detecting prompts across a codebase.

    Scans Python and JavaScript/TypeScript files for LLM API calls,
    finds .prompt files, and tracks version markers.
    """

    def __init__(self, project_path: Optional[Path] = None):
        """
        Initialize Detection Engine.

        Args:
            project_path: Root path of the project to scan.
                         If None, uses current directory.
        """
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.version_engine = VersionEngine(self.project_path)
        self.prompt_parser = PromptParser()
        self.python_parser = PythonPromptParser()
        self.js_parser = JSPromptParser()

        # Default exclude patterns
        self.exclude_patterns = [
            '**/node_modules/**',
            '**/.venv/**',
            '**/venv/**',
            '**/__pycache__/**',
            '**/dist/**',
            '**/build/**',
            '**/.git/**',
            '**/coverage/**',
            '**/.next/**',
        ]

    def scan(
        self,
        include_python: bool = True,
        include_js: bool = True,
        include_prompt_files: bool = True
    ) -> ScanResult:
        """
        Scan the project for prompts.

        Args:
            include_python: Scan Python files
            include_js: Scan JavaScript/TypeScript files
            include_prompt_files: Include .prompt files

        Returns:
            ScanResult with all detected prompts
        """
        result = ScanResult(
            project_path=self.project_path,
            scan_time=datetime.now()
        )

        # Scan .prompt files
        if include_prompt_files:
            try:
                result.prompt_files = self.version_engine.list_prompts()
            except Exception as e:
                result.errors.append(f"Error scanning prompt files: {e}")

        # Scan Python files
        if include_python:
            try:
                python_detected = scan_python_files(
                    self.project_path,
                    self.exclude_patterns
                )
                result.python_prompts = [
                    self._convert_python_detection(d)
                    for d in python_detected
                ]
            except Exception as e:
                result.errors.append(f"Error scanning Python files: {e}")

        # Scan JavaScript/TypeScript files
        if include_js:
            try:
                js_detected = scan_js_files(
                    self.project_path,
                    self.exclude_patterns
                )
                result.js_prompts = [
                    self._convert_js_detection(d)
                    for d in js_detected
                ]
            except Exception as e:
                result.errors.append(f"Error scanning JS/TS files: {e}")

        return result

    def _convert_python_detection(self, d: DetectedPrompt) -> UnifiedDetectedPrompt:
        """Convert Python detection to unified format."""
        return UnifiedDetectedPrompt(
            file_path=d.file_path,
            line_number=d.line_number,
            end_line=d.end_line,
            prompt_text=d.prompt_text,
            detection_type=d.detection_type,
            language='python',
            api_type=d.api_type,
            function_name=d.function_name,
            variable_name=d.variable_name,
            linked_prompt=d.linked_prompt,
            version_info=d.version_info,
            content_hash=d.content_hash
        )

    def _convert_js_detection(self, d: JSDetectedPrompt) -> UnifiedDetectedPrompt:
        """Convert JS detection to unified format."""
        # Determine language from file extension
        ext = d.file_path.suffix.lower()
        language = 'typescript' if ext in ('.ts', '.tsx', '.mts') else 'javascript'

        return UnifiedDetectedPrompt(
            file_path=d.file_path,
            line_number=d.line_number,
            end_line=d.end_line,
            prompt_text=d.prompt_text,
            detection_type=d.detection_type,
            language=language,
            api_type=d.api_type,
            function_name=d.function_name,
            variable_name=d.variable_name,
            linked_prompt=d.linked_prompt,
            version_info=d.version_info,
            content_hash=d.content_hash
        )

    def add_markers(
        self,
        detections: List[UnifiedDetectedPrompt],
        prompt_name: Optional[str] = None
    ) -> List[Path]:
        """
        Add @blogus markers to detected prompts.

        Args:
            detections: List of detected prompts to mark
            prompt_name: Optional prompt name to link to

        Returns:
            List of modified file paths
        """
        modified_files: Set[Path] = set()

        for detection in detections:
            if detection.is_versioned:
                continue  # Already has marker

            # Generate marker
            if prompt_name:
                marker = f"@blogus:{prompt_name} sha256:{detection.content_hash}"
            else:
                # Use auto-generated name from function/variable
                name = (
                    detection.variable_name or
                    detection.function_name or
                    f"prompt-{detection.content_hash[:8]}"
                )
                marker = f"@blogus:{name} sha256:{detection.content_hash}"

            # Insert marker into file
            try:
                self._insert_marker(detection, marker)
                modified_files.add(detection.file_path)
            except Exception:
                continue

        return list(modified_files)

    def _insert_marker(self, detection: UnifiedDetectedPrompt, marker: str) -> None:
        """Insert a marker comment above a detection."""
        lines = detection.file_path.read_text().splitlines()

        # Determine comment style
        if detection.language == 'python':
            comment = f"# {marker}"
        else:
            comment = f"// {marker}"

        # Get indentation of the target line
        target_line = lines[detection.line_number - 1]
        indent = len(target_line) - len(target_line.lstrip())
        indented_comment = " " * indent + comment

        # Insert before the target line
        lines.insert(detection.line_number - 1, indented_comment)

        # Write back
        detection.file_path.write_text('\n'.join(lines) + '\n')

    def validate(self, strict: bool = False) -> tuple:
        """
        Validate that all prompts in the codebase are properly versioned.

        Args:
            strict: If True, fail on any untracked prompts

        Returns:
            Tuple of (is_valid, issues)
        """
        result = self.scan()
        issues = []

        # Check for untracked prompts
        if result.untracked_prompts:
            for prompt in result.untracked_prompts:
                issues.append({
                    'type': 'untracked',
                    'file': str(prompt.file_path),
                    'line': prompt.line_number,
                    'message': f"Untracked prompt at line {prompt.line_number}"
                })

        # Check for outdated markers
        for prompt in result.linked_prompts:
            if prompt.linked_prompt:
                # Find corresponding .prompt file
                vp = self.version_engine.get_prompt_by_name(prompt.linked_prompt)
                if vp:
                    # Check if hash matches
                    if prompt.version_info and prompt.version_info != vp.version.content_hash:
                        issues.append({
                            'type': 'outdated',
                            'file': str(prompt.file_path),
                            'line': prompt.line_number,
                            'message': f"Marker hash mismatch for {prompt.linked_prompt}"
                        })
                else:
                    issues.append({
                        'type': 'missing_prompt',
                        'file': str(prompt.file_path),
                        'line': prompt.line_number,
                        'message': f"Linked prompt not found: {prompt.linked_prompt}"
                    })

        # Validate .prompt files
        for vp in result.prompt_files:
            validation_issues = self.version_engine.validate_prompt(vp.parsed.file_path)
            for issue in validation_issues:
                issues.append({
                    'type': 'validation',
                    'file': str(vp.parsed.file_path),
                    'line': 1,
                    'message': issue
                })

        is_valid = len(issues) == 0 if strict else not any(
            i['type'] in ('validation', 'missing_prompt') for i in issues
        )

        return is_valid, issues

    def generate_report(self, result: ScanResult, format: str = 'text') -> str:
        """
        Generate a scan report.

        Args:
            result: Scan result to report on
            format: Output format ('text', 'json', 'markdown')

        Returns:
            Formatted report string
        """
        if format == 'json':
            return json.dumps(result.to_dict(), indent=2)

        if format == 'markdown':
            return self._generate_markdown_report(result)

        return self._generate_text_report(result)

    def _generate_text_report(self, result: ScanResult) -> str:
        """Generate a text report."""
        lines = [
            f"Blogus Scan Report",
            f"=" * 50,
            f"Project: {result.project_path}",
            f"Scan Time: {result.scan_time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"Summary:",
            f"  .prompt files: {result.stats['prompt_files']}",
            f"  Python detections: {result.stats['python_detections']}",
            f"  JS/TS detections: {result.stats['js_detections']}",
            f"  Total detections: {result.stats['total_detections']}",
            f"  Linked: {result.stats['linked']}",
            f"  Untracked: {result.stats['untracked']}",
            "",
        ]

        if result.prompt_files:
            lines.append("Prompt Files:")
            for vp in result.prompt_files:
                status = "(modified)" if vp.is_dirty else ""
                lines.append(f"  - {vp.parsed.metadata.name} v{vp.version.version} {status}")
            lines.append("")

        if result.untracked_prompts:
            lines.append("Untracked Prompts (need markers):")
            for p in result.untracked_prompts:
                rel_path = p.file_path.relative_to(result.project_path)
                lines.append(f"  - {rel_path}:{p.line_number} [{p.api_type or p.detection_type}]")
            lines.append("")

        if result.errors:
            lines.append("Errors:")
            for error in result.errors:
                lines.append(f"  - {error}")
            lines.append("")

        return '\n'.join(lines)

    def _generate_markdown_report(self, result: ScanResult) -> str:
        """Generate a Markdown report."""
        lines = [
            "# Blogus Scan Report",
            "",
            f"**Project:** `{result.project_path}`  ",
            f"**Scan Time:** {result.scan_time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            "",
            "| Metric | Count |",
            "|--------|-------|",
            f"| .prompt files | {result.stats['prompt_files']} |",
            f"| Python detections | {result.stats['python_detections']} |",
            f"| JS/TS detections | {result.stats['js_detections']} |",
            f"| Linked | {result.stats['linked']} |",
            f"| Untracked | {result.stats['untracked']} |",
            "",
        ]

        if result.prompt_files:
            lines.append("## Managed Prompts")
            lines.append("")
            lines.append("| Name | Version | Status |")
            lines.append("|------|---------|--------|")
            for vp in result.prompt_files:
                status = "Modified" if vp.is_dirty else "Clean"
                lines.append(f"| {vp.parsed.metadata.name} | v{vp.version.version} | {status} |")
            lines.append("")

        if result.untracked_prompts:
            lines.append("## Untracked Prompts")
            lines.append("")
            lines.append("These prompts need `@blogus:` markers:")
            lines.append("")
            for p in result.untracked_prompts:
                rel_path = p.file_path.relative_to(result.project_path)
                lines.append(f"- `{rel_path}:{p.line_number}` ({p.api_type or p.detection_type})")
            lines.append("")

        return '\n'.join(lines)
