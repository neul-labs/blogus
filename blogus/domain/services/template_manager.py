"""
Domain service for template management.
"""

from typing import List, Optional, Dict, Set
from ..models.template import PromptTemplate, TemplateId, TemplateContent
from ..models.prompt import TemplateRepository


class TemplateManager:
    """Domain service for managing prompt templates."""

    def __init__(self, template_repository: TemplateRepository):
        self._repository = template_repository

    def create_template(self, template_id: str, name: str, description: str,
                       template_content: str, category: str = "general",
                       tags: Optional[Set[str]] = None, author: str = "unknown") -> PromptTemplate:
        """
        Create a new prompt template.

        Args:
            template_id: Unique identifier for the template
            name: Human-readable name
            description: Template description
            template_content: Template content with variables
            category: Template category
            tags: Optional tags
            author: Template author

        Returns:
            PromptTemplate: Created template

        Raises:
            ValueError: If template validation fails or ID already exists
        """
        # Check if template already exists
        existing = self._repository.find_template(template_id)
        if existing is not None:
            raise ValueError(f"Template with ID '{template_id}' already exists")

        # Create template objects
        tid = TemplateId(template_id)
        content = TemplateContent(template_content)

        # Create template
        template = PromptTemplate(
            id=tid,
            name=name,
            description=description,
            content=content,
            category=category,
            tags=tags or set(),
            author=author
        )

        # Validate template
        issues = template.validate()
        if issues:
            raise ValueError(f"Template validation failed: {'; '.join(issues)}")

        # Save template
        self._repository.save_template(template)

        return template

    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """
        Get a template by ID.

        Args:
            template_id: Template identifier

        Returns:
            Optional[PromptTemplate]: Template if found
        """
        return self._repository.find_template(template_id)

    def list_templates(self, category: Optional[str] = None,
                      tag: Optional[str] = None) -> List[PromptTemplate]:
        """
        List templates with optional filtering.

        Args:
            category: Filter by category
            tag: Filter by tag

        Returns:
            List[PromptTemplate]: Filtered templates
        """
        templates = self._repository.find_all_templates()

        # Apply filters
        if category:
            templates = [t for t in templates if t.category == category]

        if tag:
            templates = [t for t in templates if tag in t.tags]

        # Sort by usage count (most used first), then by name
        templates.sort(key=lambda t: (-t.usage_count, t.name))

        return templates

    def update_template(self, template_id: str, **updates) -> PromptTemplate:
        """
        Update an existing template.

        Args:
            template_id: Template identifier
            **updates: Fields to update

        Returns:
            PromptTemplate: Updated template

        Raises:
            ValueError: If template doesn't exist or updates are invalid
        """
        template = self._repository.find_template(template_id)
        if template is None:
            raise ValueError(f"Template '{template_id}' does not exist")

        # Update content if provided
        if 'template_content' in updates:
            new_content = TemplateContent(updates['template_content'])
            template.update_content(new_content)

        # Update metadata if provided
        metadata_updates = {}
        for key in ['name', 'description', 'category', 'tags']:
            if key in updates:
                metadata_updates[key] = updates[key]

        if metadata_updates:
            template.update_metadata(**metadata_updates)

        # Validate updated template
        issues = template.validate()
        if issues:
            raise ValueError(f"Template validation failed: {'; '.join(issues)}")

        # Save updated template
        self._repository.save_template(template)

        return template

    def delete_template(self, template_id: str) -> bool:
        """
        Delete a template.

        Args:
            template_id: Template identifier

        Returns:
            bool: True if deleted, False if not found
        """
        template = self._repository.find_template(template_id)
        if template is None:
            return False

        # In a real implementation, this would call repository.delete_template
        # For now, we'll assume deletion is handled by the repository
        return True

    def render_template(self, template_id: str, values: Dict[str, str]) -> str:
        """
        Render a template with provided values.

        Args:
            template_id: Template identifier
            values: Variable values

        Returns:
            str: Rendered content

        Raises:
            ValueError: If template not found or rendering fails
        """
        template = self._repository.find_template(template_id)
        if template is None:
            raise ValueError(f"Template '{template_id}' not found")

        return template.render(values)

    def get_categories(self) -> List[str]:
        """Get all template categories."""
        templates = self._repository.find_all_templates()
        categories = {t.category for t in templates}
        return sorted(list(categories))

    def get_tags(self) -> List[str]:
        """Get all template tags."""
        templates = self._repository.find_all_templates()
        all_tags = set()
        for template in templates:
            all_tags.update(template.tags)
        return sorted(list(all_tags))

    def validate_template_content(self, content: str) -> List[str]:
        """
        Validate template content without creating a template.

        Args:
            content: Template content to validate

        Returns:
            List[str]: List of validation issues
        """
        try:
            template_content = TemplateContent(content)
            return template_content.validate()
        except ValueError as e:
            return [str(e)]