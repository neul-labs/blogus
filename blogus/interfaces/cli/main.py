"""
Main CLI interface for Blogus.

Blogus is a prompt versioning and management system that uses
Git-native versioning for tracking prompt changes.

Commands:
- init: Initialize Blogus in a project
- prompts: Manage .prompt files (new, list, show, validate, history)
- exec: Execute a prompt with a model
- compare: Compare prompt execution across models
- render: Render a prompt template
- analyze: Analyze prompts in codebase
- status: Show project status
"""

import click
import asyncio
from pathlib import Path

from .commands.analyze import analyze
from .commands.registry import registry
from .commands.init import init_command, status_command
from .commands.prompts import prompts_group
from .commands.exec import exec_command, compare_command, render_command
from .commands.scan import (
    scan_command, check_command, fix_command,
    lock_command, verify_command
)
from ..web.container import get_container
from ...shared.logging import setup_logging
from ...application.dto import ExecutePromptRequest, GenerateTestRequest


@click.group()
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file"
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging"
)
@click.option(
    "--data-dir",
    type=click.Path(path_type=Path),
    help="Data directory path"
)
@click.version_option(version="0.1.0", prog_name="blogus")
def cli(config: Path = None, verbose: bool = False, data_dir: Path = None):
    """Blogus: Git-native prompt versioning and management.

    Blogus helps you manage, version, and deploy AI prompts using
    Git as the source of truth for version control.

    Quick start:
        blogus init                    # Initialize in current directory
        blogus prompts new my-prompt   # Create a new prompt
        blogus exec my-prompt          # Execute the prompt
        blogus prompts history my-prompt  # View version history

    For more information, visit: https://blogus.dev
    """

    # Setup logging
    if verbose:
        # Override log level for verbose mode
        import os
        os.environ["BLOGUS_LOG_LEVEL"] = "DEBUG"

    setup_logging()

    # Initialize container with custom config if provided
    container = get_container()

    if config:
        from ...infrastructure.config.settings import reload_settings
        reload_settings(config)

    if data_dir:
        container.settings.storage.data_directory = str(data_dir)


@cli.command()
@click.argument("prompt", type=str)
@click.option(
    "--target-model",
    type=str,
    help="Target model to use for execution"
)
def execute(prompt: str, target_model: str = None):
    """Execute a prompt with a target LLM."""

    async def _execute():
        container = get_container()

        try:
            # Use default model if not specified
            if not target_model:
                target_model_to_use = container.settings.llm.default_target_model
            else:
                target_model_to_use = target_model

            # Create request
            request = ExecutePromptRequest(
                prompt_text=prompt,
                target_model=target_model_to_use
            )

            # Execute prompt
            click.echo(f"Executing prompt with {target_model_to_use}...")
            response = await container.get_prompt_service().execute_prompt(request)

            click.echo("\nExecution Result:")
            click.echo("=" * 50)
            click.echo(response.result)
            click.echo(f"\nModel: {response.model_used}")
            click.echo(f"Duration: {response.duration:.2f}s")

        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            raise click.Abort()

    asyncio.run(_execute())


@cli.command("test")
@click.argument("prompt", type=str)
@click.option(
    "--judge-model",
    type=str,
    help="Judge model to use for test generation"
)
@click.option("--goal", type=str, help="Goal for the test case")
def generate_test(prompt: str, judge_model: str = None, goal: str = None):
    """Generate a test case for a prompt."""

    async def _generate_test():
        container = get_container()

        try:
            # Use default model if not specified
            if not judge_model:
                judge_model_to_use = container.settings.llm.default_judge_model
            else:
                judge_model_to_use = judge_model

            # Create request
            request = GenerateTestRequest(
                prompt_text=prompt,
                judge_model=judge_model_to_use,
                goal=goal
            )

            # Generate test
            click.echo(f"Generating test case with {judge_model_to_use}...")
            response = await container.get_prompt_service().generate_test_case(request)

            click.echo("\nGenerated Test Case:")
            click.echo("=" * 50)

            test_case = response.test_case
            click.echo("Input Variables:")
            for key, value in test_case.input_variables.items():
                click.echo(f"  {key}: {value}")

            click.echo(f"\nExpected Output:")
            click.echo(test_case.expected_output)
            click.echo(f"\nGoal Relevance: {test_case.goal_relevance}/10")

        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            raise click.Abort()

    asyncio.run(_generate_test())


