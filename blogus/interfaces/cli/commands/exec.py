"""
CLI commands for executing prompts.

Commands:
- exec: Execute a prompt with a single model
- compare: Execute a prompt with multiple models for comparison
- render: Render a prompt template (without execution)
"""

import click
import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from ....domain.services.prompt_parser import PromptParser, PromptParseError
from ....domain.services.version_engine import VersionEngine


@dataclass
class ExecutionResult:
    """Result of executing a prompt."""
    model: str
    response: str
    duration: float
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    error: Optional[str] = None


def get_prompts_dir() -> Path:
    """Get the prompts directory."""
    cwd = Path.cwd()
    prompts_dir = cwd / "prompts"
    return prompts_dir


def get_version_engine() -> VersionEngine:
    """Get a VersionEngine for the current directory."""
    return VersionEngine(Path.cwd())


def parse_variables(var_strings: Tuple[str, ...]) -> Dict[str, str]:
    """
    Parse variable strings into a dictionary.

    Supports:
    - key=value format
    - key:value format
    - @file.json for loading from file
    """
    variables = {}

    for var_str in var_strings:
        if var_str.startswith('@'):
            # Load from JSON file
            file_path = Path(var_str[1:])
            if not file_path.exists():
                raise click.BadParameter(f"Variables file not found: {file_path}")
            with open(file_path) as f:
                file_vars = json.load(f)
                variables.update(file_vars)
        elif '=' in var_str:
            key, value = var_str.split('=', 1)
            variables[key.strip()] = value.strip()
        elif ':' in var_str:
            key, value = var_str.split(':', 1)
            variables[key.strip()] = value.strip()
        else:
            raise click.BadParameter(f"Invalid variable format: {var_str}. Use key=value")

    return variables


async def execute_with_model(
    messages: List[Dict[str, str]],
    model: str,
    temperature: float = 0.7,
    max_tokens: int = 1000
) -> ExecutionResult:
    """
    Execute prompt with a specific model.

    Uses litellm for unified API access.
    """
    start_time = time.time()

    try:
        # Import here to avoid loading if not needed
        import litellm

        response = await litellm.acompletion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        duration = time.time() - start_time

        return ExecutionResult(
            model=model,
            response=response.choices[0].message.content,
            duration=duration,
            tokens_in=response.usage.prompt_tokens if response.usage else None,
            tokens_out=response.usage.completion_tokens if response.usage else None
        )

    except Exception as e:
        duration = time.time() - start_time
        return ExecutionResult(
            model=model,
            response="",
            duration=duration,
            error=str(e)
        )


def prepare_messages(content: str, blocks: List) -> List[Dict[str, str]]:
    """Convert parsed content/blocks to API message format."""
    if blocks:
        # Use parsed conversation blocks
        return [
            {"role": block.role, "content": block.content}
            for block in blocks
        ]
    else:
        # Simple prompt - wrap in user message
        return [{"role": "user", "content": content}]


