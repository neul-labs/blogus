"""
CLI commands for scanning and validating prompts in codebases.

Commands:
- scan: Scan project for prompts and LLM API calls
- check: Validate versioning for CI/CD
- fix: Add missing @blogus markers
"""

import click
from pathlib import Path
from typing import Optional
import json

from ....domain.services.detection_engine import DetectionEngine


@click.command("scan")
@click.option(
    "--path",
    "-p",
    type=click.Path(exists=True, path_type=Path),
    default=".",
    help="Path to scan (default: current directory)"
)
@click.option(
    "--python/--no-python",
    default=True,
    help="Include Python files in scan"
)
@click.option(
    "--js/--no-js",
    default=True,
    help="Include JavaScript/TypeScript files in scan"
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Save report to file"
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["text", "json", "markdown"]),
    default="text",
    help="Output format"
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed output"
)
def scan(
    path: Path,
    python: bool,
    js: bool,
    output: Optional[Path],
    format: str,
    verbose: bool
):
    """
    Scan project for prompts and LLM API calls.

    Detects:
    - .prompt files in the project
    - LLM API calls (OpenAI, Anthropic, LiteLLM, etc.)
    - @blogus: version markers in code comments

    Examples:
        blogus scan                      # Scan current directory
        blogus scan -p ./src             # Scan specific path
        blogus scan --format json        # Output as JSON
        blogus scan -o report.md -f markdown  # Save markdown report
    """
    engine = DetectionEngine(path.resolve())

    click.echo(f"Scanning {path.resolve()}...\n")

    result = engine.scan(
        include_python=python,
        include_js=js,
        include_prompt_files=True
    )

    # Generate report
    report = engine.generate_report(result, format)

    if output:
        output.write_text(report)
        click.echo(f"Report saved to: {output}")
    else:
        click.echo(report)

    # Show summary if verbose
    if verbose and format == "text":
        click.echo("\n" + "=" * 50)
        click.echo("Detailed Detections:")
        click.echo("-" * 50)

        for p in result.all_prompts:
            try:
                rel_path = p.file_path.relative_to(path.resolve())
            except ValueError:
                rel_path = p.file_path

            status_icon = "✓" if p.is_versioned else "○"
            linked = f" → {p.linked_prompt}" if p.linked_prompt else ""

            click.echo(f"{status_icon} {rel_path}:{p.line_number}")
            click.echo(f"    Type: {p.detection_type} ({p.language})")
            if p.api_type:
                click.echo(f"    API: {p.api_type}")
            if p.function_name:
                click.echo(f"    Function: {p.function_name}")
            if p.variable_name:
                click.echo(f"    Variable: {p.variable_name}")
            click.echo(f"    Hash: {p.content_hash}{linked}")
            click.echo()

    # Exit with error if there are issues
    if result.errors:
        raise SystemExit(1)


@click.command("check")
@click.option(
    "--path",
    "-p",
    type=click.Path(exists=True, path_type=Path),
    default=".",
    help="Path to check (default: current directory)"
)
@click.option(
    "--strict",
    is_flag=True,
    help="Fail if any untracked prompts are found"
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Save issues to file (JSON format)"
)
def check(path: Path, strict: bool, output: Optional[Path]):
    """
    Validate prompt versioning for CI/CD.

    Checks:
    - All prompts have @blogus markers
    - Markers match current prompt versions
    - .prompt files are valid

    Examples:
        blogus check                     # Basic validation
        blogus check --strict            # Fail on any untracked prompts
        blogus check -o issues.json      # Save issues to file
    """
    engine = DetectionEngine(path.resolve())

    click.echo(f"Validating prompts in {path.resolve()}...\n")

    is_valid, issues = engine.validate(strict=strict)

    # Group issues by type
    issues_by_type = {}
    for issue in issues:
        issue_type = issue['type']
        if issue_type not in issues_by_type:
            issues_by_type[issue_type] = []
        issues_by_type[issue_type].append(issue)

    # Display results
    if issues:
        click.echo("Issues found:\n")

        if 'untracked' in issues_by_type:
            click.echo(f"Untracked prompts ({len(issues_by_type['untracked'])}):")
            for issue in issues_by_type['untracked']:
                click.echo(f"  ○ {issue['file']}:{issue['line']}")
            click.echo()

        if 'outdated' in issues_by_type:
            click.echo(f"Outdated markers ({len(issues_by_type['outdated'])}):")
            for issue in issues_by_type['outdated']:
                click.echo(f"  ⚠ {issue['file']}:{issue['line']} - {issue['message']}")
            click.echo()

        if 'missing_prompt' in issues_by_type:
            click.echo(f"Missing prompt files ({len(issues_by_type['missing_prompt'])}):")
            for issue in issues_by_type['missing_prompt']:
                click.echo(f"  ✗ {issue['file']}:{issue['line']} - {issue['message']}")
            click.echo()

        if 'validation' in issues_by_type:
            click.echo(f"Validation errors ({len(issues_by_type['validation'])}):")
            for issue in issues_by_type['validation']:
                click.echo(f"  ✗ {issue['file']} - {issue['message']}")
            click.echo()
    else:
        click.echo("✓ All prompts are properly versioned and valid!")

    # Save issues to file if requested
    if output:
        output.write_text(json.dumps(issues, indent=2))
        click.echo(f"\nIssues saved to: {output}")

    # Summary
    click.echo(f"\nTotal issues: {len(issues)}")
    if strict:
        click.echo("Mode: strict (failing on untracked prompts)")

    if not is_valid:
        click.echo("\n✗ Validation failed", err=True)
        raise SystemExit(1)
    else:
        click.echo("\n✓ Validation passed")


