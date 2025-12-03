"""
Dependency injection container for infrastructure components.

This module provides factory functions to create repository and service
instances based on configuration settings.
"""

from typing import Optional

from .config.settings import Settings, get_settings
from .observability import TracingConfig, init_tracing
from ..domain.models.registry import PromptRegistry, MetricsStore


async def create_registry(settings: Optional[Settings] = None) -> PromptRegistry:
    """
    Create a PromptRegistry instance based on configuration.

    Args:
        settings: Optional settings override. Uses global settings if not provided.

    Returns:
        PromptRegistry implementation (file-based or database-backed)
    """
    if settings is None:
        settings = get_settings()

    if settings.database.backend == "database":
        from .database import init_db
        from .database.repositories import TortoisePromptRegistry

        # Initialize database connection
        await init_db()
        return TortoisePromptRegistry()
    else:
        from .storage.file_repositories import FilePromptRegistry

        return FilePromptRegistry(settings.storage.data_directory)


async def create_metrics_store(settings: Optional[Settings] = None) -> MetricsStore:
    """
    Create a MetricsStore instance based on configuration.

    Args:
        settings: Optional settings override. Uses global settings if not provided.

    Returns:
        MetricsStore implementation (file-based or database-backed)
    """
    if settings is None:
        settings = get_settings()

    if settings.database.backend == "database":
        from .database import init_db
        from .database.repositories import TortoiseMetricsStore

        # Initialize database connection
        await init_db()
        return TortoiseMetricsStore()
    else:
        from .storage.file_repositories import FileMetricsStore

        return FileMetricsStore(settings.storage.data_directory)


def setup_observability(settings: Optional[Settings] = None) -> None:
    """
    Setup observability (tracing) based on configuration.

    Args:
        settings: Optional settings override. Uses global settings if not provided.
    """
    if settings is None:
        settings = get_settings()

    if settings.observability.tracing_enabled:
        config = TracingConfig(
            service_name=settings.observability.service_name,
            service_version=settings.observability.service_version,
            environment=settings.observability.environment,
            otlp_endpoint=settings.observability.otlp_endpoint,
            console_export=settings.observability.console_export,
            enabled=True
        )
        init_tracing(config)


async def create_registry_service(settings: Optional[Settings] = None):
    """
    Create a fully configured RegistryService instance.

    Args:
        settings: Optional settings override. Uses global settings if not provided.

    Returns:
        Configured RegistryService instance
    """
    from ..application.services.registry_service import RegistryService
    from .llm.litellm_provider import LiteLLMProvider

    if settings is None:
        settings = get_settings()

    # Setup observability
    setup_observability(settings)

    # Create dependencies
    registry = await create_registry(settings)
    metrics_store = await create_metrics_store(settings)
    llm_provider = LiteLLMProvider(max_retries=settings.llm.max_retries)

    return RegistryService(
        registry=registry,
        metrics_store=metrics_store,
        llm_provider=llm_provider
    )


async def create_instrumented_executor(settings: Optional[Settings] = None):
    """
    Create an InstrumentedExecutor for traced prompt execution.

    Args:
        settings: Optional settings override. Uses global settings if not provided.

    Returns:
        Configured InstrumentedExecutor instance
    """
    from .observability import InstrumentedExecutor

    if settings is None:
        settings = get_settings()

    # Setup observability first
    setup_observability(settings)

    # Create dependencies
    registry = await create_registry(settings)
    metrics_store = await create_metrics_store(settings)

    return InstrumentedExecutor(
        registry=registry,
        metrics_store=metrics_store
    )


async def shutdown():
    """Shutdown all infrastructure components."""
    from .database import close_db
    from .observability import shutdown_tracing

    # Close database connections
    try:
        await close_db()
    except Exception:
        pass  # Database may not have been initialized

    # Shutdown tracing
    shutdown_tracing()
