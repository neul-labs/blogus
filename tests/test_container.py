"""
Tests for infrastructure container and dependency injection.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from blogus.infrastructure.config.settings import Settings


class TestSetupObservability:
    """Test setup_observability function."""

    def test_setup_observability_disabled(self):
        """Test that observability is not set up when disabled."""
        from blogus.infrastructure.container import setup_observability

        settings = Settings.default()
        settings.observability.tracing_enabled = False

        with patch('blogus.infrastructure.container.init_tracing') as mock_init:
            setup_observability(settings)

            mock_init.assert_not_called()

    def test_setup_observability_enabled(self):
        """Test that observability is set up when enabled."""
        from blogus.infrastructure.container import setup_observability

        settings = Settings.default()
        settings.observability.tracing_enabled = True
        settings.observability.service_name = "test-service"

        with patch('blogus.infrastructure.container.init_tracing') as mock_init:
            setup_observability(settings)

            mock_init.assert_called_once()
            call_args = mock_init.call_args[0][0]
            assert call_args.service_name == "test-service"
            assert call_args.enabled is True


class TestContainerFactories:
    """Test container factory functions."""

    @pytest.mark.asyncio
    async def test_create_file_registry(self):
        """Test creating file-based registry."""
        from blogus.infrastructure.container import create_registry
        from blogus.infrastructure.storage.file_repositories import FilePromptRegistry

        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings.default()
            settings.storage.data_directory = Path(temp_dir)
            settings.database.backend = "file"

            registry = await create_registry(settings)

            assert registry is not None
            assert isinstance(registry, FilePromptRegistry)

    @pytest.mark.asyncio
    async def test_create_file_metrics_store(self):
        """Test creating file-based metrics store."""
        from blogus.infrastructure.container import create_metrics_store
        from blogus.infrastructure.storage.file_repositories import FileMetricsStore

        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings.default()
            settings.storage.data_directory = Path(temp_dir)
            settings.database.backend = "file"

            store = await create_metrics_store(settings)

            assert store is not None
            assert isinstance(store, FileMetricsStore)

    @pytest.mark.asyncio
    async def test_create_registry_service(self):
        """Test creating a fully configured registry service."""
        from blogus.infrastructure.container import create_registry_service

        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings.default()
            settings.storage.data_directory = Path(temp_dir)
            settings.database.backend = "file"
            settings.observability.tracing_enabled = False

            service = await create_registry_service(settings)

            assert service is not None
            assert hasattr(service, '_registry')
            assert hasattr(service, '_metrics_store')
            assert hasattr(service, '_llm_provider')


class TestShutdown:
    """Test shutdown function."""

    @pytest.mark.asyncio
    async def test_shutdown_graceful(self):
        """Test shutdown handles missing resources gracefully."""
        from blogus.infrastructure.container import shutdown

        # Should not raise even if resources weren't initialized
        await shutdown()
