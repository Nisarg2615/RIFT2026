"""
PharmaGuard — Clinical Risk Modifiers.

# NEW: clinical modifier logic

Applies patient-history-based clinical modifiers to the base
genomic risk assessment.  ADDITIVE only — never removes or
replaces the base genomic risk.

Rules
─────
1. Hepatic impairment  + PM/IM           → escalate severity
2. Severe renal impairment + renal drugs  → escalate severity
3. CYP inhibitor co-medications           → upgrade risk label
4. Advanced age (≥ 75) + ≥ MODERATE       → escalate severity
5. Low body weight (< 50 kg) + PM         → dose flag
6. Borderline activity score (IM near PM) → monitoring flag
"""

from __future__ import annotations

import logging
from typing import Dict, List, Set, Tuple

from src.models.schemas import PatientHistory, RiskLabel, Severity

logger = logging.getLogger(__name__)


# ── Severity escalation ladder ───────────────────────────────────────────

_SEV_ORDER = [
    Severity.NONE, Severity.LOW, Severity.MODERATE,
    Severity.HIGH, Severity.CRITICAL,
]


def _escalate_sev(current: Severity, steps: int = 1) -> Severity:
    idx = _SEV_ORDER.index(current)
    return _SEV_ORDER[min(idx + steps, len(_SEV_ORDER) - 1)]


# ── Risk label escalation map ───────────────────────────────────────────

_RISK_UP: Dict[RiskLabel, RiskLabel] = {
    RiskLabel.SAFE:            RiskLabel.ADJUST_DOSAGE,
    RiskLabel.ADJUST_DOSAGE:   RiskLabel.TOXIC,
    RiskLabel.INEFFECTIVE:     RiskLabel.CONTRAINDICATED,
    RiskLabel.TOXIC:           RiskLabel.CONTRAINDICATED,
    RiskLabel.CONTRAINDICATED: RiskLabel.CONTRAINDICATED,
    RiskLabel.UNKNOWN:         RiskLabel.UNKNOWN,
}


# ── Known CYP inhibitors ────────────────────────────────────────────────

_CYP_INHIBITORS: Dict[str, Set[str]] = {
    "CYP2D6":  {"FLUOXETINE", "PAROXETINE", "BUPROPION", "QUINIDINE", "TERBINAFINE"},
    "CYP2C19": {"OMEPRAZOLE", "ESOMEPRAZOLE", "FLUCONAZOLE", "FLUVOXAMINE", "TICLOPIDINE"},
    "CYP2C9":  {"FLUCONAZOLE", "AMIODARONE", "FLUVASTATIN", "MICONAZOLE"},
    "CYP3A4":  {"CLARITHROMYCIN", "ERYTHROMYCIN", "KETOCONAZOLE", "ITRACONAZOLE", "RITONAVIR"},
}

_CYP3A4_RELEVANT_GENES: Set[str] = {"SLCO1B1"}

# ── Drugs with significant renal clearance ──────────────────────────────

_RENAL_DRUGS: Set[str] = {"FLUOROURACIL", "AZATHIOPRINE"}


# ═══════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════

