"""
Main CLI interface for Blogus.
"""

import click
import asyncio
from pathlib import Path

from .commands.analyze import analyze
from .commands.templates import templates
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
def cli(config: Path = None, verbose: bool = False, data_dir: Path = None):
    """Blogus: A tool for crafting, analyzing, and perfecting AI prompts."""

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


# Add commands to main CLI
cli.add_command(analyze)
cli.add_command(templates)


if __name__ == "__main__":
    cli()