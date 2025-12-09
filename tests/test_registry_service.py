"""
Tests for registry service.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from blogus.application.services.registry_service import RegistryService, MODEL_COSTS
from blogus.application.dto import (
    RegisterDeploymentRequest, UpdateDeploymentContentRequest,
    UpdateDeploymentModelRequest, SetTrafficConfigRequest,
    ExecuteDeploymentRequest, GetMetricsRequest, RollbackDeploymentRequest,
    TrafficRouteDto
)
from blogus.domain.models.registry import (
    PromptDeployment, DeploymentId, PromptName, DeploymentStatus,
    ModelConfig, ModelParameters, VersionRecord, TrafficConfig, TrafficRoute,
    ExecutionMetrics, AggregatedMetrics
)
from blogus.shared.exceptions import ConfigurationError


class TestRegistryServiceDeploymentManagement:
    """Test RegistryService deployment management."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_registry = MagicMock()
        self.mock_metrics_store = MagicMock()
        self.mock_llm_provider = MagicMock()

        self.service = RegistryService(
            registry=self.mock_registry,
            metrics_store=self.mock_metrics_store,
            llm_provider=self.mock_llm_provider
        )

    @pytest.mark.asyncio
    async def test_register_deployment(self):
        """Test registering a new deployment."""
        request = RegisterDeploymentRequest(
            name="test-prompt",
            description="A test prompt",
            content="You are a helpful assistant",
            model_id="gpt-4o",
            goal="Help users",
            temperature=0.7,
            max_tokens=1000,
            top_p=1.0,
            category="general",
            tags=["test"],
            author="test-author"
        )

        # Mock the registry to return the deployment
        def mock_register(deployment):
            return deployment

        self.mock_registry.register = mock_register

        response = await self.service.register_deployment(request)

        assert response.deployment is not None
        assert response.deployment.name == "test-prompt"
        assert response.deployment.description == "A test prompt"

    @pytest.mark.asyncio
    async def test_get_deployment(self):
        """Test getting a deployment by name."""
        mock_deployment = PromptDeployment(
            id=DeploymentId.generate(),
            name=PromptName("test-prompt"),
            description="Test",
            content="Content",
            model_config=ModelConfig(
                model_id="gpt-4o",
                parameters=ModelParameters()
            )
        )

        self.mock_registry.get_by_name.return_value = mock_deployment

        result = await self.service.get_deployment("test-prompt")

        assert result is not None
        assert result.name == "test-prompt"

    @pytest.mark.asyncio
    async def test_get_deployment_not_found(self):
        """Test getting a non-existent deployment."""
        self.mock_registry.get_by_name.return_value = None

        result = await self.service.get_deployment("non-existent")

        assert result is None

    @pytest.mark.asyncio
    async def test_list_deployments(self):
        """Test listing deployments."""
        mock_deployments = [
            PromptDeployment(
                id=DeploymentId.generate(),
                name=PromptName("prompt-1"),
                description="First prompt",
                content="Content 1",
                model_config=ModelConfig(model_id="gpt-4o", parameters=ModelParameters())
            ),
            PromptDeployment(
                id=DeploymentId.generate(),
                name=PromptName("prompt-2"),
                description="Second prompt",
                content="Content 2",
                model_config=ModelConfig(model_id="gpt-4o", parameters=ModelParameters())
            )
        ]

        self.mock_registry.list_all.return_value = mock_deployments

        result = await self.service.list_deployments(limit=10, offset=0)

        assert len(result) == 2
        assert result[0].name == "prompt-1"
        assert result[1].name == "prompt-2"

    @pytest.mark.asyncio
    async def test_list_deployments_with_status_filter(self):
        """Test listing deployments with status filter."""
        mock_deployments = [
            PromptDeployment(
                id=DeploymentId.generate(),
                name=PromptName("active-prompt"),
                description="Active",
                content="Content",
                model_config=ModelConfig(model_id="gpt-4o", parameters=ModelParameters()),
                status=DeploymentStatus.ACTIVE
            )
        ]

        self.mock_registry.list_all.return_value = mock_deployments

        result = await self.service.list_deployments(status="active")

        assert len(result) == 1
        self.mock_registry.list_all.assert_called_with(100, 0, DeploymentStatus.ACTIVE)

    @pytest.mark.asyncio
    async def test_search_deployments(self):
        """Test searching deployments."""
        mock_deployments = [
            PromptDeployment(
                id=DeploymentId.generate(),
                name=PromptName("code-review"),
                description="Reviews code",
                content="Content",
                model_config=ModelConfig(model_id="gpt-4o", parameters=ModelParameters()),
                category="development"
            )
        ]

        self.mock_registry.search.return_value = mock_deployments

        result = await self.service.search_deployments(
            query="code",
            category="development"
        )

        assert len(result) == 1
        assert result[0].name == "code-review"

    @pytest.mark.asyncio
    async def test_update_content(self):
        """Test updating deployment content."""
        mock_deployment = PromptDeployment(
            id=DeploymentId.generate(),
            name=PromptName("test-prompt"),
            description="Test",
            content="Original content",
            model_config=ModelConfig(model_id="gpt-4o", parameters=ModelParameters())
        )

        self.mock_registry.get_by_name.return_value = mock_deployment
        self.mock_registry.update.return_value = mock_deployment

        request = UpdateDeploymentContentRequest(
            name="test-prompt",
            new_content="Updated content",
            author="updater",
            change_summary="Updated the content"
        )

        result = await self.service.update_content(request)

        assert result is not None
        self.mock_registry.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_content_not_found(self):
        """Test updating content for non-existent deployment."""
        self.mock_registry.get_by_name.return_value = None

        request = UpdateDeploymentContentRequest(
            name="non-existent",
            new_content="Content",
            author="author"
        )

        with pytest.raises(ConfigurationError, match="not found"):
            await self.service.update_content(request)

    @pytest.mark.asyncio
    async def test_update_model_config(self):
        """Test updating model configuration."""
        mock_deployment = PromptDeployment(
            id=DeploymentId.generate(),
            name=PromptName("test-prompt"),
            description="Test",
            content="Content",
            model_config=ModelConfig(
                model_id="gpt-3.5-turbo",
                parameters=ModelParameters(temperature=0.5)
            )
        )

        self.mock_registry.get_by_name.return_value = mock_deployment
        self.mock_registry.update.return_value = mock_deployment

        request = UpdateDeploymentModelRequest(
            name="test-prompt",
            model_id="gpt-4o",
            author="updater",
            temperature=0.8
        )

        result = await self.service.update_model_config(request)

        assert result is not None
        self.mock_registry.update.assert_called_once()


