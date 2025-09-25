"""
Shared exception classes.
"""


class BlogusError(Exception):
    """Base exception for all Blogus-related errors."""
    pass


class DomainError(BlogusError):
    """Base exception for domain-related errors."""
    pass


class ApplicationError(BlogusError):
    """Base exception for application-related errors."""
    pass


class InfrastructureError(BlogusError):
    """Base exception for infrastructure-related errors."""
    pass


# Domain exceptions
class ValidationError(DomainError):
    """Raised when domain validation fails."""
    pass


class InvalidPromptError(DomainError):
    """Raised when a prompt is invalid."""
    pass


class InvalidTemplateError(DomainError):
    """Raised when a template is invalid."""
    pass


# Infrastructure exceptions
class LLMAPIError(InfrastructureError):
    """Base exception for LLM API errors."""
    def __init__(self, message: str, model: str = None, status_code: int = None):
        self.model = model
        self.status_code = status_code
        super().__init__(message)


class RateLimitError(LLMAPIError):
    """Raised when API rate limits are exceeded."""
    def __init__(self, message: str, model: str = None, retry_after: int = None):
        self.retry_after = retry_after
        super().__init__(message, model)


class AuthenticationError(LLMAPIError):
    """Raised when API authentication fails."""
    pass


class ModelNotAvailableError(LLMAPIError):
    """Raised when a requested model is not available."""
    pass


class ConfigurationError(InfrastructureError):
    """Raised when there's a configuration-related error."""
    pass


class StorageError(InfrastructureError):
    """Raised when storage operations fail."""
    pass


# Application exceptions
class ServiceError(ApplicationError):
    """Raised when application service operations fail."""
    pass


class ResourceNotFoundError(ApplicationError):
    """Raised when a requested resource is not found."""
    pass


class BusinessRuleViolationError(ApplicationError):
    """Raised when business rules are violated."""
    pass