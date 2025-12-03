"""
Tests for the Prompt Registry functionality.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from blogus.domain.models.registry import (
    PromptDeployment, DeploymentId, PromptName, DeploymentStatus,
    ModelConfig, ModelParameters, VersionRecord, TrafficConfig, TrafficRoute,
    ExecutionMetrics, AggregatedMetrics
)
from blogus.infrastructure.storage.file_repositories import (
    FilePromptRegistry, FileMetricsStore
)


class TestPromptDeploymentModel:
    """Test PromptDeployment domain model."""

    def test_create_deployment(self):
        """Test creating a basic deployment."""
        deployment = PromptDeployment(
            id=DeploymentId.generate(),
            name=PromptName("test-prompt"),
            description="A test prompt",
            content="Hello, this is a test prompt."
        )

        assert deployment.name.value == "test-prompt"
        assert deployment.version == 1
        assert deployment.status == DeploymentStatus.ACTIVE
        assert not deployment.is_template

    def test_deployment_with_template_variables(self):
        """Test deployment with template variables."""
        deployment = PromptDeployment(
            id=DeploymentId.generate(),
            name=PromptName("greeting"),
            description="A greeting prompt",
            content="Hello {{name}}, welcome to {{place}}!"
        )

        assert deployment.is_template
        assert set(deployment.template_variables) == {"name", "place"}

    def test_render_template(self):
        """Test rendering template variables."""
        deployment = PromptDeployment(
            id=DeploymentId.generate(),
            name=PromptName("greeting"),
            description="A greeting prompt",
            content="Hello {{name}}, welcome to {{place}}!"
        )

        rendered = deployment.render({"name": "Alice", "place": "Wonderland"})
        assert rendered == "Hello Alice, welcome to Wonderland!"

    def test_render_template_missing_variable(self):
        """Test rendering with missing variable raises error."""
        deployment = PromptDeployment(
            id=DeploymentId.generate(),
            name=PromptName("greeting"),
            description="A greeting prompt",
            content="Hello {{name}}, welcome to {{place}}!"
        )

        with pytest.raises(ValueError, match="Unresolved template variables"):
            deployment.render({"name": "Alice"})

    def test_update_content_creates_version(self):
        """Test that updating content creates a new version."""
        deployment = PromptDeployment(
            id=DeploymentId.generate(),
            name=PromptName("test-prompt"),
            description="A test prompt",
            content="Version 1 content"
        )

        assert deployment.version == 1
        assert len(deployment.version_history) == 0

        deployment.update_content("Version 2 content", "test-author", "Updated content")

        assert deployment.version == 2
        assert deployment.content == "Version 2 content"
        assert len(deployment.version_history) == 1
        assert deployment.version_history[0].version == 1
        assert deployment.version_history[0].content == "Version 1 content"

    def test_rollback_to_previous_version(self):
        """Test rolling back to a previous version."""
        deployment = PromptDeployment(
            id=DeploymentId.generate(),
            name=PromptName("test-prompt"),
            description="A test prompt",
            content="Version 1 content"
        )

        deployment.update_content("Version 2 content", "test-author")
        deployment.update_content("Version 3 content", "test-author")

        assert deployment.version == 3
        assert deployment.content == "Version 3 content"

        deployment.rollback_to_version(1, "test-author")

        assert deployment.version == 4
        assert deployment.content == "Version 1 content"


class TestPromptName:
    """Test PromptName value object validation."""

    def test_valid_prompt_name(self):
        """Test valid prompt names."""
        valid_names = [
            "test",
            "test-prompt",
            "my-test-prompt",
            "a",
            "a1",
            "test123",
            "customer-support-v2"
        ]

        for name in valid_names:
            pn = PromptName(name)
            assert pn.value == name

    def test_invalid_prompt_name_uppercase(self):
        """Test that uppercase is rejected."""
        with pytest.raises(ValueError):
            PromptName("Test")

    def test_invalid_prompt_name_starts_with_hyphen(self):
        """Test that starting with hyphen is rejected."""
        with pytest.raises(ValueError):
            PromptName("-test")

    def test_invalid_prompt_name_ends_with_hyphen(self):
        """Test that ending with hyphen is rejected."""
        with pytest.raises(ValueError):
            PromptName("test-")

    def test_invalid_prompt_name_special_chars(self):
        """Test that special characters are rejected."""
        with pytest.raises(ValueError):
            PromptName("test_prompt")


class TestModelParameters:
    """Test ModelParameters validation."""

    def test_valid_parameters(self):
        """Test valid model parameters."""
        params = ModelParameters(
            temperature=0.7,
            max_tokens=1000,
            top_p=0.9
        )

        assert params.temperature == 0.7
        assert params.max_tokens == 1000
        assert params.top_p == 0.9

    def test_invalid_temperature(self):
        """Test invalid temperature is rejected."""
        with pytest.raises(ValueError):
            ModelParameters(temperature=3.0)

    def test_invalid_max_tokens(self):
        """Test invalid max_tokens is rejected."""
        with pytest.raises(ValueError):
            ModelParameters(max_tokens=0)

    def test_invalid_top_p(self):
        """Test invalid top_p is rejected."""
        with pytest.raises(ValueError):
            ModelParameters(top_p=1.5)


class TestTrafficConfig:
    """Test TrafficConfig validation and routing."""

    def test_valid_traffic_config(self):
        """Test valid traffic configuration."""
        config = TrafficConfig(
            routes=[
                TrafficRoute(version=1, weight=80),
                TrafficRoute(version=2, weight=20)
            ]
        )

        assert len(config.routes) == 2

    def test_invalid_traffic_weights(self):
        """Test that invalid weights are rejected."""
        with pytest.raises(ValueError, match="sum to 100"):
            TrafficConfig(
                routes=[
                    TrafficRoute(version=1, weight=60),
                    TrafficRoute(version=2, weight=20)
                ]
            )

    def test_select_route(self):
        """Test route selection based on random value."""
        config = TrafficConfig(
            routes=[
                TrafficRoute(version=1, weight=80),
                TrafficRoute(version=2, weight=20)
            ]
        )

        # 0.0 should select first route
        route = config.select_route(0.0)
        assert route.version == 1

        # 0.5 should select first route (under 80%)
        route = config.select_route(0.5)
        assert route.version == 1

        # 0.9 should select second route (over 80%)
        route = config.select_route(0.9)
        assert route.version == 2


class TestFilePromptRegistry:
    """Test FilePromptRegistry implementation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.registry = FilePromptRegistry(Path(self.temp_dir))

    def test_register_and_get_deployment(self):
        """Test registering and retrieving a deployment."""
        deployment = PromptDeployment(
            id=DeploymentId.generate(),
            name=PromptName("test-prompt"),
            description="A test prompt",
            content="Test content"
        )

        self.registry.register(deployment)

        retrieved = self.registry.get_by_name(PromptName("test-prompt"))
        assert retrieved is not None
        assert retrieved.name.value == "test-prompt"
        assert retrieved.content == "Test content"

    def test_register_duplicate_name_fails(self):
        """Test that registering duplicate name fails."""
        deployment1 = PromptDeployment(
            id=DeploymentId.generate(),
            name=PromptName("test-prompt"),
            description="First",
            content="Content 1"
        )

        deployment2 = PromptDeployment(
            id=DeploymentId.generate(),
            name=PromptName("test-prompt"),
            description="Second",
            content="Content 2"
        )

        self.registry.register(deployment1)

        with pytest.raises(Exception, match="already exists"):
            self.registry.register(deployment2)

    def test_list_all_deployments(self):
        """Test listing all deployments."""
        for i in range(3):
            deployment = PromptDeployment(
                id=DeploymentId.generate(),
                name=PromptName(f"prompt-{i}"),
                description=f"Prompt {i}",
                content=f"Content {i}"
            )
            self.registry.register(deployment)

        deployments = self.registry.list_all()
        assert len(deployments) == 3

    def test_search_by_category(self):
        """Test searching by category."""
        deployment1 = PromptDeployment(
            id=DeploymentId.generate(),
            name=PromptName("prompt-1"),
            description="Prompt 1",
            content="Content 1",
            category="support"
        )

        deployment2 = PromptDeployment(
            id=DeploymentId.generate(),
            name=PromptName("prompt-2"),
            description="Prompt 2",
            content="Content 2",
            category="marketing"
        )

        self.registry.register(deployment1)
        self.registry.register(deployment2)

        results = self.registry.search(category="support")
        assert len(results) == 1
        assert results[0].name.value == "prompt-1"

    def test_update_deployment(self):
        """Test updating a deployment."""
        deployment = PromptDeployment(
            id=DeploymentId.generate(),
            name=PromptName("test-prompt"),
            description="Original",
            content="Original content"
        )

        self.registry.register(deployment)

        deployment.update_content("Updated content", "test-author")
        self.registry.update(deployment)

        retrieved = self.registry.get_by_name(PromptName("test-prompt"))
        assert retrieved.content == "Updated content"
        assert retrieved.version == 2

    def test_delete_deployment(self):
        """Test deleting a deployment."""
        deployment = PromptDeployment(
            id=DeploymentId.generate(),
            name=PromptName("test-prompt"),
            description="Test",
            content="Content"
        )

        self.registry.register(deployment)
        assert self.registry.exists(PromptName("test-prompt"))

        self.registry.delete(PromptName("test-prompt"))
        assert not self.registry.exists(PromptName("test-prompt"))


