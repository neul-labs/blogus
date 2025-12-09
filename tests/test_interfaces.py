"""
Tests for interface layer.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

# Skip all tests in this module if fastapi is not installed
pytest.importorskip("fastapi")

from fastapi.testclient import TestClient
from blogus.interfaces.web.main import app
from blogus.interfaces.web.container import get_container
from blogus.application.dto import (
    AnalyzePromptResponse, AnalysisDto, FragmentDto,
    ExecutePromptResponse, CreateTemplateResponse, TemplateDto
)


class TestWebAPI:
    """Test FastAPI web interface."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)

    def teardown_method(self):
        """Clean up test fixtures."""
        # Clear any dependency overrides after each test
        app.dependency_overrides.clear()

    def test_root_endpoint(self):
        """Test root endpoint."""
        response = self.client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Blogus API", "version": "1.0.0"}

    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = self.client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "blogus-api"}

    def test_analyze_prompt_endpoint(self):
        """Test analyze prompt endpoint."""
        # Create mock container and service
        mock_container = MagicMock()
        mock_service = MagicMock()
        mock_container.get_prompt_service.return_value = mock_service

        # Mock the analysis response
        mock_analysis = AnalysisDto(
            prompt_id="test-id",
            goal_alignment=8,
            effectiveness=7,
            suggestions=["Improve clarity"],
            status="completed",
            inferred_goal=None
        )
        mock_response = AnalyzePromptResponse(
            analysis=mock_analysis,
            fragments=[]
        )
        mock_service.analyze_prompt = AsyncMock(return_value=mock_response)

        # Override the dependency
        app.dependency_overrides[get_container] = lambda: mock_container

        # Make the request
        request_data = {
            "prompt_text": "Test prompt",
            "judge_model": "gpt-4",
            "goal": "Test goal"
        }
        response = self.client.post("/api/v1/prompts/analyze", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["analysis"]["goal_alignment"] == 8
        assert data["analysis"]["effectiveness"] == 7

    def test_execute_prompt_endpoint(self):
        """Test execute prompt endpoint."""
        # Create mock container and service
        mock_container = MagicMock()
        mock_service = MagicMock()
        mock_container.get_prompt_service.return_value = mock_service

        # Mock the execution response
        mock_response = ExecutePromptResponse(
            result="Test response",
            model_used="gpt-4",
            duration=1.5
        )
        mock_service.execute_prompt = AsyncMock(return_value=mock_response)

        # Override the dependency
        app.dependency_overrides[get_container] = lambda: mock_container

        # Make the request
        request_data = {
            "prompt_text": "Test prompt",
            "target_model": "gpt-4"
        }
        response = self.client.post("/api/v1/prompts/execute", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "Test response"
        assert data["model_used"] == "gpt-4"
        assert data["duration"] == 1.5

    def test_invalid_request_validation(self):
        """Test request validation."""
        # Test with missing required fields
        response = self.client.post("/api/v1/prompts/analyze", json={})
        assert response.status_code == 422  # Validation error

        # Test with invalid data types
        response = self.client.post("/api/v1/prompts/analyze", json={
            "prompt_text": 123,  # Should be string
            "judge_model": "gpt-4"
        })
        assert response.status_code == 422


class TestCLIInterface:
    """Test CLI interface integration."""

    @patch('blogus.interfaces.cli.main.get_container')
    @pytest.mark.asyncio
    async def test_cli_container_integration(self, mock_get_container):
        """Test that CLI can get container successfully."""
        mock_container = AsyncMock()
        mock_get_container.return_value = mock_container

        # Import and test the get_container function
        from blogus.interfaces.cli.main import get_container
        container = get_container()

        assert container is not None
        mock_get_container.assert_called_once()
