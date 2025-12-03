"""
CLI registry commands for prompt deployment management.
"""

import asyncio
import click
import json
from typing import Optional

from ...web.container import get_container
from ....application.dto import (
    RegisterDeploymentRequest, UpdateDeploymentContentRequest,
    UpdateDeploymentModelRequest, SetTrafficConfigRequest,
    ExecuteDeploymentRequest, RollbackDeploymentRequest,
    GetMetricsRequest, CompareVersionsRequest, TrafficRouteDto
)
from ....shared.exceptions import BlogusError, ConfigurationError
from ....shared.logging import get_logger


@click.group()
def registry():
    """Manage prompt deployments in the registry."""
    pass


# ==================== Deployment Management ====================

@registry.command("register")
@click.argument("name", type=str)
@click.argument("content", type=str)
@click.option("--model", "-m", required=True, help="Model ID (e.g., gpt-4o, claude-3-sonnet-20240229)")
@click.option("--description", "-d", default="", help="Deployment description")
@click.option("--goal", "-g", type=str, help="Goal for this prompt")
@click.option("--temperature", type=float, default=0.7, help="Model temperature (0.0-2.0)")
@click.option("--max-tokens", type=int, default=1000, help="Max tokens for response")
@click.option("--category", type=str, default="general", help="Deployment category")
@click.option("--tags", type=str, help="Comma-separated tags")
@click.option("--author", type=str, default="anonymous", help="Author name")
@click.option("--from-file", "-f", type=click.Path(exists=True), help="Read content from file")
async def register_deployment(name: str, content: str, model: str, description: str,
                              goal: Optional[str], temperature: float, max_tokens: int,
                              category: str, tags: Optional[str], author: str,
                              from_file: Optional[str]):
    """Register a new prompt deployment.

    NAME is the deployment slug (lowercase, alphanumeric, hyphens).
    CONTENT is the prompt text (or use --from-file).
    """
    logger = get_logger("blogus.cli.registry")
    container = get_container()

    try:
        # Read content from file if specified
        actual_content = content
        if from_file:
            with open(from_file, 'r') as f:
                actual_content = f.read()

        # Parse tags
        tag_list = [tag.strip() for tag in tags.split(",")] if tags else []

        # Create request
        request = RegisterDeploymentRequest(
            name=name,
            description=description or f"Deployment: {name}",
            content=actual_content,
            model_id=model,
            goal=goal,
            temperature=temperature,
            max_tokens=max_tokens,
            category=category,
            tags=tag_list,
            author=author
        )

        # Register deployment
        response = await container.get_registry_service().register_deployment(request)
        deployment = response.deployment

        click.echo(f"Registered deployment '{name}'")
        click.echo(f"  ID: {deployment.id}")
        click.echo(f"  Model: {deployment.model_config.model_id}")
        click.echo(f"  Version: {deployment.version}")
        if deployment.is_template:
            click.echo(f"  Variables: {', '.join(deployment.template_variables)}")

    except ConfigurationError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    except BlogusError as e:
        logger.error(f"Registration failed: {e}")
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@registry.command("list")
@click.option("--status", type=click.Choice(["active", "inactive", "archived"]), help="Filter by status")
@click.option("--category", type=str, help="Filter by category")
@click.option("--tag", type=str, help="Filter by tag")
@click.option("--limit", type=int, default=50, help="Maximum results")
@click.option("--format", "output_format", type=click.Choice(["text", "json"]), default="text")
async def list_deployments(status: Optional[str], category: Optional[str],
                           tag: Optional[str], limit: int, output_format: str):
    """List registered deployments."""
    container = get_container()

    try:
        tags_list = [tag] if tag else None
        deployments = await container.get_registry_service().list_deployments(
            limit=limit,
            status=status,
            category=category,
            tags=tags_list
        )

        if output_format == "json":
            output_data = [
                {
                    "name": d.name,
                    "description": d.description,
                    "model_id": d.model_id,
                    "version": d.version,
                    "status": d.status,
                    "category": d.category,
                    "is_template": d.is_template,
                    "updated_at": d.updated_at.isoformat()
                }
                for d in deployments
            ]
            click.echo(json.dumps(output_data, indent=2))
        else:
            if not deployments:
                click.echo("No deployments found.")
                return

            click.echo(f"\nFound {len(deployments)} deployment(s):")
            click.echo("=" * 80)

            for d in deployments:
                template_marker = "[T]" if d.is_template else "   "
                status_marker = {"active": "", "inactive": "[I]", "archived": "[A]"}.get(d.status, "")
                click.echo(f"{template_marker} {d.name:<30} v{d.version:<3} {d.model_id:<25} {status_marker}")

    except BlogusError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@registry.command("show")
