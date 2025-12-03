"""
CLI commands for prompt management.

Commands:
- new: Create a new .prompt file
- list: List all prompts
- show: Display prompt details
- validate: Validate prompt files
- history: Show version history
"""

import click
from pathlib import Path
from datetime import datetime

from ....domain.services.prompt_parser import (
    PromptParser,
    PromptMetadata,
    ModelConfig,
    PromptVariable,
    PromptParseError
)
from ....domain.services.version_engine import VersionEngine


def get_prompts_dir() -> Path:
    """Get the prompts directory, creating if needed."""
    cwd = Path.cwd()
    prompts_dir = cwd / "prompts"
    if not prompts_dir.exists():
        prompts_dir.mkdir(parents=True)
    return prompts_dir


def get_version_engine() -> VersionEngine:
    """Get a VersionEngine for the current directory."""
    return VersionEngine(Path.cwd())


@click.group("prompts")
def prompts():
    """Manage .prompt files."""
    pass


@prompts.command("new")
@click.argument("name", type=str)
@click.option(
    "--description",
    "-d",
    type=str,
    default="",
    help="Prompt description"
)
@click.option(
    "--model",
    "-m",
    type=str,
    default="gpt-4o",
    help="Default model (e.g., gpt-4o, claude-3-5-sonnet)"
)
@click.option(
    "--category",
    "-c",
    type=str,
    default="general",
    help="Prompt category"
)
@click.option(
    "--goal",
    "-g",
    type=str,
    default="",
    help="Goal/purpose of the prompt"
)
@click.option(
    "--interactive",
    "-i",
    is_flag=True,
    help="Interactive mode - prompt for content"
)
def new_prompt(
    name: str,
    description: str,
    model: str,
    category: str,
    goal: str,
    interactive: bool
):
    """
    Create a new .prompt file.

    Examples:
        blogus prompts new my-assistant
        blogus prompts new customer-support -d "Support agent" -m gpt-4o
        blogus prompts new code-reviewer -i  # Interactive mode
    """
    prompts_dir = get_prompts_dir()
    prompt_file = prompts_dir / f"{name}.prompt"

    if prompt_file.exists():
        click.echo(f"Error: Prompt '{name}' already exists at {prompt_file}", err=True)
        raise click.Abort()

    # Normalize name
    name_normalized = name.lower().replace(" ", "-").replace("_", "-")

    if interactive:
        click.echo(f"Creating new prompt: {name_normalized}\n")

        if not description:
            description = click.prompt("Description", default=f"Prompt: {name_normalized}")

        if not goal:
            goal = click.prompt("Goal (what should this prompt achieve?)", default="")

        click.echo("\nEnter prompt content (press Ctrl+D or Ctrl+Z when done):")
        click.echo("Tip: Use <system>, <user>, <assistant> tags for multi-turn prompts")
        click.echo("     Use {{variable_name}} for template variables\n")

        try:
            content_lines = []
            while True:
                try:
                    line = input()
                    content_lines.append(line)
                except EOFError:
                    break
            content = "\n".join(content_lines)
        except KeyboardInterrupt:
            click.echo("\nAborted.")
            raise click.Abort()

        if not content.strip():
            content = "<system>\nYou are a helpful assistant.\n</system>\n\n<user>\n{{user_input}}\n</user>"
    else:
        content = "<system>\nYou are a helpful assistant.\n</system>\n\n<user>\n{{user_input}}\n</user>"

    # Extract variables from content
    parser = PromptParser()
    variables = parser.extract_variables(content)
    var_definitions = [
        PromptVariable(name=v, description=f"Variable: {v}")
        for v in variables
    ]

    # Create metadata
    metadata = PromptMetadata(
        name=name_normalized,
        description=description or f"Prompt: {name_normalized}",
        author="cli",
        category=category,
        tags=[],
        model=ModelConfig(id=model),
        goal=goal or None,
        variables=var_definitions
    )

    # Write file
    parser.write_file(prompt_file, metadata, content)

    click.echo(f"\nCreated: {prompt_file}")
    click.echo(f"Variables: {', '.join(variables) if variables else 'none'}")
    click.echo(f"\nNext: blogus exec {name_normalized} --vars ...")


