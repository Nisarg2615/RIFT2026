"""
PharmaGuard — backend compatibility layer (FastAPI app).

Re-exports the ``app`` instance from the canonical ``src.main`` module
so that ``uvicorn backend.main:app`` continues to work.
"""

from src.main import app  # noqa: F401
