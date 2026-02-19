"""
PharmaGuard — CPIC-style rule-based risk mapping engine.

Responsibilities
────────────────
1. Map  (drug, phenotype) → (risk_label, severity, confidence).
2. Provide the drug → primary-gene lookup.
3. Validate drug names against the supported panel.

Phenotype is inferred by the VCF parser from pathogenic variant
counts (not from star-allele diplotypes, since the VCF uses numeric
STAR quality ratings rather than star-allele nomenclature).

References
──────────
• CPIC guideline for codeine/CYP2D6       — PMID 32602691
• CPIC guideline for clopidogrel/CYP2C19  — PMID 34003977
• CPIC guideline for warfarin/CYP2C9      — PMID 27997040
• CPIC guideline for simvastatin/SLCO1B1   — PMID 24918167
• CPIC guideline for thiopurines/TPMT      — PMID 21270794
• CPIC guideline for fluoropyrimidines/DPYD— PMID 29152729
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

from src.models.schemas import Phenotype, RiskLabel, Severity

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# SUPPORTED PANEL
# ═══════════════════════════════════════════════════════════════════════════

SUPPORTED_GENES: List[str] = [
    "CYP2D6", "CYP2C19", "CYP2C9", "SLCO1B1", "TPMT", "DPYD",
]

SUPPORTED_DRUGS: List[str] = [
    "CODEINE", "WARFARIN", "CLOPIDOGREL",
    "SIMVASTATIN", "AZATHIOPRINE", "FLUOROURACIL",
]


# ═══════════════════════════════════════════════════════════════════════════
# DRUG → PRIMARY GENE
# ═══════════════════════════════════════════════════════════════════════════

DRUG_GENE_MAP: Dict[str, str] = {
    "CODEINE":      "CYP2D6",
    "CLOPIDOGREL":  "CYP2C19",
    "WARFARIN":     "CYP2C9",
    "SIMVASTATIN":  "SLCO1B1",
    "AZATHIOPRINE": "TPMT",
    "FLUOROURACIL": "DPYD",
}


# ═══════════════════════════════════════════════════════════════════════════
# (DRUG, PHENOTYPE_STRING) → (RiskLabel, Severity, confidence)
#
# Phenotype comes from the VCF parser as a string: PM, IM, NM, RM, URM
# ═══════════════════════════════════════════════════════════════════════════

_RiskRow = Tuple[RiskLabel, Severity, float]

RISK_TABLE: Dict[Tuple[str, str], _RiskRow] = {
    # ── CODEINE × CYP2D6 ────────────────────────────────────────────
    ("CODEINE", "NM"):  (RiskLabel.SAFE,          Severity.NONE,     0.95),
    ("CODEINE", "IM"):  (RiskLabel.ADJUST_DOSAGE, Severity.MODERATE, 0.85),
    ("CODEINE", "PM"):  (RiskLabel.INEFFECTIVE,   Severity.HIGH,     0.92),
    ("CODEINE", "RM"):  (RiskLabel.ADJUST_DOSAGE, Severity.MODERATE, 0.80),
    ("CODEINE", "URM"): (RiskLabel.TOXIC,         Severity.CRITICAL, 0.93),

    # ── CLOPIDOGREL × CYP2C19 ───────────────────────────────────────
    ("CLOPIDOGREL", "NM"):  (RiskLabel.SAFE,          Severity.NONE,     0.95),
    ("CLOPIDOGREL", "IM"):  (RiskLabel.ADJUST_DOSAGE, Severity.MODERATE, 0.87),
    ("CLOPIDOGREL", "PM"):  (RiskLabel.INEFFECTIVE,   Severity.HIGH,     0.93),
    ("CLOPIDOGREL", "RM"):  (RiskLabel.SAFE,          Severity.NONE,     0.90),
    ("CLOPIDOGREL", "URM"): (RiskLabel.SAFE,          Severity.NONE,     0.88),

    # ── WARFARIN × CYP2C9 ───────────────────────────────────────────
    ("WARFARIN", "NM"): (RiskLabel.SAFE,          Severity.NONE,     0.94),
    ("WARFARIN", "IM"): (RiskLabel.ADJUST_DOSAGE, Severity.MODERATE, 0.88),
    ("WARFARIN", "PM"): (RiskLabel.TOXIC,         Severity.CRITICAL, 0.91),

    # ── SIMVASTATIN × SLCO1B1 ───────────────────────────────────────
    ("SIMVASTATIN", "NM"): (RiskLabel.SAFE,          Severity.NONE,     0.94),
    ("SIMVASTATIN", "IM"): (RiskLabel.ADJUST_DOSAGE, Severity.MODERATE, 0.86),
    ("SIMVASTATIN", "PM"): (RiskLabel.TOXIC,         Severity.HIGH,     0.90),

    # ── AZATHIOPRINE × TPMT ─────────────────────────────────────────
    ("AZATHIOPRINE", "NM"): (RiskLabel.SAFE,          Severity.NONE,     0.95),
    ("AZATHIOPRINE", "IM"): (RiskLabel.ADJUST_DOSAGE, Severity.HIGH,     0.89),
    ("AZATHIOPRINE", "PM"): (RiskLabel.TOXIC,         Severity.CRITICAL, 0.94),

    # ── FLUOROURACIL × DPYD ─────────────────────────────────────────
    ("FLUOROURACIL", "NM"): (RiskLabel.SAFE,          Severity.NONE,     0.95),
    ("FLUOROURACIL", "IM"): (RiskLabel.ADJUST_DOSAGE, Severity.HIGH,     0.90),
    ("FLUOROURACIL", "PM"): (RiskLabel.TOXIC,         Severity.CRITICAL, 0.95),
}


# ═══════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════

def validate_drug(drug: str) -> bool:
    """Check whether a drug name is in the supported panel."""
    return drug.strip().upper() in DRUG_GENE_MAP


def get_primary_gene(drug: str) -> Optional[str]:
    """Return the primary pharmacogene for a drug, or None."""
    return DRUG_GENE_MAP.get(drug.strip().upper())


def assess_risk(
    drug: str,
    phenotype: str,
) -> Tuple[RiskLabel, Severity, float]:
    """
    Evaluate pharmacogenomic risk for a drug–phenotype pair.

    Parameters
    ----------
    drug      : str – drug name (e.g. "CODEINE")
    phenotype : str – metabolizer phenotype string (e.g. "PM", "IM", "NM")

    Returns
    -------
    tuple of (RiskLabel, Severity, confidence: float)
        Falls back to (Unknown, low, 0.40) when no rule matches.
    """
    key = (drug.strip().upper(), phenotype.strip().upper())
    if key in RISK_TABLE:
        return RISK_TABLE[key]

    logger.info(
        "No risk rule for (%s, %s) — defaulting to Unknown", drug, phenotype,
    )
    return (RiskLabel.UNKNOWN, Severity.LOW, 0.40)
