"""
PharmaGuard — Application configuration.

Loads environment variables via pydantic-settings.
All config is centralised here so nothing else reads os.environ directly.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application-wide settings, populated from environment / .env file.
    """

    # ── App metadata ─────────────────────────────────────────────────
    app_name: str = "PharmaGuard"
    app_version: str = "1.0.0"
    debug: bool = False

    # ── Server ───────────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000

    # ── Google Gemini ────────────────────────────────────────────────
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # ── VCF constraints ──────────────────────────────────────────────
    max_vcf_size_bytes: int = 5 * 1024 * 1024  # 5 MB

    # ── CORS (comma-separated origins in env, parsed to list) ────────
    cors_origins: List[str] = ["*"]

    # ── Supported pharmacogenes and drugs ────────────────────────────
    supported_genes: List[str] = [
        "CYP2D6", "CYP2C19", "CYP2C9", "SLCO1B1", "TPMT", "DPYD",
    ]
    supported_drugs: List[str] = [
        "CODEINE", "WARFARIN", "CLOPIDOGREL",
        "SIMVASTATIN", "AZATHIOPRINE", "FLUOROURACIL",
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False          # GEMINI_API_KEY or gemini_api_key


@lru_cache()
def get_settings() -> Settings:
    """Singleton accessor — import this wherever you need config."""
    return Settings()