@prompts.command("list")
@click.option(
    "--category",
    "-c",
    type=str,
    help="Filter by category"
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show more details"
)
def list_prompts(category: str, verbose: bool):
    """
    List all prompts.

    Examples:
        blogus prompts list
        blogus prompts list -c support
        blogus prompts list -v
    """
    engine = get_version_engine()
    prompts_list = engine.list_prompts()

    if not prompts_list:
        click.echo("No prompts found.")
        click.echo("Create one with: blogus prompts new <name>")
        return

    # Filter by category if specified
    if category:
        prompts_list = [
            p for p in prompts_list
            if p.parsed.metadata.category.lower() == category.lower()
        ]

    if not prompts_list:
        click.echo(f"No prompts found in category: {category}")
        return

    click.echo(f"Found {len(prompts_list)} prompt(s):\n")

    for vp in prompts_list:
        meta = vp.parsed.metadata
        version = vp.version

        # Status indicator
        status = "●" if not vp.is_dirty else "○"
        dirty_marker = " (modified)" if vp.is_dirty else ""

        if verbose:
            click.echo(f"{status} {meta.name} v{version.version}{dirty_marker}")
            click.echo(f"    Description: {meta.description[:60]}...")
            click.echo(f"    Category: {meta.category}")
            click.echo(f"    Model: {meta.model.id}")
            if meta.goal:
                click.echo(f"    Goal: {meta.goal[:50]}...")
            click.echo(f"    Variables: {', '.join(v.name for v in meta.variables) or 'none'}")
            click.echo(f"    Hash: {version.content_hash}")
            click.echo()
        else:
            vars_str = f" [{', '.join(v.name for v in meta.variables)}]" if meta.variables else ""
            click.echo(f"{status} {meta.name:<25} v{version.version:<3} {meta.category:<12}{vars_str}{dirty_marker}")


@prompts.command("show")
@click.argument("name", type=str)
@click.option(
    "--version",
    "-v",
    "version_num",
    type=int,
    help="Show specific version"
)
@click.option(
    "--content",
    "-c",
    is_flag=True,
    help="Show full content"
)
def show_prompt(name: str, version_num: int, content: bool):
    """
    Display prompt details.

    Examples:
        blogus prompts show my-assistant
        blogus prompts show my-assistant -c  # Show content
        blogus prompts show my-assistant -v 2  # Show version 2
    """
    engine = get_version_engine()
    vp = engine.get_prompt_by_name(name)

    if not vp:
        # Try with file path
        prompt_path = get_prompts_dir() / f"{name}.prompt"
        vp = engine.get_versioned_prompt(prompt_path)

    if not vp:
        click.echo(f"Prompt not found: {name}", err=True)
        click.echo("Use 'blogus prompts list' to see available prompts")
        raise click.Abort()

    # If specific version requested
    if version_num:
        parsed = engine.get_prompt_at_version(vp.parsed.file_path, version_num)
        if not parsed:
            click.echo(f"Version {version_num} not found", err=True)
            raise click.Abort()
        meta = parsed.metadata
        version_str = f"v{version_num}"
    else:
        parsed = vp.parsed
        meta = parsed.metadata
        version_str = f"v{vp.version.version}"

    # Display header
    click.echo(f"\n{'=' * 60}")
    click.echo(f"  {meta.name} {version_str}")
    click.echo(f"{'=' * 60}\n")

    # Metadata
    click.echo(f"Description: {meta.description}")
    click.echo(f"Category:    {meta.category}")
    click.echo(f"Author:      {meta.author}")
    click.echo(f"Model:       {meta.model.id} (temp={meta.model.temperature})")

    if meta.goal:
        click.echo(f"\nGoal:")
        click.echo(f"  {meta.goal}")

    if meta.tags:
        click.echo(f"\nTags: {', '.join(meta.tags)}")

    # Variables
    if meta.variables:
        click.echo(f"\nVariables:")
        for v in meta.variables:
            req = "required" if v.required else "optional"
            enum_str = f" [{', '.join(v.enum)}]" if v.enum else ""
            click.echo(f"  {{{{ {v.name} }}}} - {v.description} ({req}){enum_str}")

    # Version info
    if not version_num and vp.version:
        click.echo(f"\nVersion Info:")
        click.echo(f"  Version:  {vp.version.version}")
        click.echo(f"  Hash:     {vp.version.content_hash}")
        if vp.version.commit_sha:
            click.echo(f"  Commit:   {vp.version.short_sha}")
        click.echo(f"  Modified: {vp.version.timestamp.strftime('%Y-%m-%d %H:%M')}")
        if vp.is_dirty:
            click.echo(f"  Status:   Uncommitted changes")

    # Content
    if content:
        click.echo(f"\n{'-' * 60}")
        click.echo("Content:\n")
        click.echo(parsed.content)
        click.echo(f"\n{'-' * 60}")

    # Marker for code
    if vp.parsed.file_path:
        marker = engine.get_marker_string(vp.parsed.file_path)
        if marker:
            click.echo(f"\nCode marker: # {marker}")