@click.command("fix")
@click.option(
    "--path",
    "-p",
    type=click.Path(exists=True, path_type=Path),
    default=".",
    help="Path to fix (default: current directory)"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be changed without modifying files"
)
@click.option(
    "--link",
    "-l",
    type=str,
    help="Link all detections to a specific prompt name"
)
def fix(path: Path, dry_run: bool, link: Optional[str]):
    """
    Add missing @blogus markers to detected prompts.

    Scans the project for untracked LLM API calls and adds
    version markers above them.

    Examples:
        blogus fix                       # Add markers to all untracked prompts
        blogus fix --dry-run             # Preview changes without modifying
        blogus fix -l my-prompt          # Link all to 'my-prompt'
    """
    engine = DetectionEngine(path.resolve())

    click.echo(f"Scanning {path.resolve()} for untracked prompts...\n")

    result = engine.scan()
    untracked = result.untracked_prompts

    if not untracked:
        click.echo("✓ No untracked prompts found!")
        return

    click.echo(f"Found {len(untracked)} untracked prompt(s):\n")

    for p in untracked:
        try:
            rel_path = p.file_path.relative_to(path.resolve())
        except ValueError:
            rel_path = p.file_path

        marker_name = link or p.variable_name or p.function_name or f"prompt-{p.content_hash[:8]}"
        marker = f"@blogus:{marker_name} sha256:{p.content_hash}"

        click.echo(f"  {rel_path}:{p.line_number}")
        click.echo(f"    → Add: # {marker}" if p.language == 'python' else f"    → Add: // {marker}")
        click.echo()

    if dry_run:
        click.echo("Dry run - no files modified")
        return

    # Confirm before modifying
    if not click.confirm(f"Add markers to {len(untracked)} file(s)?"):
        click.echo("Aborted.")
        return

    # Add markers
    modified_files = engine.add_markers(untracked, link)

    click.echo(f"\n✓ Added markers to {len(modified_files)} file(s):")
    for f in modified_files:
        try:
            rel_path = f.relative_to(path.resolve())
        except ValueError:
            rel_path = f
        click.echo(f"  - {rel_path}")


@click.command("lock")
@click.option(
    "--path",
    "-p",
    type=click.Path(exists=True, path_type=Path),
    default=".",
    help="Path to project (default: current directory)"
)
def lock(path: Path):
    """
    Update the prompts.lock file with current versions.

    Creates/updates .blogus/prompts.lock with hashes of all
    managed prompts for reproducible deployments.

    Examples:
        blogus lock                      # Update lock file
    """
    engine = DetectionEngine(path.resolve())
    blogus_dir = path.resolve() / ".blogus"
    lock_file = blogus_dir / "prompts.lock"

    if not blogus_dir.exists():
        click.echo("Error: Not a Blogus project. Run 'blogus init' first.", err=True)
        raise SystemExit(1)

    result = engine.scan(include_python=False, include_js=False)

    lock_data = {
        "version": 1,
        "prompts": {}
    }

    for vp in result.prompt_files:
        lock_data["prompts"][vp.parsed.metadata.name] = {
            "version": vp.version.version,
            "content_hash": vp.version.content_hash,
            "commit_sha": vp.version.commit_sha,
            "file": str(vp.parsed.file_path.relative_to(path.resolve()))
        }

    lock_file.write_text(json.dumps(lock_data, indent=2))

    click.echo(f"✓ Updated {lock_file.relative_to(path.resolve())}")
    click.echo(f"  Locked {len(lock_data['prompts'])} prompt(s):")
    for name, info in lock_data["prompts"].items():
        click.echo(f"    - {name} v{info['version']} ({info['content_hash'][:8]})")


@click.command("verify")
@click.option(
    "--path",
    "-p",
    type=click.Path(exists=True, path_type=Path),
    default=".",
    help="Path to project (default: current directory)"
)
def verify(path: Path):
    """
    Verify that prompts match the lock file.

    Compares current prompt hashes against .blogus/prompts.lock
    to ensure reproducible deployments.

    Examples:
        blogus verify                    # Verify lock file
    """
    lock_file = path.resolve() / ".blogus" / "prompts.lock"

    if not lock_file.exists():
        click.echo("Error: No lock file found. Run 'blogus lock' first.", err=True)
        raise SystemExit(1)

    try:
        lock_data = json.loads(lock_file.read_text())
    except json.JSONDecodeError:
        click.echo("Error: Invalid lock file format.", err=True)
        raise SystemExit(1)

    engine = DetectionEngine(path.resolve())
    result = engine.scan(include_python=False, include_js=False)

    mismatches = []
    missing = []

    # Check locked prompts against current state
    for name, info in lock_data.get("prompts", {}).items():
        found = False
        for vp in result.prompt_files:
            if vp.parsed.metadata.name == name:
                found = True
                if vp.version.content_hash != info["content_hash"]:
                    mismatches.append({
                        "name": name,
                        "locked_hash": info["content_hash"],
                        "current_hash": vp.version.content_hash
                    })
                break

        if not found:
            missing.append(name)

    if mismatches or missing:
        click.echo("✗ Lock file verification failed:\n", err=True)

        if mismatches:
            click.echo("Hash mismatches:")
            for m in mismatches:
                click.echo(f"  - {m['name']}: locked={m['locked_hash'][:8]} current={m['current_hash'][:8]}")

        if missing:
            click.echo("\nMissing prompts:")
            for name in missing:
                click.echo(f"  - {name}")

        click.echo("\nRun 'blogus lock' to update the lock file.")
        raise SystemExit(1)
    else:
        click.echo(f"✓ All {len(lock_data.get('prompts', {}))} prompt(s) match lock file")


# Export commands
scan_command = scan
check_command = check
fix_command = fix
lock_command = lock
verify_command = verify
