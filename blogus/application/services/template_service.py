"""
Application service for template operations.
"""

from typing import List, Optional, Dict, Set
from ..dto import (
    TemplateDto,
    CreateTemplateRequest, CreateTemplateResponse,
    RenderTemplateRequest, RenderTemplateResponse
)
from ...domain.models.prompt import TemplateRepository
from ...domain.services.template_manager import TemplateManager


class TemplateService:
    """Application service for template operations."""

    def __init__(self, template_repository: TemplateRepository):
        self._template_manager = TemplateManager(template_repository)

    async def create_template(self, request: CreateTemplateRequest) -> CreateTemplateResponse:
        """
        Create a new template.

        Args:
            request: Template creation request

        Returns:
            CreateTemplateResponse: Created template
        """
        tags = set(request.tags) if request.tags else set()

        template = self._template_manager.create_template(
            template_id=request.template_id,
            name=request.name,
            description=request.description,
            template_content=request.content,
            category=request.category,
            tags=tags,
            author=request.author
        )

        return CreateTemplateResponse(
            template=self._to_template_dto(template)
        )

    async def get_template(self, template_id: str) -> Optional[TemplateDto]:
        """
        Get a template by ID.

        Args:
            template_id: Template identifier

        Returns:
            Optional[TemplateDto]: Template if found
        """
        template = self._template_manager.get_template(template_id)
        return self._to_template_dto(template) if template else None

    async def list_templates(self, category: Optional[str] = None,
                           tag: Optional[str] = None) -> List[TemplateDto]:
        """
        List templates with optional filtering.

        Args:
            category: Filter by category
            tag: Filter by tag

        Returns:
            List[TemplateDto]: Filtered templates
        """
        templates = self._template_manager.list_templates(category, tag)
        return [self._to_template_dto(template) for template in templates]

    async def update_template(self, template_id: str, **updates) -> TemplateDto:
        """
        Update an existing template.

        Args:
            template_id: Template identifier
            **updates: Fields to update

        Returns:
            TemplateDto: Updated template
        """
        template = self._template_manager.update_template(template_id, **updates)
        return self._to_template_dto(template)

    async def delete_template(self, template_id: str) -> bool:
        """
        Delete a template.

        Args:
            template_id: Template identifier

        Returns:
            bool: True if deleted, False if not found
        """
        return self._template_manager.delete_template(template_id)

    async def render_template(self, request: RenderTemplateRequest) -> RenderTemplateResponse:
        """
        Render a template with variables.

        Args:
            request: Render request

        Returns:
            RenderTemplateResponse: Rendered content
        """
        rendered_content = self._template_manager.render_template(
            request.template_id,
            request.variables
        )

        return RenderTemplateResponse(
            rendered_content=rendered_content
        )

    async def get_categories(self) -> List[str]:
        """Get all template categories."""
        return self._template_manager.get_categories()

    async def get_tags(self) -> List[str]:
        """Get all template tags."""
        return self._template_manager.get_tags()

    async def validate_template_content(self, content: str) -> List[str]:
        """
        Validate template content.

        Args:
            content: Template content

        Returns:
            List[str]: Validation issues
        """
        return self._template_manager.validate_template_content(content)

    def _to_template_dto(self, template) -> TemplateDto:
        """Convert domain template to DTO."""
        return TemplateDto(
            id=template.id.value,
            name=template.name,
            description=template.description,
            content=template.content.template,
            category=template.category,
            tags=list(template.tags),
            author=template.author,
            version=template.version,
            variables=list(template.variables),
            usage_count=template.usage_count,
            created_at=template.created_at,
            updated_at=template.updated_at
        )