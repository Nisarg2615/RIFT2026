"""
PharmaGuard — Evidence-Based Accuracy Scoring Service.

Computes a composite evidence score that **justifies the accuracy** of each
drug recommendation.  This directly addresses the mentor feedback:
  "How can you justify the accuracy of your recommended medicine?"

Pipeline stage:  Risk + Interactions → **Evidence Score** → LLM → JSON

Score Components
────────────────
1. CPIC Guideline Level (A/B/C/D)   — weight 0.35
2. Variant Pathogenicity Confidence  — weight 0.25
3. Rule-Engine Match Confidence      — weight 0.20
4. Patient-History Corroboration     — weight 0.10
5. Interaction Awareness             — weight 0.10

Each component yields 0–1; the overall score is a weighted average.

References
──────────
The PMID for every CPIC guideline is stored here and exported with
every recommendation so clinicians can verify the source.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

from src.models.schemas import (
    DrugInteraction,
    EvidenceComponent,
    EvidenceLevel,
    EvidenceScore,
    HistoryFlag,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# CPIC Guideline Reference Database
#
# (DRUG, GENE) → (evidence_level, guideline_source, PMID, year)
# ═══════════════════════════════════════════════════════════════════════════

_GuidelineRow = Tuple[EvidenceLevel, str, str, int]

GUIDELINE_DB: Dict[Tuple[str, str], _GuidelineRow] = {
    ("CODEINE",      "CYP2D6"):  (EvidenceLevel.LEVEL_A, "CPIC", "32602691", 2020),
    ("CLOPIDOGREL",  "CYP2C19"): (EvidenceLevel.LEVEL_A, "CPIC", "34003977", 2021),
    ("WARFARIN",     "CYP2C9"):  (EvidenceLevel.LEVEL_A, "CPIC", "27997040", 2017),
    ("SIMVASTATIN",  "SLCO1B1"): (EvidenceLevel.LEVEL_A, "CPIC", "24918167", 2014),
    ("AZATHIOPRINE", "TPMT"):    (EvidenceLevel.LEVEL_A, "CPIC", "21270794", 2011),
    ("FLUOROURACIL", "DPYD"):    (EvidenceLevel.LEVEL_A, "CPIC", "29152729", 2018),
}

# Level → numeric score for weighting
_LEVEL_SCORES: Dict[EvidenceLevel, float] = {
    EvidenceLevel.LEVEL_A: 1.00,
    EvidenceLevel.LEVEL_B: 0.75,
    EvidenceLevel.LEVEL_C: 0.50,
    EvidenceLevel.LEVEL_D: 0.25,
    EvidenceLevel.NA:      0.10,
}


# ═══════════════════════════════════════════════════════════════════════════
# Weights for each evidence component
# ═══════════════════════════════════════════════════════════════════════════

_WEIGHTS = {
    "cpic_guideline":          0.35,
    "variant_confidence":      0.25,
    "rule_engine_confidence":  0.20,
    "history_corroboration":   0.10,
    "interaction_awareness":   0.10,
}


# ═══════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════

def compute_evidence_score(
    drug: str,
    gene: str,
    phenotype: str,
    rule_confidence: float,
    pathogenic_count: int,
    total_variant_count: int,
    interactions: List[DrugInteraction],
    history_flags: List[HistoryFlag],
    has_history: bool = False,
) -> EvidenceScore:
    """
    Compute a composite evidence-based accuracy score for one drug recommendation.

    Parameters
    ----------
    drug                : upper-case drug name
    gene                : HGNC gene symbol
    phenotype           : metabolizer phenotype string
    rule_confidence     : confidence from the rules engine (0–1)
    pathogenic_count    : number of pathogenic variants found for this gene
    total_variant_count : total variants found for this gene in the VCF
    interactions        : list of detected drug-drug interactions
    history_flags       : list of patient-history warnings
    has_history         : whether patient history was supplied at all

    Returns
    -------
    EvidenceScore model with full breakdown and justification narrative.
    """
    components: List[EvidenceComponent] = []

    # ── 1. CPIC Guideline Level ──────────────────────────────────────
    guideline = GUIDELINE_DB.get((drug.upper(), gene.upper()))
    if guideline:
        ev_level, source, pmid, year = guideline
        cpic_score = _LEVEL_SCORES[ev_level]
        components.append(EvidenceComponent(
            name="cpic_guideline",
            score=cpic_score,
            detail=f"CPIC Level {ev_level.value} guideline ({source}, PMID:{pmid}, {year}). "
                   f"Strong clinical evidence supports this gene-drug recommendation.",
        ))
    else:
        ev_level = EvidenceLevel.NA
        source = "None"
        pmid = ""
        cpic_score = _LEVEL_SCORES[EvidenceLevel.NA]
        components.append(EvidenceComponent(
            name="cpic_guideline",
            score=cpic_score,
            detail="No CPIC guideline available for this gene-drug pair. "
                   "Recommendation is based on general pharmacogenomic principles.",
        ))

    # ── 2. Variant Pathogenicity Confidence ──────────────────────────
    if total_variant_count > 0 and pathogenic_count > 0:
        # Higher confidence when we have clear pathogenic variants
        variant_score = min(1.0, 0.5 + (pathogenic_count * 0.25))
        variant_detail = (
            f"{pathogenic_count} pathogenic variant(s) out of {total_variant_count} "
            f"total variants detected for {gene}. Variant-level evidence is strong."
        )
    elif total_variant_count > 0:
        variant_score = 0.70  # Variants found but none flagged pathogenic
        variant_detail = (
            f"{total_variant_count} variants detected for {gene} but none are in the "
            f"known pathogenic set. Normal metabolizer inference is well-supported."
        )
    else:
        variant_score = 0.30
        variant_detail = (
            f"No variants detected for {gene}. Phenotype inference has lower confidence."
        )
    components.append(EvidenceComponent(
        name="variant_confidence",
        score=round(variant_score, 2),
        detail=variant_detail,
    ))

    # ── 3. Rule-Engine Match Confidence ──────────────────────────────
    re_detail = (
        f"Rule engine matched ({drug}, {phenotype}) with {rule_confidence:.0%} confidence. "
    )
    if rule_confidence >= 0.90:
        re_detail += "This is a well-established pharmacogenomic association."
    elif rule_confidence >= 0.80:
        re_detail += "Moderate-to-high confidence in this association."
    else:
        re_detail += "Lower confidence; clinical correlation recommended."
    components.append(EvidenceComponent(
        name="rule_engine_confidence",
        score=round(rule_confidence, 2),
        detail=re_detail,
    ))

    # ── 4. Patient History Corroboration ─────────────────────────────
    if has_history:
        if history_flags:
            hist_score = 0.90  # History was checked AND produced relevant flags
            hist_detail = (
                f"Patient history provided and analysed. {len(history_flags)} "
                f"flag(s) raised — recommendation incorporates patient context."
            )
        else:
            hist_score = 0.80  # History checked, no contraindications
            hist_detail = (
                "Patient history provided and checked. No contraindications or "
                "relevant warnings found — increases confidence in recommendation."
            )
    else:
        hist_score = 0.40
        hist_detail = (
            "No patient history provided. Recommendation is based solely on "
            "genomic data. Providing history (conditions, current medications, "
            "allergies) would improve accuracy."
        )
    components.append(EvidenceComponent(
        name="history_corroboration",
        score=round(hist_score, 2),
        detail=hist_detail,
    ))

    # ── 5. Interaction Awareness ─────────────────────────────────────
    if has_history:
        if interactions:
            int_score = 0.95  # Interactions found AND flagged
            int_detail = (
                f"{len(interactions)} drug-drug interaction(s) detected and reported. "
                f"Recommendation accounts for interaction risk."
            )
        else:
            int_score = 0.85
            int_detail = (
                "Drug interaction screening performed; no significant "
                "interactions detected with current medications."
            )
    else:
        int_score = 0.35
        int_detail = (
            "No current medication list provided; drug interaction screening "
            "could not be performed. Supply medication list for safer recommendation."
        )
    components.append(EvidenceComponent(
        name="interaction_awareness",
        score=round(int_score, 2),
        detail=int_detail,
    ))

    # ── Weighted composite ───────────────────────────────────────────
    overall = sum(
        comp.score * _WEIGHTS[comp.name]
        for comp in components
    )
    overall = round(min(1.0, max(0.0, overall)), 2)

    # ── Narrative justification ──────────────────────────────────────
    justification_parts = [
        f"Overall evidence score: {overall:.0%}.",
    ]
    if guideline:
        justification_parts.append(
            f"This recommendation is supported by CPIC Level {ev_level.value} evidence "
            f"(PMID:{pmid}), the gold standard for pharmacogenomic clinical guidelines."
        )
    justification_parts.append(
        f"The patient's {phenotype} metabolizer status for {gene} was inferred from "
        f"{pathogenic_count} pathogenic variant(s) detected in the VCF."
    )
    if has_history:
        justification_parts.append(
            "Patient history was incorporated, enabling personalised risk assessment "
            "beyond genomic data alone."
        )
    else:
        justification_parts.append(
            "⚠ Patient history was not provided. Submitting conditions, allergies, "
            "and current medications would further improve recommendation accuracy."
        )

    return EvidenceScore(
        overall_score=overall,
        evidence_level=ev_level,
        guideline_source=source,
        guideline_pmid=pmid,
        components=components,
        accuracy_justification=" ".join(justification_parts),
    )
