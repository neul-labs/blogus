"""
TortoiseORM database configuration.
"""

import os
from tortoise import Tortoise

# Get database URL from environment or use SQLite as default
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite://./data/blogus.db"
)

# TortoiseORM configuration
TORTOISE_ORM = {
    "connections": {
        "default": DATABASE_URL
    },
    "apps": {
        "models": {
            "models": ["blogus.infrastructure.database.models", "aerich.models"],
            "default_connection": "default",
        }
    },
    "use_tz": True,
    "timezone": "UTC"
}


async def init_db():
    """Initialize database connection and create tables."""
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()


async def close_db():
    """Close database connections."""
    await Tortoise.close_connections()


def get_tortoise_config():
    """Get TortoiseORM configuration for FastAPI integration."""
    return TORTOISE_ORM
