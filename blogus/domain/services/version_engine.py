"""
Version Engine for Git-based prompt versioning.

Provides version tracking, history, comparison, and tagging
for prompts stored as .prompt files in Git repositories.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict
import difflib

from blogus.infrastructure.git.repo import GitRepo, GitCommit, GitError
from blogus.domain.services.prompt_parser import (
    PromptParser,
    ParsedPromptFile,
    PromptParseError
)


@dataclass
class PromptVersion:
    """Represents a version of a prompt."""
    version: int                      # Incremental version (commit count)
    content_hash: str                 # SHA256 hash of content
    commit_sha: Optional[str]         # Git commit SHA
    timestamp: datetime
    author: str
    message: str
    tag: Optional[str] = None         # Semantic tag (production, staging)

    @property
    def short_sha(self) -> str:
        """Get short commit SHA."""
        return self.commit_sha[:7] if self.commit_sha else ""


@dataclass
class PromptDiff:
    """Represents differences between two prompt versions."""
    prompt_name: str
    version_from: PromptVersion
    version_to: PromptVersion
    content_diff: str                 # Unified diff format
    metadata_changes: Dict[str, tuple]  # {field: (old, new)}
    lines_added: int
    lines_removed: int


@dataclass
class VersionedPrompt:
    """A prompt with version information."""
    parsed: ParsedPromptFile
    version: PromptVersion
    is_dirty: bool                    # Has uncommitted changes


class VersionEngine:
    """
    Git-native version management for prompts.

    Uses Git commits as the source of truth for versioning.
    Each commit touching a .prompt file creates a new version.
    """

    def __init__(self, repo_path: Optional[Path] = None):
        """
        Initialize Version Engine.

        Args:
            repo_path: Path to Git repository. If None, uses current directory.
        """
        self.git = GitRepo(repo_path)
        self.parser = PromptParser()
        self._prompt_dir = "prompts"  # Default directory for .prompt files

    @property
    def is_initialized(self) -> bool:
        """Check if we're in a Git repository."""
        return self.git.is_git_repo

    @property
    def prompts_path(self) -> Path:
        """Get path to prompts directory."""
        root = self.git.root or self.git.path
        return root / self._prompt_dir

    def get_version(self, prompt_path: Path) -> Optional[PromptVersion]:
        """
        Get current version info for a prompt.

        Args:
            prompt_path: Path to the .prompt file

        Returns:
            PromptVersion or None if file not found/tracked
        """
        if not prompt_path.exists():
            return None

        # Parse the current file for content hash
        try:
            parsed = self.parser.parse_file(prompt_path)
        except PromptParseError:
            return None

        # Get Git history
        commits = self.git.get_file_history(prompt_path, limit=1)
        commit_count = self.git.get_commit_count(prompt_path)

        if commits:
            commit = commits[0]
            return PromptVersion(
                version=commit_count,
                content_hash=parsed.content_hash,
                commit_sha=commit.sha,
                timestamp=commit.timestamp,
                author=commit.author,
                message=commit.message
            )
        else:
            # File exists but not committed
            return PromptVersion(
                version=0,
                content_hash=parsed.content_hash,
                commit_sha=None,
                timestamp=datetime.now(),
                author="local",
                message="Uncommitted changes"
            )

    def get_versioned_prompt(self, prompt_path: Path) -> Optional[VersionedPrompt]:
        """
        Get a prompt with full version information.

        Args:
            prompt_path: Path to the .prompt file

        Returns:
            VersionedPrompt or None if file not found
        """
        if not prompt_path.exists():
            return None

        try:
            parsed = self.parser.parse_file(prompt_path)
        except PromptParseError:
            return None

        version = self.get_version(prompt_path)
        if not version:
            return None

        # Check if file has uncommitted changes
        status = self.git.get_file_status(prompt_path)
        is_dirty = status.status in ('modified', 'untracked', 'staged')

        return VersionedPrompt(
            parsed=parsed,
            version=version,
            is_dirty=is_dirty
        )

    def get_history(
        self,
        prompt_path: Path,
        limit: int = 50
    ) -> List[PromptVersion]:
        """
        Get version history for a prompt.

        Args:
            prompt_path: Path to the .prompt file
            limit: Maximum number of versions to return

        Returns:
            List of PromptVersion, newest first
        """
        commits = self.git.get_file_history(prompt_path, limit=limit)
        versions = []

        total_commits = self.git.get_commit_count(prompt_path)

        for i, commit in enumerate(commits):
            version_num = total_commits - i  # Newest = highest number
            versions.append(PromptVersion(
                version=version_num,
                content_hash="",  # Would need to parse at each commit
                commit_sha=commit.sha,
                timestamp=commit.timestamp,
                author=commit.author,
                message=commit.message
            ))

        return versions

    def get_prompt_at_version(
        self,
        prompt_path: Path,
        version: int
    ) -> Optional[ParsedPromptFile]:
        """
        Get prompt content at a specific version.

        Args:
            prompt_path: Path to the .prompt file
            version: Version number (1-based)

        Returns:
            ParsedPromptFile or None if version not found
        """
        history = self.get_history(prompt_path)

        for v in history:
            if v.version == version:
                content = self.git.get_file_at_commit(prompt_path, v.commit_sha)
                if content:
                    return self.parser.parse_string(content)
        return None

    def diff(
        self,
        prompt_path: Path,
        version_from: int,
        version_to: int
    ) -> Optional[PromptDiff]:
        """
        Compare two versions of a prompt.

        Args:
            prompt_path: Path to the .prompt file
            version_from: First version number
            version_to: Second version number

        Returns:
            PromptDiff or None if versions not found
        """
        prompt_from = self.get_prompt_at_version(prompt_path, version_from)
        prompt_to = self.get_prompt_at_version(prompt_path, version_to)

        if not prompt_from or not prompt_to:
            return None

        # Get version info
        history = self.get_history(prompt_path)
        v_from = next((v for v in history if v.version == version_from), None)
        v_to = next((v for v in history if v.version == version_to), None)

        if not v_from or not v_to:
            return None

        # Generate unified diff
        from_lines = prompt_from.content.splitlines(keepends=True)
        to_lines = prompt_to.content.splitlines(keepends=True)

        diff_lines = list(difflib.unified_diff(
            from_lines,
            to_lines,
            fromfile=f"v{version_from}",
            tofile=f"v{version_to}"
        ))
        content_diff = ''.join(diff_lines)

        # Count changes
        lines_added = sum(1 for l in diff_lines if l.startswith('+') and not l.startswith('+++'))
        lines_removed = sum(1 for l in diff_lines if l.startswith('-') and not l.startswith('---'))

        # Compare metadata
        metadata_changes = {}
        m1 = prompt_from.metadata
        m2 = prompt_to.metadata

        if m1.name != m2.name:
            metadata_changes['name'] = (m1.name, m2.name)
        if m1.description != m2.description:
            metadata_changes['description'] = (m1.description, m2.description)
        if m1.category != m2.category:
            metadata_changes['category'] = (m1.category, m2.category)
        if m1.goal != m2.goal:
            metadata_changes['goal'] = (m1.goal, m2.goal)
        if m1.model.id != m2.model.id:
            metadata_changes['model'] = (m1.model.id, m2.model.id)

        return PromptDiff(
            prompt_name=prompt_from.metadata.name,
            version_from=v_from,
            version_to=v_to,
            content_diff=content_diff,
            metadata_changes=metadata_changes,
            lines_added=lines_added,
            lines_removed=lines_removed
        )

    def create_tag(
        self,
        prompt_path: Path,
        tag: str,
        message: Optional[str] = None
    ) -> None:
        """
        Create a tag for the current version of a prompt.

        Args:
            prompt_path: Path to the .prompt file
            tag: Tag name (e.g., 'production', 'v1.0.0')
            message: Optional tag message
        """
        # Create a prompt-specific tag
        prompt_name = prompt_path.stem
        full_tag = f"{prompt_name}/{tag}"
        self.git.create_tag(full_tag, message=message)

    def list_prompts(self) -> List[VersionedPrompt]:
        """
        List all prompts in the repository.

        Returns:
            List of VersionedPrompt for all .prompt files
        """
        prompt_files = self.git.find_prompt_files()
        prompts = []

        for path in prompt_files:
            vp = self.get_versioned_prompt(path)
            if vp:
                prompts.append(vp)

        return prompts

    def get_prompt_by_name(self, name: str) -> Optional[VersionedPrompt]:
        """
        Find a prompt by name.

        Args:
            name: Prompt name (without .prompt extension)

        Returns:
            VersionedPrompt or None if not found
        """
        # Try prompts directory first
        prompt_path = self.prompts_path / f"{name}.prompt"
        if prompt_path.exists():
            return self.get_versioned_prompt(prompt_path)

        # Search all prompt files
        for path in self.git.find_prompt_files():
            try:
                parsed = self.parser.parse_file(path)
                if parsed.metadata.name == name:
                    return self.get_versioned_prompt(path)
            except PromptParseError:
                continue

        return None

    def validate_prompt(self, prompt_path: Path) -> List[str]:
        """
        Validate a prompt file.

        Args:
            prompt_path: Path to the .prompt file

        Returns:
            List of validation issues (empty if valid)
        """
        issues = []

        if not prompt_path.exists():
            issues.append(f"File not found: {prompt_path}")
            return issues

        if prompt_path.suffix != '.prompt':
            issues.append(f"Invalid extension: expected .prompt, got {prompt_path.suffix}")

        try:
            parsed = self.parser.parse_file(prompt_path)
        except PromptParseError as e:
            issues.append(f"Parse error: {e}")
            return issues

        # Validate metadata
        if not parsed.metadata.name or parsed.metadata.name == 'untitled':
            issues.append("Missing prompt name in frontmatter")

        if not parsed.content.strip():
            issues.append("Empty prompt content")

        # Check for undefined variables
        defined_vars = {v.name for v in parsed.metadata.variables}
        used_vars = set(self.parser.extract_variables(parsed.content))
        undefined = used_vars - defined_vars

        if undefined:
            issues.append(f"Undefined variables: {', '.join(undefined)}")

        return issues

    def get_marker_string(self, prompt_path: Path) -> str:
        """
        Generate a version marker string for embedding in code.

        Format: @blogus:prompt-name@v{version} sha256:{hash}

        Args:
            prompt_path: Path to the .prompt file

        Returns:
            Marker string
        """
        version = self.get_version(prompt_path)
        if not version:
            return ""

        try:
            parsed = self.parser.parse_file(prompt_path)
            name = parsed.metadata.name
            return f"@blogus:{name}@v{version.version} sha256:{version.content_hash}"
        except PromptParseError:
            return ""
