"""
Tests for web API endpoints.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

# Skip all tests if fastapi is not installed
pytest.importorskip("fastapi")

from fastapi.testclient import TestClient
from blogus.application.dto import (
    AnalyzePromptResponse, AnalysisDto, FragmentDto,
    ExecutePromptResponse, PromptDto
)


class TestWebAPIEndpoints:
    """Test FastAPI web interface endpoints."""

    def setup_method(self):
        """Set up test fixtures."""
        # Import here to avoid issues if fastapi not installed
        from blogus.interfaces.web.main import app
        from blogus.interfaces.web.container import get_container

        self.app = app
        self.get_container = get_container
        self.client = TestClient(app)

    def teardown_method(self):
        """Clean up test fixtures."""
        self.app.dependency_overrides.clear()

    def test_root_endpoint(self):
        """Test root endpoint."""
        response = self.client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Blogus API"
        assert "version" in data

    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "blogus-api"

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
            suggestions=["Improve clarity", "Add examples"],
            status="completed",
            inferred_goal="Help users understand code"
        )
        mock_response = AnalyzePromptResponse(
            analysis=mock_analysis,
            fragments=[
                FragmentDto(
                    text="System prompt",
                    fragment_type="instruction",
                    goal_alignment=8,
                    improvement_suggestion="None needed"
                )
            ]
        )
        mock_service.analyze_prompt = AsyncMock(return_value=mock_response)

        # Override the dependency
        self.app.dependency_overrides[self.get_container] = lambda: mock_container

        # Make the request
        request_data = {
            "prompt_text": "Analyze this Python code for bugs",
            "judge_model": "gpt-4o",
            "goal": "Find and explain bugs in code"
        }
        response = self.client.post("/api/v1/prompts/analyze", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["analysis"]["goal_alignment"] == 8
        assert data["analysis"]["effectiveness"] == 7
        assert len(data["analysis"]["suggestions"]) == 2
        assert len(data["fragments"]) == 1

    def test_analyze_prompt_without_goal(self):
        """Test analyze prompt without explicit goal."""
        mock_container = MagicMock()
        mock_service = MagicMock()
        mock_container.get_prompt_service.return_value = mock_service

        mock_analysis = AnalysisDto(
            prompt_id="test-id",
            goal_alignment=7,
            effectiveness=7,
            suggestions=[],
            status="completed",
            inferred_goal="Inferred goal from prompt"
        )
        mock_response = AnalyzePromptResponse(
            analysis=mock_analysis,
            fragments=[]
        )
        mock_service.analyze_prompt = AsyncMock(return_value=mock_response)

        self.app.dependency_overrides[self.get_container] = lambda: mock_container

        request_data = {
            "prompt_text": "Help me write better code",
            "judge_model": "gpt-4o"
            # No goal provided
        }
        response = self.client.post("/api/v1/prompts/analyze", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["analysis"]["inferred_goal"] == "Inferred goal from prompt"

    def test_execute_prompt_endpoint(self):
        """Test execute prompt endpoint."""
        mock_container = MagicMock()
        mock_service = MagicMock()
        mock_container.get_prompt_service.return_value = mock_service

        mock_response = ExecutePromptResponse(
            result="Here is the generated response from the model.",
            model_used="gpt-4o",
            duration=1.234
        )
        mock_service.execute_prompt = AsyncMock(return_value=mock_response)

        self.app.dependency_overrides[self.get_container] = lambda: mock_container

        request_data = {
            "prompt_text": "Write a haiku about programming",
            "target_model": "gpt-4o"
        }
        response = self.client.post("/api/v1/prompts/execute", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "generated response" in data["result"]
        assert data["model_used"] == "gpt-4o"
        assert data["duration"] == 1.234

    def test_execute_prompt_validation_error(self):
        """Test execute prompt with invalid data."""
        response = self.client.post("/api/v1/prompts/execute", json={})

        assert response.status_code == 422  # Validation error

    def test_analyze_prompt_validation_error(self):
        """Test analyze prompt with invalid data types."""
        response = self.client.post("/api/v1/prompts/analyze", json={
            "prompt_text": 123,  # Should be string
            "judge_model": "gpt-4"
        })

        assert response.status_code == 422

    def test_missing_required_fields(self):
        """Test endpoints with missing required fields."""
        # Missing prompt_text
        response = self.client.post("/api/v1/prompts/execute", json={
            "target_model": "gpt-4o"
        })
        assert response.status_code == 422

        # Missing judge_model
        response = self.client.post("/api/v1/prompts/analyze", json={
            "prompt_text": "Test"
        })
        assert response.status_code == 422


class TestWebAPIErrorHandling:
    """Test API error handling."""

    def setup_method(self):
        """Set up test fixtures."""
        from blogus.interfaces.web.main import app
        from blogus.interfaces.web.container import get_container

        self.app = app
        self.get_container = get_container
        self.client = TestClient(app)

    def teardown_method(self):
        """Clean up test fixtures."""
        self.app.dependency_overrides.clear()

    def test_service_error_handling(self):
        """Test that service errors are handled gracefully."""
        mock_container = MagicMock()
        mock_service = MagicMock()
        mock_container.get_prompt_service.return_value = mock_service

        # Make service raise an exception
        mock_service.execute_prompt = AsyncMock(side_effect=Exception("Service error"))

        self.app.dependency_overrides[self.get_container] = lambda: mock_container

        request_data = {
            "prompt_text": "Test prompt",
            "target_model": "gpt-4o"
        }

        response = self.client.post("/api/v1/prompts/execute", json=request_data)

        # Should return 500 or handle error gracefully
        assert response.status_code in [500, 400]

    def test_invalid_json(self):
        """Test handling of invalid JSON."""
        response = self.client.post(
            "/api/v1/prompts/execute",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    def test_content_type_validation(self):
        """Test that correct content type is required."""
        response = self.client.post(
            "/api/v1/prompts/execute",
            content="prompt_text=test&target_model=gpt-4",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        assert response.status_code == 422


class TestWebAPIIntegration:
    """Integration tests for web API."""

    def setup_method(self):
        """Set up test fixtures."""
        from blogus.interfaces.web.main import app
        from blogus.interfaces.web.container import get_container

        self.app = app
        self.get_container = get_container
        self.client = TestClient(app)

    def teardown_method(self):
        """Clean up test fixtures."""
        self.app.dependency_overrides.clear()

    def test_multiple_sequential_requests(self):
        """Test multiple sequential requests."""
        mock_container = MagicMock()
        mock_service = MagicMock()
        mock_container.get_prompt_service.return_value = mock_service

        # Counter for different responses
        call_count = [0]

        async def mock_execute(*args, **kwargs):
            call_count[0] += 1
            return ExecutePromptResponse(
                result=f"Response {call_count[0]}",
                model_used="gpt-4o",
                duration=0.5
            )

        mock_service.execute_prompt = mock_execute

        self.app.dependency_overrides[self.get_container] = lambda: mock_container

        for i in range(3):
            request_data = {
                "prompt_text": f"Test prompt {i}",
                "target_model": "gpt-4o"
            }
            response = self.client.post("/api/v1/prompts/execute", json=request_data)
            assert response.status_code == 200
            data = response.json()
            assert f"Response {i + 1}" in data["result"]

    def test_concurrent_endpoint_access(self):
        """Test that different endpoints can be accessed."""
        # Health check
        response1 = self.client.get("/health")
        assert response1.status_code == 200

        # Root
        response2 = self.client.get("/")
        assert response2.status_code == 200

        # Both should work independently
        assert response1.json()["status"] == "healthy"
        assert response2.json()["message"] == "Blogus API"