@click.command("exec")
@click.argument("name", type=str)
@click.option(
    "--vars",
    "-v",
    multiple=True,
    help="Variables as key=value pairs or @file.json"
)
@click.option(
    "--model",
    "-m",
    type=str,
    help="Override model (default: from prompt metadata)"
)
@click.option(
    "--temperature",
    "-t",
    type=float,
    help="Override temperature"
)
@click.option(
    "--max-tokens",
    type=int,
    help="Override max tokens"
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Save response to file"
)
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    help="Output result as JSON"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Render prompt without executing"
)
def exec_prompt(
    name: str,
    vars: Tuple[str, ...],
    model: Optional[str],
    temperature: Optional[float],
    max_tokens: Optional[int],
    output: Optional[Path],
    json_output: bool,
    dry_run: bool
):
    """
    Execute a prompt with variables.

    Examples:
        blogus exec my-prompt -v user_input="Hello!"
        blogus exec my-prompt -v @variables.json
        blogus exec my-prompt -m gpt-4o-mini --dry-run
        blogus exec my-prompt -v question="What is Python?" -o response.txt
    """
    engine = get_version_engine()
    prompts_dir = get_prompts_dir()

    # Find the prompt
    vp = engine.get_prompt_by_name(name)
    if not vp:
        prompt_path = prompts_dir / f"{name}.prompt"
        if prompt_path.exists():
            vp = engine.get_versioned_prompt(prompt_path)

    if not vp:
        click.echo(f"Prompt not found: {name}", err=True)
        click.echo("Use 'blogus prompts list' to see available prompts")
        raise click.Abort()

    parsed = vp.parsed
    meta = parsed.metadata

    # Parse variables
    try:
        variables = parse_variables(vars)
    except click.BadParameter as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

    # Check required variables
    required_vars = {v.name for v in meta.variables if v.required}
    provided_vars = set(variables.keys())
    missing = required_vars - provided_vars

    if missing:
        click.echo(f"Missing required variables: {', '.join(missing)}", err=True)
        click.echo("\nRequired variables:")
        for v in meta.variables:
            if v.name in missing:
                click.echo(f"  {v.name}: {v.description}")
        raise click.Abort()

    # Render the prompt
    parser = PromptParser()
    try:
        rendered_content = parser.render(parsed.content, variables)
    except Exception as e:
        click.echo(f"Error rendering prompt: {e}", err=True)
        raise click.Abort()

    # Re-parse to get blocks with rendered content
    try:
        rendered_parsed = parser.parse_string(
            f"---\nname: {meta.name}\n---\n{rendered_content}"
        )
    except PromptParseError:
        # Fallback: use rendered content directly
        rendered_parsed = parsed

    # Prepare messages
    messages = prepare_messages(rendered_content, rendered_parsed.blocks)

    # Get model settings
    model_to_use = model or meta.model.id
    temp_to_use = temperature if temperature is not None else meta.model.temperature
    tokens_to_use = max_tokens or meta.model.max_tokens or 1000

    if dry_run:
        # Show rendered prompt without executing
        click.echo(f"\n{'=' * 60}")
        click.echo(f"  DRY RUN: {meta.name} v{vp.version.version}")
        click.echo(f"{'=' * 60}\n")

        click.echo(f"Model: {model_to_use}")
        click.echo(f"Temperature: {temp_to_use}")
        click.echo(f"Max Tokens: {tokens_to_use}")

        if variables:
            click.echo("\nVariables:")
            for k, v in variables.items():
                click.echo(f"  {k}: {v[:50]}..." if len(str(v)) > 50 else f"  {k}: {v}")

        click.echo("\nRendered Messages:")
        click.echo("-" * 40)
        for msg in messages:
            click.echo(f"\n[{msg['role'].upper()}]")
            click.echo(msg['content'])
        click.echo("-" * 40)

        # Show version marker
        marker = engine.get_marker_string(vp.parsed.file_path)
        if marker:
            click.echo(f"\nVersion marker: # {marker}")
        return

    # Execute the prompt
    async def _execute():
        if not json_output:
            click.echo(f"Executing {meta.name} with {model_to_use}...")

        result = await execute_with_model(
            messages=messages,
            model=model_to_use,
            temperature=temp_to_use,
            max_tokens=tokens_to_use
        )

        if result.error:
            click.echo(f"Error: {result.error}", err=True)
            raise click.Abort()

        if json_output:
            output_data = {
                "prompt": meta.name,
                "version": vp.version.version,
                "model": result.model,
                "response": result.response,
                "duration": result.duration,
                "tokens_in": result.tokens_in,
                "tokens_out": result.tokens_out,
                "variables": variables,
                "content_hash": vp.version.content_hash
            }
            click.echo(json.dumps(output_data, indent=2))
        else:
            click.echo(f"\n{'=' * 60}")
            click.echo(f"  Response from {result.model}")
            click.echo(f"{'=' * 60}\n")
            click.echo(result.response)
            click.echo(f"\n{'-' * 60}")
            click.echo(f"Duration: {result.duration:.2f}s")
            if result.tokens_in and result.tokens_out:
                click.echo(f"Tokens: {result.tokens_in} in, {result.tokens_out} out")

        # Save to file if requested
        if output:
            output.write_text(result.response)
            if not json_output:
                click.echo(f"\nSaved to: {output}")

    asyncio.run(_execute())


