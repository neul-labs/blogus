"""
Tests for interface layer.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from blogus.interfaces.web.main import app
from blogus.application.dto import AnalyzePromptResponse, AnalysisDto, FragmentDto


class TestWebAPI:
    """Test FastAPI web interface."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)

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

    @patch('blogus.interfaces.web.container.get_container')
    def test_analyze_prompt_endpoint(self, mock_get_container):
        """Test analyze prompt endpoint."""
        # Mock the container and service
        mock_container = AsyncMock()
        mock_service = AsyncMock()
        mock_get_container.return_value = mock_container
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
        mock_service.analyze_prompt.return_value = mock_response

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

    @patch('blogus.interfaces.web.container.get_container')
    def test_execute_prompt_endpoint(self, mock_get_container):
        """Test execute prompt endpoint."""
        # Mock the container and service
        mock_container = AsyncMock()
        mock_service = AsyncMock()
        mock_get_container.return_value = mock_container
        mock_container.get_prompt_service.return_value = mock_service

        # Mock the execution response
        from blogus.application.dto import ExecutePromptResponse
        mock_response = ExecutePromptResponse(
            result="Test response",
            model_used="gpt-4",
            duration=1.5
        )
        mock_service.execute_prompt.return_value = mock_response

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

    @patch('blogus.interfaces.web.container.get_container')
    def test_create_template_endpoint(self, mock_get_container):
        """Test create template endpoint."""
        # Mock the container and service
        mock_container = AsyncMock()
        mock_service = AsyncMock()
        mock_get_container.return_value = mock_container
        mock_container.get_template_service.return_value = mock_service

        # Mock the template response
        from blogus.application.dto import CreateTemplateResponse, TemplateDto
        mock_template = TemplateDto(
            id="test-template",
            name="Test Template",
            description="A test template",
            content="Hello {{name}}",
            category="greeting",
            tags=["test"],
            author="test-author",
            version="1.0.0",
            variables=["name"],
            usage_count=0
        )
        mock_response = CreateTemplateResponse(template=mock_template)
        mock_service.create_template.return_value = mock_response

        # Make the request
        request_data = {
            "template_id": "test-template",
            "name": "Test Template",
            "description": "A test template",
            "content": "Hello {{name}}",
            "category": "greeting",
            "tags": ["test"],
            "author": "test-author"
        }
        response = self.client.post("/api/v1/templates/", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["template"]["id"] == "test-template"
        assert data["template"]["name"] == "Test Template"

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