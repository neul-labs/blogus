"""
Configuration management for the application.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv
import yaml
import json

# Load environment variables
load_dotenv()


@dataclass
class LLMSettings:
    """LLM configuration settings."""
    default_target_model: str = "gpt-4o"
    default_judge_model: str = "gpt-4o"
    max_retries: int = 3
    timeout_seconds: int = 60
    max_tokens: int = 1000

    # API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None

    def __post_init__(self):
        """Load API keys from environment."""
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.groq_api_key = os.getenv('GROQ_API_KEY')


@dataclass
class StorageSettings:
    """Storage configuration settings."""
    data_directory: str = str(Path.home() / '.blogus')
    backup_enabled: bool = True
    backup_directory: Optional[str] = None

    def __post_init__(self):
        """Initialize storage directories."""
        # Ensure data directory exists
        Path(self.data_directory).mkdir(parents=True, exist_ok=True)

        # Set default backup directory
        if self.backup_enabled and not self.backup_directory:
            self.backup_directory = str(Path(self.data_directory) / 'backups')
            Path(self.backup_directory).mkdir(parents=True, exist_ok=True)


@dataclass
class SecuritySettings:
    """Security configuration settings."""
    max_prompt_length: int = 100000
    enable_input_validation: bool = True
    enable_output_sanitization: bool = True
    allowed_models: Optional[list] = None

    def __post_init__(self):
        """Set default allowed models."""
        if self.allowed_models is None:
            self.allowed_models = [
                "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo",
                "claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307",
                "groq/llama3-70b-8192", "groq/mixtral-8x7b-32768", "groq/gemma-7b-it"
            ]


@dataclass
class WebSettings:
    """Web interface configuration settings."""
    host: str = "localhost"
    port: int = 8000
    debug: bool = False
    cors_origins: list = None
    api_prefix: str = "/api/v1"

    def __post_init__(self):
        """Set default CORS origins."""
        if self.cors_origins is None:
            self.cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]


@dataclass
class LoggingSettings:
    """Logging configuration settings."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size_mb: int = 10
    backup_count: int = 5


@dataclass
class DatabaseSettings:
    """Database configuration settings."""
    backend: str = "file"  # "file" or "database"
    url: str = "sqlite://./data/blogus.db"
    pool_size: int = 5
    echo: bool = False

    def __post_init__(self):
        """Load database URL from environment."""
        env_url = os.getenv('DATABASE_URL')
        if env_url:
            self.url = env_url
            self.backend = "database"


@dataclass
class ObservabilitySettings:
    """Observability configuration settings."""
    tracing_enabled: bool = True
    service_name: str = "blogus"
    service_version: str = "0.2.0"
    environment: str = "development"
    otlp_endpoint: Optional[str] = None
    console_export: bool = False

    def __post_init__(self):
        """Load settings from environment."""
        self.tracing_enabled = os.getenv('OTEL_ENABLED', 'true').lower() == 'true'
        self.service_name = os.getenv('OTEL_SERVICE_NAME', self.service_name)
        self.environment = os.getenv('OTEL_ENVIRONMENT', self.environment)
        self.otlp_endpoint = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT')
        self.console_export = os.getenv('OTEL_CONSOLE_EXPORT', '').lower() == 'true'


@dataclass
class Settings:
    """Main application settings."""
    llm: LLMSettings
    storage: StorageSettings
    security: SecuritySettings
    web: WebSettings
    logging: LoggingSettings
    database: DatabaseSettings
    observability: ObservabilitySettings

    @classmethod
    def load_from_file(cls, config_path: Optional[Path] = None) -> 'Settings':
        """Load settings from configuration file."""
        if config_path and config_path.exists():
            return cls._load_config_file(config_path)

        # Try default config file locations
        default_paths = [
            Path.home() / '.blogus' / 'config.yaml',
            Path.home() / '.blogus' / 'config.json',
            Path.cwd() / 'blogus.config.yaml',
            Path.cwd() / 'blogus.config.json',
        ]

        for path in default_paths:
            if path.exists():
                return cls._load_config_file(path)

        # Return default settings if no config file found
        return cls.default()

    @classmethod
    def default(cls) -> 'Settings':
        """Create default settings."""
        return cls(
            llm=LLMSettings(),
            storage=StorageSettings(),
            security=SecuritySettings(),
            web=WebSettings(),
            logging=LoggingSettings(),
            database=DatabaseSettings(),
            observability=ObservabilitySettings()
        )

    @classmethod
    def _load_config_file(cls, config_path: Path) -> 'Settings':
        """Load configuration from a specific file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    data = yaml.safe_load(f) or {}
                elif config_path.suffix.lower() == '.json':
                    data = json.load(f) or {}
                else:
                    raise ValueError(f"Unsupported config file format: {config_path.suffix}")

            return cls._from_dict(data)

        except Exception as e:
            raise ValueError(f"Failed to load config from {config_path}: {e}")

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> 'Settings':
        """Create settings from dictionary."""
        return cls(
            llm=LLMSettings(**data.get('llm', {})),
            storage=StorageSettings(**data.get('storage', {})),
            security=SecuritySettings(**data.get('security', {})),
            web=WebSettings(**data.get('web', {})),
            logging=LoggingSettings(**data.get('logging', {})),
            database=DatabaseSettings(**data.get('database', {})),
            observability=ObservabilitySettings(**data.get('observability', {}))
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            'llm': {
                'default_target_model': self.llm.default_target_model,
                'default_judge_model': self.llm.default_judge_model,
                'max_retries': self.llm.max_retries,
                'timeout_seconds': self.llm.timeout_seconds,
                'max_tokens': self.llm.max_tokens
                # Note: API keys are not included for security
            },
            'storage': {
                'data_directory': self.storage.data_directory,
                'backup_enabled': self.storage.backup_enabled,
                'backup_directory': self.storage.backup_directory
            },
            'security': {
                'max_prompt_length': self.security.max_prompt_length,
                'enable_input_validation': self.security.enable_input_validation,
                'enable_output_sanitization': self.security.enable_output_sanitization,
                'allowed_models': self.security.allowed_models
            },
            'web': {
                'host': self.web.host,
                'port': self.web.port,
                'debug': self.web.debug,
                'cors_origins': self.web.cors_origins,
                'api_prefix': self.web.api_prefix
            },
            'logging': {
                'level': self.logging.level,
                'format': self.logging.format,
                'file_path': self.logging.file_path,
                'max_file_size_mb': self.logging.max_file_size_mb,
                'backup_count': self.logging.backup_count
            },
            'database': {
                'backend': self.database.backend,
                'url': self.database.url,
                'pool_size': self.database.pool_size,
                'echo': self.database.echo
            },
            'observability': {
                'tracing_enabled': self.observability.tracing_enabled,
                'service_name': self.observability.service_name,
                'service_version': self.observability.service_version,
                'environment': self.observability.environment,
                'otlp_endpoint': self.observability.otlp_endpoint,
                'console_export': self.observability.console_export
            }
        }

    def save_to_file(self, config_path: Path) -> None:
        """Save settings to configuration file."""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        data = self.to_dict()

        with open(config_path, 'w', encoding='utf-8') as f:
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                yaml.dump(data, f, default_flow_style=False, sort_keys=True)
            elif config_path.suffix.lower() == '.json':
                json.dump(data, f, indent=2, sort_keys=True)
            else:
                raise ValueError(f"Unsupported config file format: {config_path.suffix}")


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings.load_from_file()
    return _settings


def reload_settings(config_path: Optional[Path] = None) -> Settings:
    """Reload global settings."""
    global _settings
    _settings = Settings.load_from_file(config_path)
    return _settings