@click.command("compare")
@click.argument("name", type=str)
@click.option(
    "--vars",
    "-v",
    multiple=True,
    help="Variables as key=value pairs or @file.json"
)
@click.option(
    "--models",
    "-m",
    multiple=True,
    required=True,
    help="Models to compare (specify multiple times)"
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Save comparison to JSON file"
)
def compare_models(
    name: str,
    vars: Tuple[str, ...],
    models: Tuple[str, ...],
    output: Optional[Path]
):
    """
    Compare prompt execution across multiple models.

    Examples:
        blogus compare my-prompt -m gpt-4o -m claude-3-5-sonnet -m llama3.1-70b
        blogus compare my-prompt -v question="Explain AI" -m gpt-4o -m gpt-4o-mini
    """
    if len(models) < 2:
        click.echo("Error: Please specify at least 2 models to compare", err=True)
        raise click.Abort()

    engine = get_version_engine()
    prompts_dir = get_prompts_dir()

    # Find the prompt
    vp = engine.get_prompt_by_name(name)
    if not vp:
        prompt_path = prompts_dir / f"{name}.prompt"
        if prompt_path.exists():
            vp = engine.get_versioned_prompt(prompt_path)

    if not vp:
        click.echo(f"Prompt not found: {name}", err=True)
        raise click.Abort()

    parsed = vp.parsed
    meta = parsed.metadata

    # Parse variables
    try:
        variables = parse_variables(vars)
    except click.BadParameter as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

    # Render the prompt
    parser = PromptParser()
    try:
        rendered_content = parser.render(parsed.content, variables)
    except Exception as e:
        click.echo(f"Error rendering prompt: {e}", err=True)
        raise click.Abort()

    # Re-parse to get blocks
    try:
        rendered_parsed = parser.parse_string(
            f"---\nname: {meta.name}\n---\n{rendered_content}"
        )
    except PromptParseError:
        rendered_parsed = parsed

    # Prepare messages
    messages = prepare_messages(rendered_content, rendered_parsed.blocks)
    temp_to_use = meta.model.temperature
    tokens_to_use = meta.model.max_tokens or 1000

    async def _compare():
        click.echo(f"\nComparing {meta.name} across {len(models)} models...")
        click.echo(f"{'=' * 60}\n")

        # Execute in parallel
        tasks = [
            execute_with_model(
                messages=messages,
                model=model,
                temperature=temp_to_use,
                max_tokens=tokens_to_use
            )
            for model in models
        ]

        results = await asyncio.gather(*tasks)

        # Display results
        comparison_data = {
            "prompt": meta.name,
            "version": vp.version.version,
            "content_hash": vp.version.content_hash,
            "variables": variables,
            "results": []
        }

        for result in results:
            if result.error:
                click.echo(f"\n[{result.model}] ERROR")
                click.echo(f"  {result.error}")
            else:
                click.echo(f"\n[{result.model}] ({result.duration:.2f}s)")
                click.echo("-" * 40)
                # Truncate long responses for display
                response_preview = result.response[:500]
                if len(result.response) > 500:
                    response_preview += "..."
                click.echo(response_preview)

            comparison_data["results"].append({
                "model": result.model,
                "response": result.response,
                "duration": result.duration,
                "tokens_in": result.tokens_in,
                "tokens_out": result.tokens_out,
                "error": result.error
            })

        # Summary
        click.echo(f"\n{'=' * 60}")
        click.echo("Summary:")
        click.echo("-" * 40)

        successful = [r for r in results if not r.error]
        if successful:
            fastest = min(successful, key=lambda r: r.duration)
            slowest = max(successful, key=lambda r: r.duration)

            click.echo(f"Fastest: {fastest.model} ({fastest.duration:.2f}s)")
            click.echo(f"Slowest: {slowest.model} ({slowest.duration:.2f}s)")

            # Token comparison
            with_tokens = [r for r in successful if r.tokens_out]
            if with_tokens:
                most_tokens = max(with_tokens, key=lambda r: r.tokens_out)
                least_tokens = min(with_tokens, key=lambda r: r.tokens_out)
                click.echo(f"Most verbose: {most_tokens.model} ({most_tokens.tokens_out} tokens)")
                click.echo(f"Most concise: {least_tokens.model} ({least_tokens.tokens_out} tokens)")

        # Save comparison if requested
        if output:
            output.write_text(json.dumps(comparison_data, indent=2))
            click.echo(f"\nComparison saved to: {output}")

    asyncio.run(_compare())


@click.command("render")
@click.argument("name", type=str)
@click.option(
    "--vars",
    "-v",
    multiple=True,
    help="Variables as key=value pairs or @file.json"
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Save rendered prompt to file"
)
def render_prompt(
    name: str,
    vars: Tuple[str, ...],
    output: Optional[Path]
):
    """
    Render a prompt template with variables (without execution).

    Examples:
        blogus render my-prompt -v name="Alice"
        blogus render my-prompt -v @vars.json -o rendered.txt
    """
    engine = get_version_engine()
    prompts_dir = get_prompts_dir()

    # Find the prompt
    vp = engine.get_prompt_by_name(name)
    if not vp:
        prompt_path = prompts_dir / f"{name}.prompt"
        if prompt_path.exists():
            vp = engine.get_versioned_prompt(prompt_path)

    if not vp:
        click.echo(f"Prompt not found: {name}", err=True)
        raise click.Abort()

    parsed = vp.parsed

    # Parse variables
    try:
        variables = parse_variables(vars)
    except click.BadParameter as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

    # Render the prompt
    parser = PromptParser()
    try:
        rendered_content = parser.render(parsed.content, variables)
    except Exception as e:
        click.echo(f"Error rendering prompt: {e}", err=True)
        raise click.Abort()

    if output:
        output.write_text(rendered_content)
        click.echo(f"Rendered prompt saved to: {output}")
    else:
        click.echo(rendered_content)


# Export commands
exec_command = exec_prompt
compare_command = compare_models
render_command = render_prompt
