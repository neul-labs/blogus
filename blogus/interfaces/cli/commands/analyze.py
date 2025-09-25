"""
CLI analyze command.
"""

import asyncio
import click
from typing import Optional

from ...web.container import get_container
from ....application.dto import AnalyzePromptRequest
from ....shared.exceptions import BlogusError
from ....shared.logging import get_logger


@click.command()
@click.argument("prompt", type=str)
@click.option(
    "--judge-model",
    type=str,
    help="Judge model to use for analysis"
)
@click.option(
    "--goal",
    type=str,
    default=None,
    help="Goal for the prompt (will be inferred if not provided)"
)
@click.option(
    "--output-format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format"
)
async def analyze(prompt: str, judge_model: Optional[str], goal: Optional[str], output_format: str):
    """Analyze a prompt for effectiveness and goal alignment."""
    logger = get_logger("blogus.cli.analyze")
    container = get_container()

    try:
        # Use default model if not specified
        if not judge_model:
            judge_model = container.settings.llm.default_judge_model

        # Create request
        request = AnalyzePromptRequest(
            prompt_text=prompt,
            judge_model=judge_model,
            goal=goal
        )

        # Analyze prompt
        click.echo(f"Analyzing prompt with {judge_model}...")
        response = await container.get_prompt_service().analyze_prompt(request)

        # Output results
        if output_format == "json":
            import json
            output_data = {
                "analysis": {
                    "goal_alignment": response.analysis.goal_alignment,
                    "effectiveness": response.analysis.effectiveness,
                    "suggestions": response.analysis.suggestions,
                    "status": response.analysis.status,
                    "inferred_goal": response.analysis.inferred_goal
                },
                "fragments": [
                    {
                        "text": f.text,
                        "type": f.fragment_type,
                        "goal_alignment": f.goal_alignment,
                        "improvement_suggestion": f.improvement_suggestion
                    }
                    for f in response.fragments
                ]
            }
            click.echo(json.dumps(output_data, indent=2))
        else:
            # Text format
            click.echo("\n" + "="*60)
            click.echo("PROMPT ANALYSIS RESULTS")
            click.echo("="*60)

            analysis = response.analysis
            click.echo(f"Goal Alignment: {analysis.goal_alignment}/10")
            click.echo(f"Effectiveness: {analysis.effectiveness}/10")
            click.echo(f"Status: {analysis.status}")

            if analysis.inferred_goal:
                click.echo(f"Inferred Goal: {analysis.inferred_goal}")

            if analysis.suggestions:
                click.echo("\nSuggested Improvements:")
                for i, suggestion in enumerate(analysis.suggestions, 1):
                    click.echo(f"  {i}. {suggestion}")

            if response.fragments:
                click.echo(f"\nFragment Analysis ({len(response.fragments)} fragments):")
                for i, fragment in enumerate(response.fragments, 1):
                    click.echo(f"\n  Fragment {i}: {fragment.fragment_type}")
                    click.echo(f"    Text: {fragment.text[:100]}{'...' if len(fragment.text) > 100 else ''}")
                    click.echo(f"    Alignment: {fragment.goal_alignment}/5")
                    click.echo(f"    Suggestion: {fragment.improvement_suggestion}")

    except BlogusError as e:
        logger.error(f"Analysis failed: {e}")
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        click.echo(f"Unexpected error: {e}", err=True)
        raise click.Abort()


# Make command work with asyncio
def analyze_sync(prompt: str, judge_model: Optional[str], goal: Optional[str], output_format: str):
    """Synchronous wrapper for the analyze command."""
    return asyncio.run(analyze(prompt, judge_model, goal, output_format))


# Replace the async command with sync wrapper
analyze.callback = analyze_sync