@click.argument("name", type=str)
@click.option("--show-content", is_flag=True, help="Show full prompt content")
@click.option("--show-history", is_flag=True, help="Show version history")
async def show_deployment(name: str, show_content: bool, show_history: bool):
    """Show deployment details."""
    container = get_container()

    try:
        deployment = await container.get_registry_service().get_deployment(name)

        if not deployment:
            click.echo(f"Deployment '{name}' not found.", err=True)
            raise click.Abort()

        click.echo(f"\nDeployment: {deployment.name}")
        click.echo("=" * 60)
        click.echo(f"ID: {deployment.id}")
        click.echo(f"Description: {deployment.description}")
        click.echo(f"Status: {deployment.status}")
        click.echo(f"Version: {deployment.version}")
        click.echo(f"Model: {deployment.model_config.model_id}")
        click.echo(f"Temperature: {deployment.model_config.parameters.temperature}")
        click.echo(f"Max Tokens: {deployment.model_config.parameters.max_tokens}")
        click.echo(f"Category: {deployment.category}")
        click.echo(f"Tags: {', '.join(deployment.tags)}")
        click.echo(f"Author: {deployment.author}")

        if deployment.is_template:
            click.echo(f"Template Variables: {', '.join(deployment.template_variables)}")

        if deployment.goal:
            click.echo(f"Goal: {deployment.goal}")

        if deployment.traffic_config:
            click.echo("\nTraffic Configuration:")
            for route in deployment.traffic_config.routes:
                override = f" (model: {route.model_override})" if route.model_override else ""
                click.echo(f"  v{route.version}: {route.weight}%{override}")
            if deployment.traffic_config.shadow_version:
                click.echo(f"  Shadow: v{deployment.traffic_config.shadow_version}")

        click.echo(f"\nCreated: {deployment.created_at}")
        click.echo(f"Updated: {deployment.updated_at}")

        if show_content:
            click.echo("\nContent:")
            click.echo("-" * 40)
            click.echo(deployment.content)

        if show_history and deployment.version_history:
            click.echo(f"\nVersion History ({len(deployment.version_history)} previous versions):")
            click.echo("-" * 40)
            for vr in reversed(deployment.version_history[-5:]):  # Show last 5
                summary = vr.change_summary or "No summary"
                click.echo(f"  v{vr.version}: {summary} (by {vr.created_by}, {vr.created_at.strftime('%Y-%m-%d')})")

    except BlogusError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@registry.command("update-content")
@click.argument("name", type=str)
@click.argument("content", type=str, required=False)
@click.option("--from-file", "-f", type=click.Path(exists=True), help="Read content from file")
@click.option("--author", "-a", required=True, help="Author of this change")
@click.option("--summary", "-s", type=str, help="Summary of changes")
async def update_content(name: str, content: Optional[str], from_file: Optional[str],
                         author: str, summary: Optional[str]):
    """Update deployment content (creates new version)."""
    container = get_container()

    try:
        # Get content
        if from_file:
            with open(from_file, 'r') as f:
                actual_content = f.read()
        elif content:
            actual_content = content
        else:
            click.echo("Error: Provide content or use --from-file", err=True)
            raise click.Abort()

        request = UpdateDeploymentContentRequest(
            name=name,
            new_content=actual_content,
            author=author,
            change_summary=summary
        )

        deployment = await container.get_registry_service().update_content(request)

        click.echo(f"Updated '{name}' to version {deployment.version}")
        click.echo(f"Content hash: {deployment.version_history[-1].content_hash if deployment.version_history else 'N/A'}")

    except ConfigurationError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    except BlogusError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@registry.command("update-model")
