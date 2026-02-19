"""
PharmaGuard — Centralised configuration re-export.

Usage:
    from src.core.config import get_settings
    settings = get_settings()
"""

from src.core import Settings, get_settings

__all__ = ["Settings", "get_settings"]
