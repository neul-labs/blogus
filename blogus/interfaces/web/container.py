"""
Dependency injection container for web interface.
"""

from pathlib import Path
from functools import lru_cache

from ...infrastructure.config.settings import get_settings
from ...infrastructure.llm.litellm_provider import LiteLLMProvider
from ...infrastructure.storage.file_repositories import FilePromptRepository, FileTemplateRepository
from ...application.services.prompt_service import PromptService
from ...application.services.template_service import TemplateService


class WebContainer:
    """Dependency injection container for web interface."""

    def __init__(self):
        self._settings = get_settings()
        self._instances = {}

    @property
    def settings(self):
        """Get settings."""
        return self._settings

    def get_llm_provider(self):
        """Get LLM provider."""
        if 'llm_provider' not in self._instances:
            self._instances['llm_provider'] = LiteLLMProvider(
                max_retries=self._settings.llm.max_retries
            )
        return self._instances['llm_provider']

    def get_prompt_repository(self):
        """Get prompt repository."""
        if 'prompt_repository' not in self._instances:
            storage_dir = Path(self._settings.storage.data_directory)
            self._instances['prompt_repository'] = FilePromptRepository(storage_dir)
        return self._instances['prompt_repository']

    def get_template_repository(self):
        """Get template repository."""
        if 'template_repository' not in self._instances:
            storage_dir = Path(self._settings.storage.data_directory)
            self._instances['template_repository'] = FileTemplateRepository(storage_dir)
        return self._instances['template_repository']

    def get_prompt_service(self):
        """Get prompt service."""
        if 'prompt_service' not in self._instances:
            self._instances['prompt_service'] = PromptService(
                self.get_prompt_repository(),
                self.get_llm_provider()
            )
        return self._instances['prompt_service']

    def get_template_service(self):
        """Get template service."""
        if 'template_service' not in self._instances:
            self._instances['template_service'] = TemplateService(
                self.get_template_repository()
            )
        return self._instances['template_service']


# Global container
_container = None


@lru_cache()
def get_container() -> WebContainer:
    """Get container instance."""
    global _container
    if _container is None:
        _container = WebContainer()
    return _container