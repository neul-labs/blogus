"""
CLI template commands.
"""

import asyncio
import click
import json
from typing import Optional, List

from ...web.container import get_container
from ....application.dto import CreateTemplateRequest, RenderTemplateRequest
from ....shared.exceptions import BlogusError
from ....shared.logging import get_logger


@click.group()
def templates():
    """Manage prompt templates."""
    pass


@templates.command("create")
@click.argument("template_id", type=str)
@click.argument("name", type=str)
@click.argument("content", type=str)
@click.option("--description", type=str, default="", help="Template description")
@click.option("--category", type=str, default="general", help="Template category")
@click.option("--tags", type=str, help="Comma-separated tags")
@click.option("--author", type=str, default="unknown", help="Template author")
async def create_template(template_id: str, name: str, content: str, description: str,
                         category: str, tags: Optional[str], author: str):
    """Create a new template."""
    logger = get_logger("blogus.cli.templates")
    container = get_container()

    try:
        # Parse tags
        tag_list = [tag.strip() for tag in tags.split(",")] if tags else []

        # Create request
        request = CreateTemplateRequest(
            template_id=template_id,
            name=name,
            description=description,
            content=content,
            category=category,
            tags=tag_list,
            author=author
        )

        # Create template
        response = await container.get_template_service().create_template(request)

        click.echo(f"✓ Created template '{template_id}'")
        click.echo(f"  Name: {response.template.name}")
        click.echo(f"  Variables: {', '.join(response.template.variables)}")

    except BlogusError as e:
        logger.error(f"Template creation failed: {e}")
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@templates.command("list")
@click.option("--category", type=str, help="Filter by category")
@click.option("--tag", type=str, help="Filter by tag")
@click.option("--format", "output_format", type=click.Choice(["text", "json"]), default="text")
async def list_templates(category: Optional[str], tag: Optional[str], output_format: str):
    """List available templates."""
    container = get_container()

    try:
        templates_list = await container.get_template_service().list_templates(category, tag)

        if output_format == "json":
            output_data = [
                {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "category": t.category,
                    "tags": t.tags,
                    "variables": t.variables,
                    "usage_count": t.usage_count
                }
                for t in templates_list
            ]
            click.echo(json.dumps(output_data, indent=2))
        else:
            if not templates_list:
                click.echo("No templates found.")
                return

            click.echo(f"\nFound {len(templates_list)} template(s):")
            click.echo("="*60)

            for template in templates_list:
                click.echo(f"\nID: {template.id}")
                click.echo(f"Name: {template.name}")
                click.echo(f"Description: {template.description}")
                click.echo(f"Category: {template.category}")
                click.echo(f"Tags: {', '.join(template.tags)}")
                click.echo(f"Variables: {', '.join(template.variables)}")
                click.echo(f"Usage Count: {template.usage_count}")

    except BlogusError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@templates.command("render")
@click.argument("template_id", type=str)
@click.option("--variables", type=str, help="JSON string of variables")
@click.option("--var", multiple=True, help="Variable in format key=value")
async def render_template(template_id: str, variables: Optional[str], var: tuple):
    """Render a template with variables."""
    container = get_container()

    try:
        # Parse variables
        var_dict = {}

        # From JSON string
        if variables:
            var_dict.update(json.loads(variables))

        # From --var options
        for variable in var:
            if "=" not in variable:
                click.echo(f"Invalid variable format: {variable}. Use key=value", err=True)
                raise click.Abort()
            key, value = variable.split("=", 1)
            var_dict[key] = value

        # Create request
        request = RenderTemplateRequest(
            template_id=template_id,
            variables=var_dict
        )

        # Render template
        response = await container.get_template_service().render_template(request)

        click.echo("Rendered template:")
        click.echo("-" * 40)
        click.echo(response.rendered_content)

    except BlogusError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON in --variables: {e}", err=True)
        raise click.Abort()


@templates.command("show")
@click.argument("template_id", type=str)
async def show_template(template_id: str):
    """Show template details."""
    container = get_container()

    try:
        template = await container.get_template_service().get_template(template_id)

        if not template:
            click.echo(f"Template '{template_id}' not found.", err=True)
            raise click.Abort()

        click.echo(f"Template: {template.id}")
        click.echo("="*60)
        click.echo(f"Name: {template.name}")
        click.echo(f"Description: {template.description}")
        click.echo(f"Category: {template.category}")
        click.echo(f"Tags: {', '.join(template.tags)}")
        click.echo(f"Author: {template.author}")
        click.echo(f"Version: {template.version}")
        click.echo(f"Variables: {', '.join(template.variables)}")
        click.echo(f"Usage Count: {template.usage_count}")
        click.echo(f"Created: {template.created_at}")
        click.echo(f"Updated: {template.updated_at}")
        click.echo("\nContent:")
        click.echo("-" * 40)
        click.echo(template.content)

    except BlogusError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


# Sync wrappers
def sync_wrapper(func):
    """Create sync wrapper for async function."""
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))
    return wrapper


# Replace async callbacks with sync wrappers
create_template.callback = sync_wrapper(create_template.callback)
list_templates.callback = sync_wrapper(list_templates.callback)
render_template.callback = sync_wrapper(render_template.callback)
show_template.callback = sync_wrapper(show_template.callback)