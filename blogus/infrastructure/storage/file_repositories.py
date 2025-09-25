"""
File-based repository implementations.
"""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from ...domain.models.prompt import Prompt, PromptRepository, PromptId, TemplateRepository
from ...domain.models.template import PromptTemplate
from ...shared.exceptions import ConfigurationError


class FilePromptRepository(PromptRepository):
    """File-based implementation of PromptRepository."""

    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.prompts_dir = storage_dir / "prompts"
        self.prompts_dir.mkdir(parents=True, exist_ok=True)

    def save(self, prompt: Prompt) -> None:
        """Save a prompt to file."""
        try:
            prompt_file = self.prompts_dir / f"{prompt.id.value}.json"
            data = self._prompt_to_dict(prompt)

            with open(prompt_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)

        except Exception as e:
            raise ConfigurationError(f"Failed to save prompt {prompt.id.value}: {e}")

    def find_by_id(self, prompt_id: PromptId) -> Optional[Prompt]:
        """Find prompt by ID."""
        try:
            prompt_file = self.prompts_dir / f"{prompt_id.value}.json"
            if not prompt_file.exists():
                return None

            with open(prompt_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return self._dict_to_prompt(data)

        except Exception as e:
            raise ConfigurationError(f"Failed to load prompt {prompt_id.value}: {e}")

    def find_all(self) -> List[Prompt]:
        """Find all prompts."""
        prompts = []

        try:
            for prompt_file in self.prompts_dir.glob("*.json"):
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                prompt = self._dict_to_prompt(data)
                prompts.append(prompt)

        except Exception as e:
            raise ConfigurationError(f"Failed to load prompts: {e}")

        return prompts

    def delete(self, prompt_id: PromptId) -> bool:
        """Delete a prompt."""
        try:
            prompt_file = self.prompts_dir / f"{prompt_id.value}.json"
            if prompt_file.exists():
                prompt_file.unlink()
                return True
            return False

        except Exception as e:
            raise ConfigurationError(f"Failed to delete prompt {prompt_id.value}: {e}")

    def _prompt_to_dict(self, prompt: Prompt) -> Dict[str, Any]:
        """Convert prompt to dictionary."""
        return {
            "id": prompt.id.value,
            "text": prompt.text.content,
            "goal": prompt.goal.description if prompt.goal else None,
            "created_at": prompt.created_at.isoformat(),
            "updated_at": prompt.updated_at.isoformat()
        }

    def _dict_to_prompt(self, data: Dict[str, Any]) -> Prompt:
        """Convert dictionary to prompt."""
        from ...domain.models.prompt import PromptText, Goal

        prompt_id = PromptId(data["id"])
        prompt_text = PromptText(data["text"])
        goal = Goal(data["goal"]) if data.get("goal") else None

        # Parse timestamps
        created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now()
        updated_at = datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now()

        prompt = Prompt(
            id=prompt_id,
            text=prompt_text,
            goal=goal,
            created_at=created_at,
            updated_at=updated_at
        )

        return prompt


class FileTemplateRepository(TemplateRepository):
    """File-based implementation of TemplateRepository."""

    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.templates_dir = storage_dir / "templates"
        self.templates_dir.mkdir(parents=True, exist_ok=True)

    def save_template(self, template: PromptTemplate) -> None:
        """Save a template to file."""
        try:
            template_file = self.templates_dir / f"{template.id.value}.json"
            data = self._template_to_dict(template)

            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)

        except Exception as e:
            raise ConfigurationError(f"Failed to save template {template.id.value}: {e}")

    def find_template(self, name: str) -> Optional[PromptTemplate]:
        """Find template by name."""
        try:
            template_file = self.templates_dir / f"{name}.json"
            if not template_file.exists():
                return None

            with open(template_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return self._dict_to_template(data)

        except Exception as e:
            raise ConfigurationError(f"Failed to load template {name}: {e}")

    def find_all_templates(self) -> List[PromptTemplate]:
        """Find all templates."""
        templates = []

        try:
            for template_file in self.templates_dir.glob("*.json"):
                with open(template_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                template = self._dict_to_template(data)
                templates.append(template)

        except Exception as e:
            raise ConfigurationError(f"Failed to load templates: {e}")

        return templates

    def _template_to_dict(self, template: PromptTemplate) -> Dict[str, Any]:
        """Convert template to dictionary."""
        return {
            "id": template.id.value,
            "name": template.name,
            "description": template.description,
            "content": template.content.template,
            "category": template.category,
            "tags": list(template.tags),
            "author": template.author,
            "version": template.version,
            "usage_count": template.usage_count,
            "created_at": template.created_at.isoformat(),
            "updated_at": template.updated_at.isoformat()
        }

    def _dict_to_template(self, data: Dict[str, Any]) -> PromptTemplate:
        """Convert dictionary to template."""
        from ...domain.models.template import TemplateId, TemplateContent

        template_id = TemplateId(data["id"])
        content = TemplateContent(data["content"])

        # Parse timestamps
        created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now()
        updated_at = datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now()

        template = PromptTemplate(
            id=template_id,
            name=data["name"],
            description=data["description"],
            content=content,
            category=data.get("category", "general"),
            tags=set(data.get("tags", [])),
            author=data.get("author", "unknown"),
            version=data.get("version", "1.0.0"),
            created_at=created_at,
            updated_at=updated_at,
            usage_count=data.get("usage_count", 0)
        )

        return template