@prompts.command("validate")
@click.argument("name", type=str, required=False)
@click.option(
    "--all",
    "validate_all",
    is_flag=True,
    help="Validate all prompts"
)
def validate_prompt(name: str, validate_all: bool):
    """
    Validate prompt files.

    Examples:
        blogus prompts validate my-assistant
        blogus prompts validate --all
    """
    engine = get_version_engine()
    prompts_dir = get_prompts_dir()

    if validate_all or not name:
        # Validate all prompts
        prompt_files = list(prompts_dir.glob("*.prompt"))
        if not prompt_files:
            click.echo("No prompts to validate.")
            return

        click.echo(f"Validating {len(prompt_files)} prompt(s)...\n")
        all_valid = True

        for pf in prompt_files:
            issues = engine.validate_prompt(pf)
            if issues:
                all_valid = False
                click.echo(f"✗ {pf.name}")
                for issue in issues:
                    click.echo(f"    - {issue}")
            else:
                click.echo(f"✓ {pf.name}")

        click.echo()
        if all_valid:
            click.echo("All prompts are valid!")
        else:
            click.echo("Some prompts have issues.", err=True)
            raise click.Abort()
    else:
        # Validate single prompt
        prompt_path = prompts_dir / f"{name}.prompt"
        if not prompt_path.exists():
            click.echo(f"Prompt not found: {name}", err=True)
            raise click.Abort()

        issues = engine.validate_prompt(prompt_path)
        if issues:
            click.echo(f"Validation failed for {name}:")
            for issue in issues:
                click.echo(f"  - {issue}")
            raise click.Abort()
        else:
            click.echo(f"✓ {name} is valid")


@prompts.command("history")
@click.argument("name", type=str)
@click.option(
    "--limit",
    "-n",
    type=int,
    default=20,
    help="Number of versions to show"
)
def history_prompt(name: str, limit: int):
    """
    Show version history for a prompt.

    Examples:
        blogus prompts history my-assistant
        blogus prompts history my-assistant -n 5
    """
    engine = get_version_engine()
    prompts_dir = get_prompts_dir()
    prompt_path = prompts_dir / f"{name}.prompt"

    if not prompt_path.exists():
        click.echo(f"Prompt not found: {name}", err=True)
        raise click.Abort()

    versions = engine.get_history(prompt_path, limit=limit)

    if not versions:
        click.echo(f"No version history for {name}")
        click.echo("(Prompt may not be committed to Git yet)")
        return

    click.echo(f"\nVersion history for {name}:\n")

    for v in versions:
        date_str = v.timestamp.strftime("%Y-%m-%d %H:%M")
        tag_str = f" [{v.tag}]" if v.tag else ""
        click.echo(f"  v{v.version:<3}  {v.short_sha}  {date_str}  {v.author}{tag_str}")
        if v.message:
            # Truncate long messages
            msg = v.message[:60] + "..." if len(v.message) > 60 else v.message
            click.echo(f"         └─ {msg}")

    click.echo()
    click.echo(f"Total: {len(versions)} version(s)")


@prompts.command("diff")
@click.argument("name", type=str)
@click.argument("version1", type=int)
@click.argument("version2", type=int)
def diff_prompt(name: str, version1: int, version2: int):
    """
    Compare two versions of a prompt.

    Examples:
        blogus prompts diff my-assistant 1 2
    """
    engine = get_version_engine()
    prompts_dir = get_prompts_dir()
    prompt_path = prompts_dir / f"{name}.prompt"

    if not prompt_path.exists():
        click.echo(f"Prompt not found: {name}", err=True)
        raise click.Abort()

    diff = engine.diff(prompt_path, version1, version2)

    if not diff:
        click.echo(f"Could not generate diff between v{version1} and v{version2}")
        raise click.Abort()

    click.echo(f"\nDiff: {name} v{version1} → v{version2}\n")

    # Metadata changes
    if diff.metadata_changes:
        click.echo("Metadata changes:")
        for field, (old, new) in diff.metadata_changes.items():
            click.echo(f"  {field}: {old} → {new}")
        click.echo()

    # Stats
    click.echo(f"Lines: +{diff.lines_added} -{diff.lines_removed}\n")

    # Content diff
    if diff.content_diff:
        click.echo("Content diff:")
        click.echo(diff.content_diff)


# Export the group
prompts_group = prompts
