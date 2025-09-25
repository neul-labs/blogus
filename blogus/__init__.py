"""
Blogus: A comprehensive library for crafting, analyzing, and perfecting AI prompts.

This package provides tools for:
- Prompt analysis and optimization
- Test case generation
- Multi-model prompt execution
- Template management with variable substitution
- Clean architecture with proper abstractions
- CLI and web interfaces
- REST API for integration
"""

__version__ = "0.2.0"
__author__ = "Dipankar Sarkar"
__email__ = "me@dipankar.name"

# Core domain models
from .domain.models.prompt import Prompt, PromptText, Goal
from .domain.models.template import PromptTemplate, TemplateContent

# Application DTOs
from .application.dto import (
    AnalyzePromptRequest,
    AnalyzePromptResponse,
    ExecutePromptRequest,
    ExecutePromptResponse,
    GenerateTestRequest,
    GenerateTestResponse,
    CreateTemplateRequest,
    CreateTemplateResponse,
    RenderTemplateRequest,
    RenderTemplateResponse
)

# Shared exceptions
from .shared.exceptions import (
    BlogusError,
    ValidationError,
    ResourceNotFoundError
)

# Configuration
from .infrastructure.config.settings import get_settings

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",

    # Domain models
    "Prompt",
    "PromptText",
    "Goal",
    "PromptTemplate",
    "TemplateContent",

    # Application DTOs
    "AnalyzePromptRequest",
    "AnalyzePromptResponse",
    "ExecutePromptRequest",
    "ExecutePromptResponse",
    "GenerateTestRequest",
    "GenerateTestResponse",
    "CreateTemplateRequest",
    "CreateTemplateResponse",
    "RenderTemplateRequest",
    "RenderTemplateResponse",

    # Exceptions
    "BlogusError",
    "ValidationError",
    "ResourceNotFoundError",

    # Configuration
    "get_settings"
]