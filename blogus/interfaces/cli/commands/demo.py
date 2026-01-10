"""
CLI command for launching the interactive TUI demo.

Usage:
    blogus demo              # Launch demo with auto-generated project
    blogus demo --speed slow # Slow animations for presentations
    blogus demo -p ./myproj  # Use existing project
"""

import click
from pathlib import Path
from typing import Optional


@click.command("demo")
@click.option(
    "--speed",
    "-s",
    type=click.Choice(["slow", "normal", "fast"]),
    default="normal",
    help="Animation speed (slow for presentations, fast for quick demos)",
)
@click.option(
    "--project",
    "-p",
    type=click.Path(exists=True, path_type=Path),
    help="Use an existing project instead of demo project",
)
@click.option(
    "--no-cleanup",
    is_flag=True,
    help="Don't cleanup demo project on exit",
)
def demo_command(
    speed: str,
    project: Optional[Path],
    no_cleanup: bool,
):
    """
    Launch interactive TUI demo.

    This starts a visually impressive terminal-based demo that showcases
    Blogus capabilities including:

    - Prompt scanning and detection
    - LLM-powered prompt analysis
    - Multi-model comparison
    - Version management workflow (check/fix/lock/verify)

    Perfect for conference talks and presentations!

    Examples:

        blogus demo                  # Start with demo project

        blogus demo --speed slow     # Slow animations for talks

        blogus demo -p ./my-project  # Demo with your own project
    """
    try:
        from textual.app import App
    except ImportError:
        click.echo(
            "Error: TUI dependencies not installed.\n"
            "Install with: pip install blogus[tui]\n"
            "Or: pip install textual",
            err=True,
        )
        raise SystemExit(1)

    from ...tui.app import BlogusDemoApp
    from ...tui.demo_data.setup import setup_demo_project, cleanup_demo_project

    demo_path = None
    created_demo = False

    try:
        if project:
            demo_path = project.resolve()
            click.echo(f"Using project: {demo_path}")
        else:
            click.echo("Setting up demo project...")
            demo_path = setup_demo_project()
            created_demo = True
            click.echo(f"Demo project created at: {demo_path}")

        click.echo("Launching demo... (Press 'q' to quit)")

        # Launch the TUI app
        app = BlogusDemoApp(demo_path=demo_path, speed=speed)
        app.run()

    except Exception as e:
        click.echo(f"Error launching demo: {e}", err=True)
        raise SystemExit(1)

    finally:
        # Cleanup demo project if we created it
        if created_demo and not no_cleanup and demo_path:
            try:
                cleanup_demo_project(demo_path)
                click.echo("Demo project cleaned up.")
            except Exception:
                pass

    click.echo("Thanks for watching the Blogus demo!")