@click.argument("name", type=str)
@click.option("--model", "-m", required=True, help="New model ID")
@click.option("--author", "-a", required=True, help="Author of this change")
@click.option("--temperature", type=float, help="New temperature")
@click.option("--max-tokens", type=int, help="New max tokens")
@click.option("--summary", "-s", type=str, help="Summary of changes")
async def update_model(name: str, model: str, author: str, temperature: Optional[float],
                       max_tokens: Optional[int], summary: Optional[str]):
    """Update deployment model configuration (creates new version)."""
    container = get_container()

    try:
        request = UpdateDeploymentModelRequest(
            name=name,
            model_id=model,
            author=author,
            temperature=temperature,
            max_tokens=max_tokens,
            change_summary=summary
        )

        deployment = await container.get_registry_service().update_model_config(request)

        click.echo(f"Updated '{name}' model to {model} (version {deployment.version})")

    except ConfigurationError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    except BlogusError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@registry.command("rollback")
@click.argument("name", type=str)
@click.argument("version", type=int)
@click.option("--author", "-a", required=True, help="Author of this rollback")
async def rollback(name: str, version: int, author: str):
    """Rollback deployment to a previous version."""
    container = get_container()

    try:
        request = RollbackDeploymentRequest(
            name=name,
            target_version=version,
            author=author
        )

        deployment = await container.get_registry_service().rollback(request)

        click.echo(f"Rolled back '{name}' to version {version}")
        click.echo(f"New version: {deployment.version}")

    except ConfigurationError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    except BlogusError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@registry.command("set-status")
@click.argument("name", type=str)
@click.argument("status", type=click.Choice(["active", "inactive", "archived"]))
async def set_status(name: str, status: str):
    """Set deployment status."""
    container = get_container()

    try:
        deployment = await container.get_registry_service().set_status(name, status)
        click.echo(f"Set '{name}' status to {status}")

    except ConfigurationError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    except BlogusError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@registry.command("delete")
@click.argument("name", type=str)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
async def delete_deployment(name: str, yes: bool):
    """Delete a deployment."""
    container = get_container()

    try:
        if not yes:
            if not click.confirm(f"Delete deployment '{name}'?"):
                click.echo("Cancelled.")
                return

        deleted = await container.get_registry_service().delete_deployment(name)

        if deleted:
            click.echo(f"Deleted deployment '{name}'")
        else:
            click.echo(f"Deployment '{name}' not found.", err=True)
            raise click.Abort()

    except BlogusError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


# ==================== Traffic Routing ====================

@registry.command("set-traffic")
@click.argument("name", type=str)
@click.option("--route", "-r", multiple=True, help="Route in format version:weight (e.g., 1:80,2:20)")
@click.option("--shadow", type=int, help="Shadow test version")
async def set_traffic(name: str, route: tuple, shadow: Optional[int]):
    """Set traffic routing configuration for A/B testing.

    Example: blogus registry set-traffic my-prompt -r 1:80 -r 2:20 --shadow 3
    """
    container = get_container()

    try:
        if not route:
            click.echo("Error: At least one --route is required", err=True)
            raise click.Abort()

        routes = []
        total_weight = 0

        for r in route:
            if ":" not in r:
                click.echo(f"Invalid route format: {r}. Use version:weight", err=True)
                raise click.Abort()
            parts = r.split(":")
            version = int(parts[0])
            weight = int(parts[1])
            total_weight += weight
            routes.append(TrafficRouteDto(version=version, weight=weight))

        if total_weight != 100:
            click.echo(f"Error: Traffic weights must sum to 100 (got {total_weight})", err=True)
            raise click.Abort()

        request = SetTrafficConfigRequest(
            name=name,
            routes=routes,
            shadow_version=shadow
        )

        deployment = await container.get_registry_service().set_traffic_config(request)

        click.echo(f"Set traffic configuration for '{name}':")
        for r in routes:
            click.echo(f"  v{r.version}: {r.weight}%")
        if shadow:
            click.echo(f"  Shadow: v{shadow}")

    except ConfigurationError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    except BlogusError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@registry.command("clear-traffic")