@cli.command()
def config_show():
    """Show current configuration."""
    container = get_container()
    settings = container.settings

    click.echo("Current Configuration:")
    click.echo("=" * 50)
    click.echo(f"Data Directory: {settings.storage.data_directory}")
    click.echo(f"Default Target Model: {settings.llm.default_target_model}")
    click.echo(f"Default Judge Model: {settings.llm.default_judge_model}")
    click.echo(f"Max Retries: {settings.llm.max_retries}")
    click.echo(f"Timeout: {settings.llm.timeout_seconds}s")
    click.echo(f"Max Tokens: {settings.llm.max_tokens}")

    # Show API key status (without exposing keys)
    click.echo("\nAPI Key Status:")
    click.echo(f"  OpenAI: {'✓ Set' if settings.llm.openai_api_key else '✗ Not set'}")
    click.echo(f"  Anthropic: {'✓ Set' if settings.llm.anthropic_api_key else '✗ Not set'}")
    click.echo(f"  Groq: {'✓ Set' if settings.llm.groq_api_key else '✗ Not set'}")

    click.echo(f"\nSecurity:")
    click.echo(f"  Max Prompt Length: {settings.security.max_prompt_length:,}")
    click.echo(f"  Input Validation: {'Enabled' if settings.security.enable_input_validation else 'Disabled'}")

    click.echo(f"\nWeb Interface:")
    click.echo(f"  Host: {settings.web.host}")
    click.echo(f"  Port: {settings.web.port}")
    click.echo(f"  Debug: {'Enabled' if settings.web.debug else 'Disabled'}")


# Add command groups to main CLI
cli.add_command(init_command)          # blogus init
cli.add_command(status_command)        # blogus status
cli.add_command(prompts_group)         # blogus prompts <subcommand>
cli.add_command(exec_command)          # blogus exec
cli.add_command(compare_command)       # blogus compare
cli.add_command(render_command)        # blogus render
cli.add_command(scan_command)          # blogus scan
cli.add_command(check_command)         # blogus check
cli.add_command(fix_command)           # blogus fix
cli.add_command(lock_command)          # blogus lock
cli.add_command(verify_command)        # blogus verify
cli.add_command(analyze)               # blogus analyze (legacy)
cli.add_command(registry)              # blogus registry (legacy)


# Create convenient aliases
@cli.command("new")
@click.argument("name", type=str)
@click.option("--description", "-d", type=str, default="", help="Prompt description")
@click.option("--model", "-m", type=str, default="gpt-4o", help="Default model")
@click.option("--category", "-c", type=str, default="general", help="Prompt category")
@click.option("--interactive", "-i", is_flag=True, help="Interactive mode")
@click.pass_context
def new_alias(ctx, name, description, model, category, interactive):
    """Alias for 'blogus prompts new' - Create a new prompt."""
    from .commands.prompts import new_prompt
    ctx.invoke(new_prompt, name=name, description=description, model=model,
               category=category, goal="", interactive=interactive)


@cli.command("list")
@click.option("--category", "-c", type=str, help="Filter by category")
@click.option("--verbose", "-v", is_flag=True, help="Show more details")
@click.pass_context
def list_alias(ctx, category, verbose):
    """Alias for 'blogus prompts list' - List all prompts."""
    from .commands.prompts import list_prompts
    ctx.invoke(list_prompts, category=category, verbose=verbose)


@cli.command("show")
@click.argument("name", type=str)
@click.option("--version", "-v", "version_num", type=int, help="Show specific version")
@click.option("--content", "-c", is_flag=True, help="Show full content")
@click.pass_context
def show_alias(ctx, name, version_num, content):
    """Alias for 'blogus prompts show' - Display prompt details."""
    from .commands.prompts import show_prompt
    ctx.invoke(show_prompt, name=name, version_num=version_num, content=content)


@cli.command("history")
@click.argument("name", type=str)
@click.option("--limit", "-n", type=int, default=20, help="Number of versions to show")
@click.pass_context
def history_alias(ctx, name, limit):
    """Alias for 'blogus prompts history' - Show version history."""
    from .commands.prompts import history_prompt
    ctx.invoke(history_prompt, name=name, limit=limit)


if __name__ == "__main__":
    cli()