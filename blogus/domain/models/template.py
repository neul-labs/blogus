"""
Domain models for prompt templates.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Set
import re


@dataclass(frozen=True)
class TemplateId:
    """Value object for template identification."""
    value: str

    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("TemplateId value must be a non-empty string")
        # Template names should be alphanumeric with underscores/hyphens
        if not re.match(r'^[a-zA-Z0-9_-]+$', self.value):
            raise ValueError("TemplateId must contain only alphanumeric characters, underscores, and hyphens")


@dataclass(frozen=True)
class TemplateContent:
    """Value object for template content."""
    template: str
    variables: frozenset[str] = field(init=False)

    def __post_init__(self):
        if not isinstance(self.template, str):
            raise ValueError("Template content must be a string")
        if not self.template.strip():
            raise ValueError("Template content cannot be empty")

        # Extract variables using double braces {{ }}
        variables = set(re.findall(r'\{\{([^}]+)\}\}', self.template))
        object.__setattr__(self, 'variables', frozenset(variables))

    def render(self, values: Dict[str, str]) -> str:
        """Render template with provided values."""
        missing_vars = self.variables - set(values.keys())
        if missing_vars:
            raise ValueError(f"Missing required variables: {missing_vars}")

        try:
            # Replace double braces with single braces for .format()
            template_for_format = self.template
            for key, value in values.items():
                template_for_format = template_for_format.replace('{{' + key + '}}', str(value))
            return template_for_format
        except Exception as e:
            raise ValueError(f"Template rendering failed: {e}")

    def validate(self) -> List[str]:
        """Validate template content."""
        issues = []

        # Check for basic syntax issues
        try:
            # Test with dummy values
            test_values = {var: f"test_{var}" for var in self.variables}
            self.template.format(**test_values)
        except Exception as e:
            issues.append(f"Template syntax error: {e}")

        # Check for suspicious patterns
        if '<script' in self.template.lower():
            issues.append("Template contains potentially unsafe script tags")

        return issues


@dataclass
class PromptTemplate:
    """Domain entity for prompt templates."""
    id: TemplateId
    name: str
    description: str
    content: TemplateContent
    category: str = "general"
    tags: Set[str] = field(default_factory=set)
    author: str = "unknown"
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    usage_count: int = 0

    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("Template name cannot be empty")
        if not self.description.strip():
            raise ValueError("Template description cannot be empty")
        if not self.category.strip():
            raise ValueError("Template category cannot be empty")

    def update_content(self, new_content: TemplateContent):
        """Update template content."""
        self.content = new_content
        self.updated_at = datetime.now()

    def update_metadata(self, name: Optional[str] = None, description: Optional[str] = None,
                       category: Optional[str] = None, tags: Optional[Set[str]] = None):
        """Update template metadata."""
        if name is not None:
            if not name.strip():
                raise ValueError("Template name cannot be empty")
            self.name = name

        if description is not None:
            if not description.strip():
                raise ValueError("Template description cannot be empty")
            self.description = description

        if category is not None:
            if not category.strip():
                raise ValueError("Template category cannot be empty")
            self.category = category

        if tags is not None:
            self.tags = tags

        self.updated_at = datetime.now()

    def increment_usage(self):
        """Increment usage counter."""
        self.usage_count += 1

    def validate(self) -> List[str]:
        """Validate the entire template."""
        issues = []

        # Validate content
        content_issues = self.content.validate()
        issues.extend(content_issues)

        # Validate metadata
        if len(self.name) > 100:
            issues.append("Template name is too long (max 100 characters)")

        if len(self.description) > 500:
            issues.append("Template description is too long (max 500 characters)")

        return issues

    @property
    def variables(self) -> frozenset[str]:
        """Get template variables."""
        return self.content.variables

    def render(self, values: Dict[str, str]) -> str:
        """Render template with provided values."""
        self.increment_usage()
        return self.content.render(values)