"""
PharmaGuard — Shared utility helpers.

Functions that don't belong to any single service live here.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from src.models.schemas import (
    ClinicalRecommendation,
    DrugInteraction,
    HistoryFlag,
)


# ─────────────────────────────────────────────────────────────────────────────
# Alternative drug suggestions (CPIC-informed)
# ─────────────────────────────────────────────────────────────────────────────

_ALT_DRUGS: Dict[str, List[str]] = {
    "CODEINE":      ["Tramadol", "Morphine (with monitoring)"],
    "WARFARIN":     ["Direct oral anticoagulants (DOACs)"],
    "CLOPIDOGREL":  ["Prasugrel", "Ticagrelor"],
    "SIMVASTATIN":  ["Pravastatin", "Rosuvastatin"],
    "AZATHIOPRINE": ["Mycophenolate mofetil"],
    "FLUOROURACIL": ["Capecitabine (with dose adjustment)"],
}


def build_clinical_recommendation(
    risk_label: str,
    drug: str,
    gene: str,
    interactions: Optional[List[DrugInteraction]] = None,
    history_flags: Optional[List[HistoryFlag]] = None,
) -> ClinicalRecommendation:
    """
    Build a structured clinical recommendation based on:
      - Rule-engine risk label
      - Detected drug-drug interactions      ← NEW
      - Patient history flags (allergies, conditions)  ← NEW

    Parameters
    ----------
    risk_label      : str – one of Safe, Adjust Dosage, Toxic, Ineffective, Contraindicated, Unknown
    drug            : str – upper-case drug name
    gene            : str – HGNC gene symbol
    interactions    : list of DrugInteraction (may be None)
    history_flags   : list of HistoryFlag (may be None)

    Returns
    -------
    ClinicalRecommendation
    """
    interactions = interactions or []
    history_flags = history_flags or []

    # ── Build history-based warning string ───────────────────────────
    warning_parts = []
    for fl in history_flags:
        warning_parts.append(f"[{fl.severity.value.upper()}] {fl.message}")
    for ix in interactions:
        warning_parts.append(
            f"[DDI-{ix.interaction_severity.value.upper()}] "
            f"{ix.assessed_drug} × {ix.current_medication}: {ix.recommendation}"
        )
    history_warnings = " | ".join(warning_parts) if warning_parts else None

    # ── Check for critical flags that override everything ────────────
    has_allergy = any(f.flag_type == "allergy" for f in history_flags)
    has_contraindicated = any(
        ix.interaction_severity.value == "contraindicated" for ix in interactions
    )

    if has_allergy:
        return ClinicalRecommendation(
            action=f"⛔ STOP — Patient has a documented ALLERGY to {drug}. Do NOT prescribe.",
            alternative_drugs=_ALT_DRUGS.get(drug, []),
            monitoring="Immediate allergy review; document in patient record.",
            history_based_warnings=history_warnings,
        )

    if has_contraindicated or risk_label == "Contraindicated":
        return ClinicalRecommendation(
            action=f"⛔ CONTRAINDICATED — {drug} must not be used due to critical drug interaction.",
            alternative_drugs=_ALT_DRUGS.get(drug, []),
            monitoring="Urgent pharmacist consult; select alternative therapy.",
            history_based_warnings=history_warnings,
        )

    # ── Standard risk-based recommendations ──────────────────────────
    if risk_label == "Safe":
        action = "Continue standard dosing."
        monitoring = "Routine follow-up."
        if warning_parts:
            action += " However, review patient history flags below."
            monitoring = "Enhanced monitoring due to patient history flags."
        return ClinicalRecommendation(
            action=action,
            monitoring=monitoring,
            history_based_warnings=history_warnings,
        )

    if risk_label == "Adjust Dosage":
        action = f"Reduce dose of {drug} per CPIC guidelines for {gene} phenotype."
        if any(ix.interaction_severity.value == "major" for ix in interactions):
            action += " ⚠ Major drug interaction detected — additional dose caution required."
        return ClinicalRecommendation(
            action=action,
            alternative_drugs=_ALT_DRUGS.get(drug, []),
            monitoring="Increased therapeutic drug monitoring recommended.",
            history_based_warnings=history_warnings,
        )

    if risk_label in ("Toxic", "Ineffective"):
        return ClinicalRecommendation(
            action=f"AVOID {drug}. Select alternative therapy.",
            alternative_drugs=_ALT_DRUGS.get(drug, []),
            monitoring="Urgent pharmacist / geneticist consult.",
            history_based_warnings=history_warnings,
        )

    # Unknown or unsupported
    return ClinicalRecommendation(
        action="Insufficient data; use clinical judgement.",
        history_based_warnings=history_warnings,
    )
