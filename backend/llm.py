"""
PharmaGuard — backend compatibility layer (LLM client).

Re-exports the public API from the canonical ``src.services.llm_client``
module so that legacy ``backend.llm`` imports continue to work.
"""

from src.services.llm_client import generate_explanation  # noqa: F401
