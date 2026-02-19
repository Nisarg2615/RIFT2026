"""
PharmaGuard — Phenotype Refinement Helper (CPIC Activity Score Model).

# NEW: clinical modifier logic — phenotype precision layer

Refines the base VCF-parser phenotype using CPIC-style activity scores
for more granular metabolizer classification.

Does NOT replace the VCF parser or its phenotype inference.
Provides an additional activity_score that downstream clinical
modifiers can use for finer-grained risk adjustment.

Reference: CPIC Term Standardization — PMID 27441996
"""

from __future__ import annotations

import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# CPIC activity score baselines and thresholds per gene
# ═══════════════════════════════════════════════════════════════════════════

_GENE_ACTIVITY_CONFIG: Dict[str, Dict] = {
    "CYP2D6": {
        "base_activity": 2.0,
        "het_decrement": 0.5,
        "hom_decrement": 1.0,
        "thresholds": [
            (0.0,  "PM"),
            (1.0,  "IM"),
            (2.25, "NM"),
            (999,  "URM"),
        ],
    },
    "CYP2C19": {
        "base_activity": 2.0,
        "het_decrement": 0.5,
        "hom_decrement": 1.0,
        "thresholds": [
            (0.0, "PM"),
            (1.0, "IM"),
            (2.0, "NM"),
            (999, "RM"),
        ],
    },
    "CYP2C9": {
        "base_activity": 2.0,
        "het_decrement": 0.5,
        "hom_decrement": 1.0,
        "thresholds": [(0.0, "PM"), (1.0, "IM"), (2.0, "NM")],
    },
    "SLCO1B1": {
        "base_activity": 2.0,
        "het_decrement": 0.5,
        "hom_decrement": 1.0,
        "thresholds": [(0.0, "PM"), (1.0, "IM"), (2.0, "NM")],
    },
    "TPMT": {
        "base_activity": 2.0,
        "het_decrement": 0.5,
        "hom_decrement": 1.0,
        "thresholds": [(0.0, "PM"), (0.5, "IM"), (2.0, "NM")],
    },
    "DPYD": {
        "base_activity": 2.0,
        "het_decrement": 0.5,
        "hom_decrement": 1.0,
        "thresholds": [(0.0, "PM"), (1.0, "IM"), (2.0, "NM")],
    },
}


def compute_activity_score(
    gene: str,
    pathogenic_count: int,
    hom_alt_count: int,
) -> float:
    """
    Compute a CPIC-style activity score for a gene.

    Parameters
    ----------
    gene             : HGNC gene symbol (e.g. "CYP2D6")
    pathogenic_count : total pathogenic variants (het + hom_alt)
    hom_alt_count    : homozygous-alternate pathogenic variants only

    Returns
    -------
    float — activity score (0.0 = no activity, 2.0 = normal)
    """
    config = _GENE_ACTIVITY_CONFIG.get(gene.upper())
    if config is None:
        return 2.0  # default: normal

    het_count = max(pathogenic_count - hom_alt_count, 0)
    score = config["base_activity"]
    score -= het_count * config["het_decrement"]
    score -= hom_alt_count * config["hom_decrement"]
    return max(0.0, round(score, 2))


def refine_phenotype(
    gene: str,
    base_phenotype: str,
    pathogenic_count: int,
    hom_alt_count: int,
) -> Tuple[str, float]:
    """
    Refine phenotype using CPIC activity score model.

    # NEW: clinical modifier logic — phenotype refinement

    Returns
    -------
    (refined_phenotype, activity_score)
    """
    activity = compute_activity_score(gene, pathogenic_count, hom_alt_count)

    config = _GENE_ACTIVITY_CONFIG.get(gene.upper())
    if config is None:
        return base_phenotype, activity

    refined = base_phenotype
    for upper_bound, label in config["thresholds"]:
        if activity <= upper_bound:
            refined = label
            break

    if refined != base_phenotype:
        logger.info(
            "Phenotype refined for %s: %s → %s (activity=%.2f)",
            gene, base_phenotype, refined, activity,
        )

    return refined, activity
