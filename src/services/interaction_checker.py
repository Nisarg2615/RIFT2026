"""
PharmaGuard — Drug-Drug Interaction Checker.

Checks for clinically significant interactions between the patient's
current medications and each drug being evaluated by PharmaGuard.

Pipeline stage:  Risk + **Interactions** → Evidence Score → LLM → JSON

Data Source
───────────
The interaction table below is compiled from:
  • FDA drug interaction guidance
  • CPIC guideline supplementary tables
  • Lexicomp / Micromedex known interaction pairs

Each entry records: (severity, interaction type, description, recommendation).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from src.models.schemas import (
    DrugInteraction,
    HistoryFlag,
    InteractionSeverity,
    PatientHistory,
    Severity,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Known interaction database  (assessed_drug ↔ current_medication)
#
# Key = frozenset({DRUG_A_UPPER, DRUG_B_UPPER})
# Val = (InteractionSeverity, type, description, recommendation)
# ═══════════════════════════════════════════════════════════════════════════

_InteractionRow = Tuple[InteractionSeverity, str, str, str]

_INTERACTION_DB: Dict[frozenset, _InteractionRow] = {
    # ── WARFARIN interactions ────────────────────────────────────────
    frozenset({"WARFARIN", "ASPIRIN"}): (
        InteractionSeverity.MAJOR,
        "pharmacodynamic",
        "Both agents inhibit hemostasis; combined use significantly increases bleeding risk.",
        "Avoid combination or monitor INR closely; consider gastroprotection.",
    ),
    frozenset({"WARFARIN", "IBUPROFEN"}): (
        InteractionSeverity.MAJOR,
        "pharmacodynamic",
        "NSAIDs increase bleeding risk and can displace warfarin from protein binding.",
        "Avoid concurrent use; use acetaminophen for analgesia instead.",
    ),
    frozenset({"WARFARIN", "NAPROXEN"}): (
        InteractionSeverity.MAJOR,
        "pharmacodynamic",
        "NSAIDs increase bleeding risk when combined with anticoagulants.",
        "Avoid concurrent use; choose acetaminophen as alternative analgesic.",
    ),
    frozenset({"WARFARIN", "FLUCONAZOLE"}): (
        InteractionSeverity.MAJOR,
        "pharmacokinetic (CYP2C9 inhibition)",
        "Fluconazole inhibits CYP2C9, the primary enzyme metabolising warfarin, "
        "leading to supratherapeutic INR and bleeding risk.",
        "Reduce warfarin dose by 25-50%; monitor INR within 3-5 days.",
    ),
    frozenset({"WARFARIN", "AMIODARONE"}): (
        InteractionSeverity.MAJOR,
        "pharmacokinetic (CYP2C9/1A2/3A4 inhibition)",
        "Amiodarone inhibits multiple CYP enzymes metabolising warfarin, "
        "increasing anticoagulant effect for weeks.",
        "Reduce warfarin dose by ~33-50%; monitor INR weekly for first month.",
    ),
    frozenset({"WARFARIN", "METFORMIN"}): (
        InteractionSeverity.MINOR,
        "pharmacodynamic",
        "Metformin has minimal interaction with warfarin; occasional reports of modestly altered INR.",
        "Routine INR monitoring is sufficient; no dose adjustment needed.",
    ),

    # ── CODEINE interactions ─────────────────────────────────────────
    frozenset({"CODEINE", "FLUOXETINE"}): (
        InteractionSeverity.MAJOR,
        "pharmacokinetic (CYP2D6 inhibition)",
        "Fluoxetine strongly inhibits CYP2D6, blocking conversion of codeine "
        "to morphine, rendering codeine ineffective.",
        "Choose an alternative analgesic not dependent on CYP2D6 activation.",
    ),
    frozenset({"CODEINE", "PAROXETINE"}): (
        InteractionSeverity.MAJOR,
        "pharmacokinetic (CYP2D6 inhibition)",
        "Paroxetine strongly inhibits CYP2D6, blocking codeine activation to morphine.",
        "Use alternative analgesic; avoid codeine in patients on paroxetine.",
    ),
    frozenset({"CODEINE", "DIAZEPAM"}): (
        InteractionSeverity.MAJOR,
        "pharmacodynamic (CNS depression)",
        "Combined opioid + benzodiazepine use increases risk of fatal respiratory depression.",
        "Avoid combination; if essential, use lowest effective doses and monitor closely.",
    ),
    frozenset({"CODEINE", "TRAMADOL"}): (
        InteractionSeverity.MODERATE,
        "pharmacodynamic (additive opioid effect)",
        "Both are opioid analgesics; combined use increases CNS/respiratory depression risk.",
        "Avoid concurrent use; choose one opioid analgesic.",
    ),

    # ── CLOPIDOGREL interactions ─────────────────────────────────────
    frozenset({"CLOPIDOGREL", "OMEPRAZOLE"}): (
        InteractionSeverity.MAJOR,
        "pharmacokinetic (CYP2C19 inhibition)",
        "Omeprazole inhibits CYP2C19, reducing clopidogrel activation to its "
        "active metabolite, diminishing antiplatelet efficacy.",
        "Switch PPI to pantoprazole (minimal CYP2C19 inhibition) or use H2-blocker.",
    ),
    frozenset({"CLOPIDOGREL", "ESOMEPRAZOLE"}): (
        InteractionSeverity.MAJOR,
        "pharmacokinetic (CYP2C19 inhibition)",
        "Esomeprazole inhibits CYP2C19, reducing clopidogrel activation.",
        "Switch to pantoprazole or an H2 receptor antagonist.",
    ),
    frozenset({"CLOPIDOGREL", "ASPIRIN"}): (
        InteractionSeverity.MODERATE,
        "pharmacodynamic (additive antiplatelet)",
        "Dual antiplatelet therapy is intentional in many protocols but increases bleeding risk.",
        "If prescribed together, ensure indication (e.g. post-ACS) and monitor for bleeding.",
    ),
    frozenset({"CLOPIDOGREL", "WARFARIN"}): (
        InteractionSeverity.MAJOR,
        "pharmacodynamic (anticoagulant + antiplatelet)",
        "Triple or dual antithrombotic therapy markedly increases haemorrhage risk.",
        "Minimise duration of combined use; add PPI for gastroprotection.",
    ),

    # ── SIMVASTATIN interactions ─────────────────────────────────────
    frozenset({"SIMVASTATIN", "AMLODIPINE"}): (
        InteractionSeverity.MODERATE,
        "pharmacokinetic (CYP3A4 inhibition)",
        "Amlodipine increases simvastatin exposure ~1.5-2×, raising myopathy risk.",
        "Limit simvastatin dose to 20 mg/day when combined with amlodipine.",
    ),
    frozenset({"SIMVASTATIN", "CLARITHROMYCIN"}): (
        InteractionSeverity.CONTRAINDICATED,
        "pharmacokinetic (strong CYP3A4 inhibition)",
        "Clarithromycin dramatically increases simvastatin levels, high risk of rhabdomyolysis.",
        "CONTRAINDICATED — suspend simvastatin during clarithromycin course.",
    ),
    frozenset({"SIMVASTATIN", "ERYTHROMYCIN"}): (
        InteractionSeverity.MAJOR,
        "pharmacokinetic (CYP3A4 inhibition)",
        "Erythromycin increases simvastatin levels and risk of rhabdomyolysis.",
        "Suspend simvastatin during erythromycin therapy.",
    ),
    frozenset({"SIMVASTATIN", "GEMFIBROZIL"}): (
        InteractionSeverity.CONTRAINDICATED,
        "pharmacokinetic (OATP1B1 inhibition + glucuronidation)",
        "Gemfibrozil increases simvastatin acid AUC ~2.8×; high rhabdomyolysis risk.",
        "CONTRAINDICATED — use fenofibrate if fibrate is needed.",
    ),

    # ── AZATHIOPRINE interactions ────────────────────────────────────
    frozenset({"AZATHIOPRINE", "ALLOPURINOL"}): (
        InteractionSeverity.MAJOR,
        "pharmacokinetic (xanthine oxidase inhibition)",
        "Allopurinol blocks azathioprine breakdown, causing severe myelosuppression.",
        "Reduce azathioprine dose by 67-75% if allopurinol is essential; monitor CBC weekly.",
    ),
    frozenset({"AZATHIOPRINE", "FEBUXOSTAT"}): (
        InteractionSeverity.MAJOR,
        "pharmacokinetic (xanthine oxidase inhibition)",
        "Same mechanism as allopurinol interaction — risk of severe pancytopenia.",
        "Avoid combination or drastically reduce azathioprine dose.",
    ),

    # ── FLUOROURACIL interactions ────────────────────────────────────
    frozenset({"FLUOROURACIL", "METHOTREXATE"}): (
        InteractionSeverity.MAJOR,
        "pharmacodynamic (additive cytotoxicity)",
        "Both are antimetabolites; combined use intensifies myelosuppression and mucositis.",
        "Sequence and timing critical; follow established oncology protocols.",
    ),
    frozenset({"FLUOROURACIL", "WARFARIN"}): (
        InteractionSeverity.MAJOR,
        "pharmacokinetic",
        "Fluorouracil increases warfarin effect via protein binding displacement and reduced metabolism.",
        "Monitor INR closely; consider LMWH as alternative anticoagulation.",
    ),
}


# ═══════════════════════════════════════════════════════════════════════════
# Condition-based contraindications
#
# Maps (drug, condition_keyword) → warning message
# ═══════════════════════════════════════════════════════════════════════════

_CONDITION_CONTRAINDICATIONS: Dict[Tuple[str, str], Tuple[Severity, str]] = {
    ("WARFARIN", "liver disease"):    (Severity.CRITICAL, "Warfarin metabolism is hepatic; liver disease increases bleeding risk dramatically."),
    ("WARFARIN", "hepatic"):          (Severity.CRITICAL, "Impaired hepatic function alters warfarin clearance."),
    ("WARFARIN", "peptic ulcer"):     (Severity.HIGH, "Active GI bleeding or ulcer history elevates warfarin bleeding risk."),
    ("WARFARIN", "gi bleeding"):      (Severity.CRITICAL, "History of GI bleeding is a relative contraindication to warfarin."),
    ("CODEINE", "respiratory"):       (Severity.HIGH, "Opioids can worsen respiratory depression in patients with respiratory disease."),
    ("CODEINE", "asthma"):            (Severity.MODERATE, "Codeine may trigger bronchospasm in asthmatic patients."),
    ("CODEINE", "sleep apnea"):       (Severity.HIGH, "Opioids exacerbate obstructive sleep apnoea."),
    ("SIMVASTATIN", "liver disease"): (Severity.HIGH, "Statins are hepatically metabolised; contraindicated in active liver disease."),
    ("SIMVASTATIN", "myopathy"):      (Severity.HIGH, "History of statin-induced myopathy increases rhabdomyolysis risk."),
    ("SIMVASTATIN", "rhabdomyolysis"):(Severity.CRITICAL, "Prior rhabdomyolysis is a contraindication to simvastatin."),
    ("AZATHIOPRINE", "bone marrow"):  (Severity.CRITICAL, "Azathioprine causes myelosuppression; avoid in bone marrow failure."),
    ("AZATHIOPRINE", "leukopenia"):   (Severity.HIGH, "Azathioprine worsens leukopenia."),
    ("FLUOROURACIL", "bone marrow"):  (Severity.CRITICAL, "Fluorouracil causes severe myelosuppression."),
    ("FLUOROURACIL", "pregnancy"):    (Severity.CRITICAL, "Fluorouracil is teratogenic; absolutely contraindicated in pregnancy."),
    ("CLOPIDOGREL", "bleeding"):      (Severity.HIGH, "Active bleeding is a contraindication to antiplatelet therapy."),
}


# ═══════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════

def check_drug_interactions(
    drug: str,
    patient_history: PatientHistory,
) -> Tuple[List[DrugInteraction], List[HistoryFlag]]:
    """
    Check for drug-drug interactions AND patient-history-based flags.

    Parameters
    ----------
    drug            : str – upper-case drug name being evaluated
    patient_history : PatientHistory – patient's medical context

    Returns
    -------
    (interactions, flags) tuple
        interactions : list of DrugInteraction objects
        flags        : list of HistoryFlag warnings
    """
    drug_upper = drug.strip().upper()
    interactions: List[DrugInteraction] = []
    flags: List[HistoryFlag] = []

    # ── 1. Drug-drug interactions ────────────────────────────────────
    for med in patient_history.current_medications:
        med_upper = med.strip().upper()
        if not med_upper:
            continue

        pair = frozenset({drug_upper, med_upper})
        if pair in _INTERACTION_DB:
            sev, itype, desc, rec = _INTERACTION_DB[pair]
            interactions.append(DrugInteraction(
                current_medication=med.strip(),
                assessed_drug=drug_upper,
                interaction_severity=sev,
                interaction_type=itype,
                description=desc,
                recommendation=rec,
            ))
            logger.warning(
                "DDI detected: %s × %s → %s", drug_upper, med_upper, sev.value,
            )

    # ── 2. Allergy check ────────────────────────────────────────────
    for allergy in patient_history.allergies:
        allergy_upper = allergy.strip().upper()
        if allergy_upper and allergy_upper == drug_upper:
            flags.append(HistoryFlag(
                flag_type="allergy",
                severity=Severity.CRITICAL,
                message=f"⚠️ ALLERGY ALERT: Patient has a documented allergy to {drug}.",
            ))
            logger.warning("Allergy match for %s", drug_upper)

    # ── 3. Prior adverse reactions ───────────────────────────────────
    for reaction in patient_history.prior_adverse_reactions:
        reaction_upper = reaction.strip().upper()
        if drug_upper in reaction_upper:
            flags.append(HistoryFlag(
                flag_type="prior_reaction",
                severity=Severity.HIGH,
                message=f"Prior adverse reaction reported involving {drug}: '{reaction}'.",
            ))

    # ── 4. Condition-based contraindications ─────────────────────────
    conditions_lower = " ".join(c.lower() for c in patient_history.conditions)
    for (cond_drug, keyword), (sev, msg) in _CONDITION_CONTRAINDICATIONS.items():
        if cond_drug == drug_upper and keyword in conditions_lower:
            flags.append(HistoryFlag(
                flag_type="condition_risk",
                severity=sev,
                message=msg,
            ))

    # ── 5. Age-based warnings ────────────────────────────────────────
    if patient_history.age is not None:
        if patient_history.age >= 75:
            if drug_upper in {"WARFARIN", "CLOPIDOGREL"}:
                flags.append(HistoryFlag(
                    flag_type="age_risk",
                    severity=Severity.HIGH,
                    message=f"Patient age ≥75: increased bleeding risk with {drug}; "
                            f"consider dose reduction or closer monitoring.",
                ))
            if drug_upper in {"CODEINE"}:
                flags.append(HistoryFlag(
                    flag_type="age_risk",
                    severity=Severity.MODERATE,
                    message=f"Patient age ≥75: opioid sensitivity increased; "
                            f"start with lower codeine dose.",
                ))
        if patient_history.age < 18:
            if drug_upper in {"CODEINE"}:
                flags.append(HistoryFlag(
                    flag_type="age_risk",
                    severity=Severity.HIGH,
                    message="Codeine is not recommended for patients under 18 "
                            "(FDA boxed warning for paediatric respiratory depression).",
                ))

    # ── 6. Kidney function warnings ──────────────────────────────────
    if patient_history.kidney_function and patient_history.kidney_function != "normal":
        renal = patient_history.kidney_function.lower()
        if drug_upper == "WARFARIN" and "severe" in renal or "dialysis" in renal:
            flags.append(HistoryFlag(
                flag_type="organ_risk",
                severity=Severity.HIGH,
                message="Renal impairment alters warfarin pharmacokinetics; dose adjustment and closer INR monitoring recommended.",
            ))
        if drug_upper == "CODEINE" and ("moderate" in renal or "severe" in renal or "dialysis" in renal):
            flags.append(HistoryFlag(
                flag_type="organ_risk",
                severity=Severity.HIGH,
                message="Renal impairment causes accumulation of active codeine metabolites; reduce dose or avoid.",
            ))
        if drug_upper == "FLUOROURACIL" and ("severe" in renal or "dialysis" in renal):
            flags.append(HistoryFlag(
                flag_type="organ_risk",
                severity=Severity.HIGH,
                message="Severe renal impairment increases fluorouracil toxicity risk; dose reduction required.",
            ))

    # ── 7. Liver function warnings ───────────────────────────────────
    if patient_history.liver_function and patient_history.liver_function != "normal":
        hepatic = patient_history.liver_function.lower()
        if drug_upper == "WARFARIN":
            flags.append(HistoryFlag(
                flag_type="organ_risk",
                severity=Severity.CRITICAL,
                message=f"Hepatic impairment ({patient_history.liver_function}): warfarin metabolism is hepatic — dramatically increased bleeding risk.",
            ))
        if drug_upper == "SIMVASTATIN":
            flags.append(HistoryFlag(
                flag_type="organ_risk",
                severity=Severity.HIGH,
                message=f"Hepatic impairment ({patient_history.liver_function}): simvastatin is contraindicated in active liver disease.",
            ))
        if drug_upper == "CODEINE":
            flags.append(HistoryFlag(
                flag_type="organ_risk",
                severity=Severity.HIGH,
                message=f"Hepatic impairment ({patient_history.liver_function}): codeine requires hepatic metabolism to morphine — reduced efficacy and unpredictable response.",
            ))
        if drug_upper == "AZATHIOPRINE" and ("moderate" in hepatic or "severe" in hepatic):
            flags.append(HistoryFlag(
                flag_type="organ_risk",
                severity=Severity.HIGH,
                message=f"Hepatic impairment ({patient_history.liver_function}): azathioprine is hepatotoxic; dose reduction or avoidance recommended.",
            ))

    # ── 8. Smoking & alcohol warnings ────────────────────────────────
    if patient_history.smoking_status == "current":
        if drug_upper == "CLOPIDOGREL":
            flags.append(HistoryFlag(
                flag_type="lifestyle_risk",
                severity=Severity.MODERATE,
                message="Smoking induces CYP1A2 which may increase clopidogrel bioactivation, but cardiovascular risk is elevated.",
            ))
        if drug_upper == "WARFARIN":
            flags.append(HistoryFlag(
                flag_type="lifestyle_risk",
                severity=Severity.MODERATE,
                message="Smoking induces CYP1A2 affecting warfarin metabolism; dose adjustments may be needed.",
            ))

    if patient_history.alcohol_use == "heavy":
        if drug_upper in {"WARFARIN", "SIMVASTATIN", "AZATHIOPRINE", "FLUOROURACIL"}:
            flags.append(HistoryFlag(
                flag_type="lifestyle_risk",
                severity=Severity.HIGH,
                message=f"Heavy alcohol use increases hepatotoxicity risk with {drug} and may alter drug metabolism.",
            ))
        if drug_upper == "CODEINE":
            flags.append(HistoryFlag(
                flag_type="lifestyle_risk",
                severity=Severity.CRITICAL,
                message="Heavy alcohol use with codeine: severe risk of CNS depression, respiratory failure, and death.",
            ))

    return interactions, flags
