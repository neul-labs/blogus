"""
Web interface package.
"""

# Conditional import to avoid FastAPI dependency when not needed
try:
    from .main import app
    __all__ = ["app"]
except ImportError:
    # FastAPI not available, web functionality disabled
    __all__ = []