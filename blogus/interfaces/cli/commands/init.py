"""
CLI commands for initializing Blogus in a project.
"""

import click
from pathlib import Path
import yaml

from ....infrastructure.git.repo import GitRepo
from ....domain.services.prompt_parser import PromptParser, PromptMetadata, ModelConfig


EXAMPLE_PROMPT = """---
name: example-assistant
description: A helpful assistant that answers questions
author: blogus
category: general
tags: [example, assistant]
model:
  id: gpt-4o
  temperature: 0.7
  max_tokens: 1000
goal: |
  Provide helpful, accurate, and friendly responses to user questions.
variables:
  - name: user_question
    description: The user's question to answer
    required: true
---

<system>
You are a helpful assistant. Answer questions clearly and concisely.
Be friendly and informative.
</system>

<user>
{{user_question}}
</user>
"""

CONFIG_TEMPLATE = """# Blogus Configuration
# See https://blogus.dev/docs/configuration for more options

# Default model settings
model:
  default: gpt-4o
  judge: gpt-4o

# Prompt settings
prompts:
  directory: prompts
  # Patterns to ignore when scanning
  ignore:
    - "**/node_modules/**"
    - "**/.venv/**"
    - "**/dist/**"

# Detection settings (for scanning codebases)
detection:
  # Patterns for detecting prompts in code
  patterns:
    python:
      - "openai.chat.completions.create"
      - "anthropic.messages.create"
      - "litellm.completion"
    javascript:
      - "openai.chat.completions.create"
      - "new Anthropic().messages.create"

# CI/CD settings
ci:
  # Fail if unversioned prompts are found
  strict: false
"""


@click.group()
def init_group():
    """Initialize and configure Blogus."""
    pass


@click.command("init")
@click.option(
    "--with-examples",
    is_flag=True,
    help="Include example prompt files"
)
@click.option(
    "--path",
    type=click.Path(path_type=Path),
    default=".",
    help="Path to initialize (default: current directory)"
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing configuration"
)
def init(with_examples: bool, path: Path, force: bool):
    """
    Initialize Blogus in a project.

    Creates:
    - .blogus/ directory with configuration
    - prompts/ directory for .prompt files
    - Example prompts (if --with-examples)
    """
    project_path = Path(path).resolve()

    if not project_path.exists():
        click.echo(f"Error: Path does not exist: {project_path}", err=True)
        raise click.Abort()

    blogus_dir = project_path / ".blogus"
    prompts_dir = project_path / "prompts"
    config_file = blogus_dir / "config.yaml"
    lock_file = blogus_dir / "prompts.lock"

    # Check if already initialized
    if blogus_dir.exists() and not force:
        click.echo(f"Blogus is already initialized in {project_path}")
        click.echo("Use --force to reinitialize")
        return

    # Check if we're in a Git repo
    git = GitRepo(project_path)
    if not git.is_git_repo:
        click.echo("Warning: Not in a Git repository. Version history will be limited.")
        click.echo("Run 'git init' first for full versioning support.\n")

    # Create directories
    click.echo(f"Initializing Blogus in {project_path}...")

    blogus_dir.mkdir(exist_ok=True)
    prompts_dir.mkdir(exist_ok=True)

    # Create config file
    config_file.write_text(CONFIG_TEMPLATE)
    click.echo(f"  Created: {config_file.relative_to(project_path)}")

    # Create empty lock file
    lock_file.write_text("{}")
    click.echo(f"  Created: {lock_file.relative_to(project_path)}")

    # Create .gitignore for .blogus (keep config, ignore cache)
    gitignore = blogus_dir / ".gitignore"
    gitignore.write_text("# Ignore cache but keep config\ncache/\n*.log\n")
    click.echo(f"  Created: {gitignore.relative_to(project_path)}")

    # Add example prompt
    if with_examples:
        example_file = prompts_dir / "example-assistant.prompt"
        example_file.write_text(EXAMPLE_PROMPT)
        click.echo(f"  Created: {example_file.relative_to(project_path)}")

    click.echo("\nBlogus initialized successfully!")
    click.echo("\nNext steps:")
    click.echo("  1. Create prompts:    blogus new my-prompt")
    click.echo("  2. List prompts:      blogus list")
    click.echo("  3. Execute a prompt:  blogus exec my-prompt --vars key=value")
    click.echo("  4. View history:      blogus history my-prompt")

    if with_examples:
        click.echo(f"\nTry the example: blogus exec example-assistant --vars user_question='What is Python?'")


@click.command("status")
@click.option(
    "--path",
    type=click.Path(path_type=Path),
    default=".",
    help="Path to check (default: current directory)"
)
def status(path: Path):
    """
    Show Blogus initialization status.
    """
    project_path = Path(path).resolve()
    blogus_dir = project_path / ".blogus"
    prompts_dir = project_path / "prompts"

    click.echo(f"Project: {project_path}\n")

    # Check Git status
    git = GitRepo(project_path)
    if git.is_git_repo:
        click.echo(f"Git repository: ✓ (root: {git.root})")
        branch = git.get_current_branch()
        if branch:
            click.echo(f"Current branch: {branch}")
    else:
        click.echo("Git repository: ✗ (not a Git repo)")

    click.echo()

    # Check Blogus status
    if blogus_dir.exists():
        click.echo("Blogus initialized: ✓")
        config_file = blogus_dir / "config.yaml"
        if config_file.exists():
            click.echo(f"  Config: {config_file.relative_to(project_path)}")
    else:
        click.echo("Blogus initialized: ✗")
        click.echo("  Run 'blogus init' to initialize")
        return

    # Count prompts
    if prompts_dir.exists():
        prompt_files = list(prompts_dir.glob("*.prompt"))
        click.echo(f"  Prompts: {len(prompt_files)} files in {prompts_dir.relative_to(project_path)}/")

        if prompt_files:
            click.echo("\n  Prompt files:")
            for pf in prompt_files[:10]:  # Show first 10
                click.echo(f"    - {pf.name}")
            if len(prompt_files) > 10:
                click.echo(f"    ... and {len(prompt_files) - 10} more")
    else:
        click.echo("  Prompts: No prompts directory found")


# Export commands
init_command = init
status_command = status
