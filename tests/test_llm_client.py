"""
Tests for the Gemini LLM client service.

Since we don't want to hit the real API in CI, these tests exercise
the deterministic fallback path (no GEMINI_API_KEY).
"""

import asyncio

from src.services.llm_client import generate_explanation


class TestFallbackExplanation:
    """When GEMINI_API_KEY is unset the fallback path is used."""

    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_returns_all_four_keys(self):
        result = self._run(generate_explanation(
            gene="CYP2D6",
            diplotype="*1/*4",
            phenotype="IM",
            drug="CODEINE",
            risk_label="Adjust Dosage",
            severity="moderate",
        ))
        assert "summary" in result
        assert "mechanism" in result
        assert "justification" in result
        assert "recommendation" in result

    def test_summary_mentions_gene_and_drug(self):
        result = self._run(generate_explanation(
            gene="CYP2D6",
            diplotype="*4/*4",
            phenotype="PM",
            drug="CODEINE",
            risk_label="Ineffective",
            severity="high",
        ))
        assert "CYP2D6" in result["summary"]
        assert "CODEINE" in result["summary"]

    def test_values_are_strings(self):
        result = self._run(generate_explanation(
            gene="DPYD",
            diplotype="*1/*2A",
            phenotype="IM",
            drug="FLUOROURACIL",
            risk_label="Adjust Dosage",
            severity="high",
        ))
        for v in result.values():
            assert isinstance(v, str)