def apply_clinical_modifiers(
    risk_label: RiskLabel,
    severity: Severity,
    confidence: float,
    patient_history: PatientHistory,
    gene: str,
    phenotype: str,
    drug: str,
    activity_score: float = 2.0,
) -> Tuple[RiskLabel, Severity, float, List[dict]]:
    """
    Layer clinical modifiers on top of the base genomic risk.

    # NEW: clinical modifier logic

    Returns
    -------
    (adjusted_risk, adjusted_severity, adjusted_confidence, modifiers)
        modifiers : list of dicts matching ClinicalModifier schema
    """
    mods: List[dict] = []
    r, s, c = risk_label, severity, confidence
    drug_u = drug.strip().upper()
    gene_u = gene.strip().upper()
    pheno_u = phenotype.strip().upper()

    # ── 1  Hepatic impairment + PM/IM ───────────────────────────────
    if patient_history.liver_function:
        lf = patient_history.liver_function.lower()
        if any(k in lf for k in ("moderate", "severe", "child-pugh b", "child-pugh c")):
            if pheno_u in ("PM", "IM"):
                old = s
                s = _escalate_sev(s)
                if s != old:
                    mods.append(dict(
                        modifier_type="liver_impairment",
                        description=(
                            f"Hepatic impairment ({patient_history.liver_function}) "
                            f"with {pheno_u} metabolizer increases drug exposure risk."
                        ),
                        impact="severity_escalated",
                        original_value=old.value,
                        adjusted_value=s.value,
                    ))
                    logger.info("Modifier: liver + %s → sev %s→%s", pheno_u, old.value, s.value)

    # ── 2  Severe renal impairment + renal drugs ────────────────────
    if patient_history.kidney_function:
        kf = patient_history.kidney_function.lower()
        if any(k in kf for k in ("severe", "dialysis")):
            if drug_u in _RENAL_DRUGS:
                old = s
                s = _escalate_sev(s)
                if s != old:
                    mods.append(dict(
                        modifier_type="renal_impairment",
                        description=(
                            f"Severe renal impairment ({patient_history.kidney_function}) "
                            f"reduces clearance of {drug_u}, increasing toxicity risk."
                        ),
                        impact="severity_escalated",
                        original_value=old.value,
                        adjusted_value=s.value,
                    ))

    # ── 3  CYP inhibitor co-medications → risk upgrade ──────────────
    meds_upper = {m.strip().upper() for m in patient_history.current_medications}
    inhibiting = meds_upper & _CYP_INHIBITORS.get(gene_u, set())
    if gene_u in _CYP3A4_RELEVANT_GENES:
        inhibiting |= meds_upper & _CYP_INHIBITORS.get("CYP3A4", set())

    if inhibiting:
        old_r = r
        r = _RISK_UP.get(r, r)
        c = max(c - 0.05, 0.40)
        if r != old_r:
            mods.append(dict(
                modifier_type="cyp_inhibitor",
                description=(
                    f"CYP inhibitor(s) detected: {', '.join(sorted(inhibiting))}. "
                    f"Functionally worsens {gene_u} metabolizer status for {drug_u}."
                ),
                impact="risk_upgraded",
                original_value=old_r.value,
                adjusted_value=r.value,
            ))

    # ── 4  Advanced age (≥ 75) + moderate/high severity ─────────────
    if patient_history.age is not None and patient_history.age >= 75:
        if s in (Severity.MODERATE, Severity.HIGH):
            old = s
            s = _escalate_sev(s)
            if s != old:
                mods.append(dict(
                    modifier_type="advanced_age",
                    description=(
                        f"Patient age ({patient_history.age}) increases vulnerability "
                        f"to adverse effects; pharmacokinetics altered in elderly."
                    ),
                    impact="severity_escalated",
                    original_value=old.value,
                    adjusted_value=s.value,
                ))

    # ── 5  Low body weight + PM → dose flag ─────────────────────────
    if (patient_history.weight_kg is not None
            and patient_history.weight_kg < 50.0
            and pheno_u == "PM"):
        mods.append(dict(
            modifier_type="low_body_weight",
            description=(
                f"Low body weight ({patient_history.weight_kg} kg) with PM phenotype "
                f"suggests further dose reduction may be needed."
            ),
            impact="dose_flag",
            original_value=s.value,
            adjusted_value=s.value,
        ))

    # ── 6  Borderline activity score ─────────────────────────────────
    if 0.0 < activity_score <= 0.5 and pheno_u == "IM":
        mods.append(dict(
            modifier_type="borderline_phenotype",
            description=(
                f"Activity score ({activity_score:.2f}) is borderline PM/IM. "
                f"Consider PM-level precautions."
            ),
            impact="monitoring_recommended",
            original_value=pheno_u,
            adjusted_value=f"IM (activity={activity_score:.2f}, near-PM)",
        ))

    return r, s, c, mods