@click.argument("name", type=str)
async def clear_traffic(name: str):
    """Clear traffic configuration (route 100% to latest)."""
    container = get_container()

    try:
        deployment = await container.get_registry_service().clear_traffic_config(name)
        click.echo(f"Cleared traffic configuration for '{name}'")
        click.echo(f"Now routing 100% to version {deployment.version}")

    except ConfigurationError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    except BlogusError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


# ==================== Execution ====================

@registry.command("execute")
@click.argument("name", type=str)
@click.option("--var", "-v", multiple=True, help="Variable in format key=value")
@click.option("--variables", type=str, help="JSON string of variables")
@click.option("--show-stats", is_flag=True, help="Show execution statistics")
async def execute(name: str, var: tuple, variables: Optional[str], show_stats: bool):
    """Execute a deployed prompt.

    For template prompts, provide variables with --var or --variables.
    """
    container = get_container()

    try:
        # Parse variables
        var_dict = {}

        if variables:
            var_dict.update(json.loads(variables))

        for v in var:
            if "=" not in v:
                click.echo(f"Invalid variable format: {v}. Use key=value", err=True)
                raise click.Abort()
            key, value = v.split("=", 1)
            var_dict[key] = value

        request = ExecuteDeploymentRequest(
            name=name,
            variables=var_dict if var_dict else None
        )

        click.echo(f"Executing '{name}'...")
        response = await container.get_registry_service().execute(request)
        result = response.result

        click.echo("\n" + "=" * 60)
        click.echo(result.response)
        click.echo("=" * 60)

        if show_stats:
            click.echo(f"\nVersion: {result.version}")
            click.echo(f"Model: {result.model_used}")
            click.echo(f"Latency: {result.latency_ms:.0f}ms")
            click.echo(f"Tokens: {result.input_tokens} in / {result.output_tokens} out")
            click.echo(f"Est. Cost: ${result.estimated_cost_usd:.6f}")

        if result.shadow_response:
            click.echo("\n[Shadow Response]")
            click.echo("-" * 40)
            click.echo(result.shadow_response)

    except ConfigurationError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    except BlogusError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON in --variables: {e}", err=True)
        raise click.Abort()


# ==================== Metrics ====================

@registry.command("metrics")
@click.argument("name", type=str)
@click.option("--version", "-v", type=int, help="Specific version")
@click.option("--hours", type=int, default=24, help="Period in hours (default: 24)")
async def get_metrics(name: str, version: Optional[int], hours: int):
    """Get execution metrics for a deployment."""
    container = get_container()

    try:
        request = GetMetricsRequest(
            name=name,
            version=version,
            period_hours=hours
        )

        response = await container.get_registry_service().get_metrics(request)
        metrics = response.metrics

        version_str = f"v{metrics.version}" if metrics.version else "all versions"
        click.echo(f"\nMetrics for '{name}' ({version_str}) - last {hours}h:")
        click.echo("=" * 50)
        click.echo(f"Total Executions: {metrics.total_executions}")
        click.echo(f"Success Rate: {metrics.success_rate * 100:.1f}%")
        click.echo(f"Avg Latency: {metrics.avg_latency_ms:.0f}ms")
        click.echo(f"P95 Latency: {metrics.p95_latency_ms:.0f}ms")
        click.echo(f"Total Tokens: {metrics.total_tokens:,}")
        click.echo(f"Total Cost: ${metrics.total_cost_usd:.4f}")

    except BlogusError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@registry.command("compare")
