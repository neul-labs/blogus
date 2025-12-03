"""
Git repository operations for prompt versioning.

Uses subprocess for Git operations to avoid external dependencies.
Falls back gracefully when not in a Git repository.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import subprocess
import os


class GitError(Exception):
    """Error during Git operation."""
    pass


@dataclass
class GitCommit:
    """Represents a Git commit."""
    sha: str
    short_sha: str
    message: str
    author: str
    timestamp: datetime
    files_changed: List[str]


@dataclass
class GitFileStatus:
    """Status of a file in Git."""
    path: Path
    status: str  # 'untracked', 'modified', 'staged', 'committed', 'deleted'
    is_tracked: bool


class GitRepo:
    """
    Git repository wrapper for prompt versioning.

    Provides a simple interface to Git operations needed for
    tracking prompt file history.
    """

    def __init__(self, path: Optional[Path] = None):
        """
        Initialize Git repo wrapper.

        Args:
            path: Path to repo root. If None, uses current directory.
        """
        self.path = Path(path) if path else Path.cwd()
        self._root: Optional[Path] = None

    @property
    def root(self) -> Optional[Path]:
        """Get the Git repository root, or None if not in a repo."""
        if self._root is None:
            try:
                result = self._run_git(['rev-parse', '--show-toplevel'])
                self._root = Path(result.strip())
            except GitError:
                return None
        return self._root

    @property
    def is_git_repo(self) -> bool:
        """Check if the path is inside a Git repository."""
        return self.root is not None

    def _run_git(
        self,
        args: List[str],
        cwd: Optional[Path] = None,
        check: bool = True
    ) -> str:
        """
        Run a Git command.

        Args:
            args: Git command arguments (without 'git')
            cwd: Working directory (default: self.path)
            check: Raise error on non-zero exit

        Returns:
            Command stdout

        Raises:
            GitError: If command fails and check=True
        """
        cmd = ['git'] + args
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.path,
                capture_output=True,
                text=True,
                timeout=30
            )
            if check and result.returncode != 0:
                raise GitError(f"Git command failed: {result.stderr.strip()}")
            return result.stdout
        except subprocess.TimeoutExpired:
            raise GitError("Git command timed out")
        except FileNotFoundError:
            raise GitError("Git is not installed or not in PATH")

    def init(self, path: Optional[Path] = None) -> Path:
        """
        Initialize a new Git repository.

        Args:
            path: Path to initialize (default: self.path)

        Returns:
            Path to the new repository
        """
        target = path or self.path
        target.mkdir(parents=True, exist_ok=True)
        self._run_git(['init'], cwd=target)
        self._root = target
        return target

    def get_file_status(self, file_path: Path) -> GitFileStatus:
        """
        Get the Git status of a file.

        Args:
            file_path: Path to the file

        Returns:
            GitFileStatus with status information
        """
        if not self.is_git_repo:
            return GitFileStatus(
                path=file_path,
                status='untracked',
                is_tracked=False
            )

        # Make path relative to repo root
        try:
            rel_path = file_path.resolve().relative_to(self.root)
        except ValueError:
            return GitFileStatus(
                path=file_path,
                status='untracked',
                is_tracked=False
            )

        # Check status
        try:
            status_output = self._run_git(
                ['status', '--porcelain', str(rel_path)],
                check=False
            )

            if not status_output.strip():
                # Not in status output - either tracked and clean, or doesn't exist
                if file_path.exists():
                    return GitFileStatus(
                        path=file_path,
                        status='committed',
                        is_tracked=True
                    )
                return GitFileStatus(
                    path=file_path,
                    status='deleted',
                    is_tracked=False
                )

            # Parse status output
            status_code = status_output[:2]
            if status_code == '??':
                return GitFileStatus(path=file_path, status='untracked', is_tracked=False)
            elif status_code[0] == 'A':
                return GitFileStatus(path=file_path, status='staged', is_tracked=False)
            elif status_code[0] == 'M' or status_code[1] == 'M':
                return GitFileStatus(path=file_path, status='modified', is_tracked=True)
            elif status_code[0] == 'D' or status_code[1] == 'D':
                return GitFileStatus(path=file_path, status='deleted', is_tracked=True)
            else:
                return GitFileStatus(path=file_path, status='modified', is_tracked=True)

        except GitError:
            return GitFileStatus(
                path=file_path,
                status='untracked',
                is_tracked=False
            )

    def get_file_history(
        self,
        file_path: Path,
        limit: int = 50
    ) -> List[GitCommit]:
        """
        Get commit history for a file.

        Args:
            file_path: Path to the file
            limit: Maximum number of commits to return

        Returns:
            List of GitCommit objects, newest first
        """
        if not self.is_git_repo:
            return []

        try:
            rel_path = file_path.resolve().relative_to(self.root)
        except ValueError:
            return []

        try:
            # Get commit log for file
            output = self._run_git([
                'log',
                '--format=%H|%h|%s|%an|%aI',
                f'-{limit}',
                '--follow',
                '--',
                str(rel_path)
            ], check=False)

            commits = []
            for line in output.strip().split('\n'):
                if not line:
                    continue
                parts = line.split('|')
                if len(parts) >= 5:
                    commits.append(GitCommit(
                        sha=parts[0],
                        short_sha=parts[1],
                        message=parts[2],
                        author=parts[3],
                        timestamp=datetime.fromisoformat(parts[4]),
                        files_changed=[str(rel_path)]
                    ))
            return commits

        except GitError:
            return []

    def get_commit_count(self, file_path: Path) -> int:
        """
        Get number of commits for a file.

        Args:
            file_path: Path to the file

        Returns:
            Number of commits (0 if not tracked)
        """
        if not self.is_git_repo:
            return 0

        try:
            rel_path = file_path.resolve().relative_to(self.root)
            output = self._run_git([
                'rev-list',
                '--count',
                'HEAD',
                '--',
                str(rel_path)
            ], check=False)
            return int(output.strip()) if output.strip() else 0
        except (GitError, ValueError):
            return 0

    def get_file_at_commit(self, file_path: Path, commit_sha: str) -> Optional[str]:
        """
        Get file content at a specific commit.

        Args:
            file_path: Path to the file
            commit_sha: Git commit SHA

        Returns:
            File content as string, or None if not found
        """
        if not self.is_git_repo:
            return None

        try:
            rel_path = file_path.resolve().relative_to(self.root)
            content = self._run_git([
                'show',
                f'{commit_sha}:{rel_path}'
            ])
            return content
        except GitError:
            return None

    def get_current_branch(self) -> Optional[str]:
        """Get the current branch name."""
        if not self.is_git_repo:
            return None
        try:
            return self._run_git(['branch', '--show-current']).strip()
        except GitError:
            return None

    def get_head_sha(self) -> Optional[str]:
        """Get the current HEAD commit SHA."""
        if not self.is_git_repo:
            return None
        try:
            return self._run_git(['rev-parse', 'HEAD']).strip()
        except GitError:
            return None

    def add(self, *paths: Path) -> None:
        """
        Stage files for commit.

        Args:
            paths: Files to stage
        """
        if not paths:
            return
        str_paths = [str(p) for p in paths]
        self._run_git(['add'] + str_paths)

    def commit(self, message: str, author: Optional[str] = None) -> str:
        """
        Create a commit.

        Args:
            message: Commit message
            author: Optional author string (format: "Name <email>")

        Returns:
            Commit SHA
        """
        cmd = ['commit', '-m', message]
        if author:
            cmd.extend(['--author', author])
        self._run_git(cmd)
        return self.get_head_sha() or ''

    def create_tag(
        self,
        tag_name: str,
        message: Optional[str] = None,
        commit: Optional[str] = None
    ) -> None:
        """
        Create a Git tag.

        Args:
            tag_name: Name of the tag
            message: Optional tag message (creates annotated tag)
            commit: Optional commit SHA to tag (default: HEAD)
        """
        cmd = ['tag']
        if message:
            cmd.extend(['-a', tag_name, '-m', message])
        else:
            cmd.append(tag_name)
        if commit:
            cmd.append(commit)
        self._run_git(cmd)

    def get_tags_for_file(self, file_path: Path) -> List[str]:
        """
        Get tags that include changes to a file.

        Args:
            file_path: Path to the file

        Returns:
            List of tag names
        """
        if not self.is_git_repo:
            return []

        try:
            # Get all tags
            output = self._run_git(['tag', '--list'], check=False)
            return [t.strip() for t in output.split('\n') if t.strip()]
        except GitError:
            return []

    def diff(
        self,
        file_path: Path,
        commit1: str,
        commit2: str
    ) -> str:
        """
        Get diff between two commits for a file.

        Args:
            file_path: Path to the file
            commit1: First commit SHA
            commit2: Second commit SHA

        Returns:
            Diff output as string
        """
        if not self.is_git_repo:
            return ""

        try:
            rel_path = file_path.resolve().relative_to(self.root)
            return self._run_git([
                'diff',
                commit1,
                commit2,
                '--',
                str(rel_path)
            ])
        except (GitError, ValueError):
            return ""

    def find_prompt_files(self, pattern: str = "*.prompt") -> List[Path]:
        """
        Find all .prompt files in the repository.

        Excludes common directories that shouldn't contain user prompts:
        - venv, .venv, env (virtual environments)
        - node_modules
        - __pycache__
        - .git
        - dist, build

        Args:
            pattern: Glob pattern (default: *.prompt)

        Returns:
            List of absolute paths to .prompt files
        """
        root = self.root or self.path

        # Directories to exclude from search
        exclude_dirs = {
            'venv', '.venv', 'env', '.env',
            'node_modules',
            '__pycache__', '.pytest_cache',
            '.git', '.hg', '.svn',
            'dist', 'build', '.tox',
            'site-packages',
            '.mypy_cache', '.ruff_cache'
        }

        prompt_files = []
        for path in root.rglob(pattern):
            # Check if any parent directory should be excluded
            parts = path.relative_to(root).parts
            if not any(part in exclude_dirs for part in parts):
                prompt_files.append(path)

        return prompt_files