class TestRegistryServiceTrafficConfig:
    """Test RegistryService traffic configuration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_registry = MagicMock()
        self.mock_metrics_store = MagicMock()
        self.mock_llm_provider = MagicMock()

        self.service = RegistryService(
            registry=self.mock_registry,
            metrics_store=self.mock_metrics_store,
            llm_provider=self.mock_llm_provider
        )

    @pytest.mark.asyncio
    async def test_set_traffic_config(self):
        """Test setting traffic configuration."""
        mock_deployment = PromptDeployment(
            id=DeploymentId.generate(),
            name=PromptName("test-prompt"),
            description="Test",
            content="Content",
            model_config=ModelConfig(model_id="gpt-4o", parameters=ModelParameters()),
            version=2
        )

        self.mock_registry.get_by_name.return_value = mock_deployment
        self.mock_registry.update.return_value = mock_deployment

        request = SetTrafficConfigRequest(
            name="test-prompt",
            routes=[
                TrafficRouteDto(version=1, weight=30),
                TrafficRouteDto(version=2, weight=70)
            ]
        )

        result = await self.service.set_traffic_config(request)

        assert result is not None
        self.mock_registry.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_traffic_config_not_found(self):
        """Test setting traffic config for non-existent deployment."""
        self.mock_registry.get_by_name.return_value = None

        request = SetTrafficConfigRequest(
            name="non-existent",
            routes=[TrafficRouteDto(version=1, weight=100)]
        )

        with pytest.raises(ConfigurationError, match="not found"):
            await self.service.set_traffic_config(request)


class TestRegistryServiceMetrics:
    """Test RegistryService metrics operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_registry = MagicMock()
        self.mock_metrics_store = MagicMock()
        self.mock_llm_provider = MagicMock()

        self.service = RegistryService(
            registry=self.mock_registry,
            metrics_store=self.mock_metrics_store,
            llm_provider=self.mock_llm_provider
        )

    @pytest.mark.asyncio
    async def test_get_metrics(self):
        """Test getting metrics for a deployment."""
        mock_metrics = AggregatedMetrics(
            prompt_name="test-prompt",
            version=1,
            total_executions=100,
            successful_executions=95,
            failed_executions=5,
            avg_latency_ms=150.0,
            p50_latency_ms=120.0,
            p95_latency_ms=300.0,
            p99_latency_ms=500.0,
            total_tokens=50000,
            total_cost_usd=0.25,
            period_start=datetime.now(),
            period_end=datetime.now()
        )

        self.mock_metrics_store.get_aggregated.return_value = mock_metrics

        request = GetMetricsRequest(
            name="test-prompt",
            version=1,
            period_hours=24
        )

        response = await self.service.get_metrics(request)

        assert response.metrics.prompt_name == "test-prompt"
        assert response.metrics.total_executions == 100
        assert response.metrics.success_rate == 0.95