@click.argument("name", type=str)
@click.argument("versions", type=str)
@click.option("--hours", type=int, default=24, help="Period in hours (default: 24)")
async def compare_versions(name: str, versions: str, hours: int):
    """Compare metrics across versions.

    VERSIONS: Comma-separated version numbers (e.g., 1,2,3)
    """
    container = get_container()

    try:
        version_list = [int(v.strip()) for v in versions.split(",")]

        request = CompareVersionsRequest(
            name=name,
            versions=version_list,
            period_hours=hours
        )

        response = await container.get_registry_service().compare_versions(request)

        click.echo(f"\nVersion Comparison for '{name}' - last {hours}h:")
        click.echo("=" * 70)
        click.echo(f"{'Version':<10} {'Executions':<12} {'Success':<10} {'Avg Latency':<12} {'Cost':<10}")
        click.echo("-" * 70)

        for version, metrics in sorted(response.comparisons.items()):
            click.echo(
                f"v{version:<9} {metrics.total_executions:<12} "
                f"{metrics.success_rate * 100:>6.1f}%   "
                f"{metrics.avg_latency_ms:>8.0f}ms   "
                f"${metrics.total_cost_usd:<.4f}"
            )

    except ValueError:
        click.echo("Error: Invalid version format. Use comma-separated integers.", err=True)
        raise click.Abort()
    except BlogusError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


# ==================== Export/Import ====================

@registry.command("export")
@click.argument("name", type=str)
@click.option("--format", "-f", type=click.Choice(["json", "yaml", "markdown"]), default="json",
              help="Export format")
@click.option("--output", "-o", type=click.Path(), help="Output file (default: stdout)")
@click.option("--include-history", is_flag=True, help="Include version history")
async def export_deployment(name: str, format: str, output: Optional[str], include_history: bool):
    """Export a deployment to JSON, YAML, or Markdown."""
    container = get_container()

    try:
        exported = await container.get_registry_service().export_deployment(
            name, format, include_history
        )

        if output:
            with open(output, 'w') as f:
                f.write(exported)
            click.echo(f"Exported '{name}' to {output}")
        else:
            click.echo(exported)

    except ConfigurationError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    except BlogusError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@registry.command("import")
@click.argument("file", type=click.Path(exists=True))
@click.option("--format", "-f", type=click.Choice(["json", "yaml"]), help="Import format (auto-detected if not specified)")
@click.option("--author", "-a", default="import", help="Author for the imported deployment")
async def import_deployment(file: str, format: Optional[str], author: str):
    """Import a deployment from a JSON or YAML file."""
    container = get_container()

    try:
        # Read file
        with open(file, 'r') as f:
            content = f.read()

        # Auto-detect format if not specified
        if not format:
            if file.endswith('.yaml') or file.endswith('.yml'):
                format = 'yaml'
            else:
                format = 'json'

        deployment = await container.get_registry_service().import_deployment(
            content, format, author
        )

        click.echo(f"Imported deployment '{deployment.name}'")
        click.echo(f"  ID: {deployment.id}")
        click.echo(f"  Model: {deployment.model_config.model_id}")

    except ConfigurationError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    except BlogusError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON: {e}", err=True)
        raise click.Abort()


# ==================== Sync Wrappers ====================

def sync_wrapper(func):
    """Create sync wrapper for async function."""
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))
    return wrapper


# Replace async callbacks with sync wrappers
register_deployment.callback = sync_wrapper(register_deployment.callback)
list_deployments.callback = sync_wrapper(list_deployments.callback)
show_deployment.callback = sync_wrapper(show_deployment.callback)
update_content.callback = sync_wrapper(update_content.callback)
update_model.callback = sync_wrapper(update_model.callback)
rollback.callback = sync_wrapper(rollback.callback)
set_status.callback = sync_wrapper(set_status.callback)
delete_deployment.callback = sync_wrapper(delete_deployment.callback)
set_traffic.callback = sync_wrapper(set_traffic.callback)
clear_traffic.callback = sync_wrapper(clear_traffic.callback)
execute.callback = sync_wrapper(execute.callback)
get_metrics.callback = sync_wrapper(get_metrics.callback)
compare_versions.callback = sync_wrapper(compare_versions.callback)
export_deployment.callback = sync_wrapper(export_deployment.callback)
import_deployment.callback = sync_wrapper(import_deployment.callback)