class TestFileMetricsStore:
    """Test FileMetricsStore implementation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.store = FileMetricsStore(Path(self.temp_dir))

    def test_record_and_get_metrics(self):
        """Test recording and retrieving metrics."""
        metrics = ExecutionMetrics(
            prompt_name="test-prompt",
            version=1,
            model_used="gpt-4o",
            latency_ms=250.0,
            input_tokens=100,
            output_tokens=200,
            total_tokens=300,
            estimated_cost_usd=0.005,
            success=True,
            executed_at=datetime.now()
        )

        self.store.record(metrics)

        recent = self.store.get_recent("test-prompt", limit=10)
        assert len(recent) == 1
        assert recent[0].prompt_name == "test-prompt"

    def test_get_aggregated_metrics(self):
        """Test aggregated metrics calculation."""
        for i in range(5):
            metrics = ExecutionMetrics(
                prompt_name="test-prompt",
                version=1,
                model_used="gpt-4o",
                latency_ms=100.0 + i * 10,
                input_tokens=100,
                output_tokens=200,
                total_tokens=300,
                estimated_cost_usd=0.005,
                success=True,
                executed_at=datetime.now()
            )
            self.store.record(metrics)

        aggregated = self.store.get_aggregated("test-prompt", period_hours=1)

        assert aggregated.total_executions == 5
        assert aggregated.successful_executions == 5
        assert aggregated.failed_executions == 0
        assert aggregated.total_tokens == 1500

    def test_compare_versions(self):
        """Test comparing metrics across versions."""
        for version in [1, 2]:
            for i in range(3):
                metrics = ExecutionMetrics(
                    prompt_name="test-prompt",
                    version=version,
                    model_used="gpt-4o",
                    latency_ms=100.0 * version,
                    input_tokens=100,
                    output_tokens=200,
                    total_tokens=300,
                    estimated_cost_usd=0.005,
                    success=True,
                    executed_at=datetime.now()
                )
                self.store.record(metrics)

        comparison = self.store.compare_versions("test-prompt", [1, 2], period_hours=1)

        assert 1 in comparison
        assert 2 in comparison
        assert comparison[1].total_executions == 3
        assert comparison[2].total_executions == 3
