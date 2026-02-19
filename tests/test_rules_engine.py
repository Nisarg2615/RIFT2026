"""
Tests for the CPIC-style rules engine.
"""

from src.models.schemas import Phenotype, RiskLabel, Severity
from src.services.rules_engine import (
    assess_risk,
    get_primary_gene,
    resolve_phenotype,
)


class TestResolvePhenotype:
    def test_known_diplotype(self):
        assert resolve_phenotype("CYP2D6", "*1/*4") == Phenotype.IM

    def test_normal_metabolizer(self):
        assert resolve_phenotype("CYP2C9", "*1/*1") == Phenotype.NM

    def test_poor_metabolizer(self):
        assert resolve_phenotype("CYP2D6", "*4/*4") == Phenotype.PM

    def test_unknown_diplotype_returns_unknown(self):
        assert resolve_phenotype("CYP2D6", "*99/*99") == Phenotype.UNKNOWN


class TestGetPrimaryGene:
    def test_codeine(self):
        assert get_primary_gene("CODEINE") == "CYP2D6"

    def test_warfarin(self):
        assert get_primary_gene("WARFARIN") == "CYP2C9"

    def test_case_insensitive(self):
        assert get_primary_gene("codeine") == "CYP2D6"

    def test_unknown_drug_returns_none(self):
        assert get_primary_gene("ASPIRIN") is None


class TestAssessRisk:
    def test_safe_codeine_nm(self):
        label, sev, conf = assess_risk("CYP2D6", "CODEINE", Phenotype.NM)
        assert label == RiskLabel.SAFE
        assert sev == Severity.NONE
        assert conf > 0.9

    def test_toxic_codeine_urm(self):
        label, sev, conf = assess_risk("CYP2D6", "CODEINE", Phenotype.URM)
        assert label == RiskLabel.TOXIC
        assert sev == Severity.CRITICAL

    def test_unknown_phenotype_falls_back(self):
        label, sev, conf = assess_risk("CYP2D6", "CODEINE", Phenotype.UNKNOWN)
        assert label == RiskLabel.UNKNOWN
        assert conf < 0.5