class TestModelCosts:
    """Test model cost calculations."""

    def test_model_costs_defined(self):
        """Test that common models have costs defined."""
        assert "gpt-4o" in MODEL_COSTS
        assert "gpt-4o-mini" in MODEL_COSTS
        assert "claude-3-5-sonnet-20241022" in MODEL_COSTS

    def test_model_cost_structure(self):
        """Test model cost structure."""
        for model, costs in MODEL_COSTS.items():
            assert "input" in costs
            assert "output" in costs
            assert costs["input"] > 0
            assert costs["output"] > 0

    def test_gpt4o_mini_cheaper_than_gpt4o(self):
        """Test that GPT-4o-mini is cheaper than GPT-4o."""
        assert MODEL_COSTS["gpt-4o-mini"]["input"] < MODEL_COSTS["gpt-4o"]["input"]
        assert MODEL_COSTS["gpt-4o-mini"]["output"] < MODEL_COSTS["gpt-4o"]["output"]


class TestRegistryServiceDTOConversion:
    """Test DTO conversion in RegistryService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_registry = MagicMock()
        self.mock_metrics_store = MagicMock()
        self.mock_llm_provider = MagicMock()

        self.service = RegistryService(
            registry=self.mock_registry,
            metrics_store=self.mock_metrics_store,
            llm_provider=self.mock_llm_provider
        )

    def test_to_deployment_dto(self):
        """Test conversion to DeploymentDto."""
        deployment = PromptDeployment(
            id=DeploymentId.generate(),
            name=PromptName("test-prompt"),
            description="Test description",
            content="Hello {{name}}",
            goal="Greet user",
            model_config=ModelConfig(
                model_id="gpt-4o",
                parameters=ModelParameters(temperature=0.7, max_tokens=500)
            ),
            tags={"test", "greeting"},
            category="general",
            author="tester",
            version=2
        )

        dto = self.service._to_deployment_dto(deployment)

        assert dto.name == "test-prompt"
        assert dto.description == "Test description"
        assert dto.goal == "Greet user"
        assert dto.is_template is True
        assert "name" in dto.template_variables
        assert dto.version == 2
        assert dto.model_config.model_id == "gpt-4o"

    def test_to_deployment_summary_dto(self):
        """Test conversion to DeploymentSummaryDto."""
        deployment = PromptDeployment(
            id=DeploymentId.generate(),
            name=PromptName("test-prompt"),
            description="Test description",
            content="Plain content",
            model_config=ModelConfig(
                model_id="gpt-4o",
                parameters=ModelParameters()
            ),
            tags={"test"},
            category="general",
            author="tester",
            status=DeploymentStatus.ACTIVE
        )

        dto = self.service._to_deployment_summary_dto(deployment)

        assert dto.name == "test-prompt"
        assert dto.status == "active"
        assert dto.is_template is False
        assert dto.model_id == "gpt-4o"
