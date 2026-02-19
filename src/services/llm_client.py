"""
PharmaGuard — Google Gemini LLM Client Service.

Generates a clinical explanation for a given gene–drug–risk triple and
returns EXACTLY four fields:
    summary · mechanism · justification · recommendation

Enhanced pipeline prompt now includes:
  • gene, diplotype, phenotype
  • detected variant rsIDs and their zygosity
  • the drug name, risk label, and severity
  • patient history (conditions, medications, allergies)  ← NEW
  • drug-drug interactions detected                       ← NEW
  • evidence score and CPIC guideline reference            ← NEW

If ``GEMINI_API_KEY`` is not set **or** the API call fails, a deterministic
fallback is used so the demo always works without a network dependency.
"""

from __future__ import annotations

import json
import logging
from typing import Dict, List, Optional

from src.core.config import get_settings

logger = logging.getLogger(__name__)

# ── Lazy-loaded Gemini model instance ────────────────────────────────────
_model = None


def _get_model():
    """Initialise the Gemini generative model once (singleton)."""
    global _model
    if _model is not None:
        return _model

    settings = get_settings()
    if not settings.gemini_api_key:
        logger.warning(
            "GEMINI_API_KEY not configured — LLM explanations will use "
            "deterministic fallback stubs."
        )
        return None

    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        _model = genai.GenerativeModel(settings.gemini_model)
        logger.info("Gemini model initialised (%s).", settings.gemini_model)
        return _model
    except Exception as exc:
        logger.error("Failed to initialise Gemini: %s", exc)
        return None


# ═══════════════════════════════════════════════════════════════════════════
# Prompt template — enhanced with patient history + interactions + evidence
# ═══════════════════════════════════════════════════════════════════════════

PROMPT_TEMPLATE = """\
You are a clinical pharmacogenomics advisor providing evidence-based \
personalised drug recommendations.

─── PATIENT GENOMIC CONTEXT ───
  • Gene: {gene}
  • Diplotype: {diplotype}
  • Phenotype: {phenotype} metabolizer
  • Detected variants: {variants}

─── DRUG PRESCRIBED ───
  Drug: {drug}

─── RULE-ENGINE ASSESSMENT ───
  • Risk label: {risk_label}
  • Severity: {severity}

─── PATIENT HISTORY ───
{patient_history_block}

─── DRUG INTERACTIONS DETECTED ───
{interactions_block}

─── CLINICAL MODIFIERS APPLIED ───
{modifiers_block}

─── EVIDENCE & ACCURACY ───
  • Evidence level: {evidence_level}
  • CPIC guideline PMID: {guideline_pmid}
  • Overall evidence score: {evidence_score}

INSTRUCTIONS:
1. Incorporate the patient's medical history (conditions, allergies, current \
medications) into your clinical reasoning.
2. If drug interactions were detected, explicitly address them.
3. If clinical modifiers were applied (e.g. liver/kidney impairment, CYP \
inhibitors, age), explain HOW they shifted the risk from the base genomic \
assessment to the final combined risk.
4. Justify the accuracy of your recommendation by citing the evidence level \
and guideline.
5. If the patient has allergies or prior adverse reactions to this drug, \
make that the TOP priority.

Provide a concise, clinically accurate explanation in EXACTLY this JSON \
format and nothing else (no markdown fences, no extra keys):

{{
  "summary": "<2-3 sentence personalised summary incorporating patient history and any modifiers>",
  "mechanism": "<how the gene variant affects drug metabolism, interaction mechanisms, and clinical modifier effects>",
  "justification": "<evidence-based justification citing CPIC level and PMID, plus patient-specific factors>",
  "recommendation": "<actionable personalised recommendation considering history, interactions, modifiers, and genomics>"
}}
"""


# ═══════════════════════════════════════════════════════════════════════════
# Deterministic fallback (always works, no network)
# ═══════════════════════════════════════════════════════════════════════════

def _fallback_explanation(
    gene: str,
    diplotype: str,
    phenotype: str,
    drug: str,
    risk_label: str,
    severity: str,
    variants: str = "",
    patient_history_block: str = "",
    interactions_block: str = "",
    modifiers_block: str = "",  # NEW: clinical modifier logic
    evidence_level: str = "",
    guideline_pmid: str = "",
    evidence_score_str: str = "",
) -> Dict[str, str]:
    """Return a template-based explanation when the LLM is unavailable."""
    history_note = ""
    if patient_history_block and patient_history_block != "No patient history provided.":
        history_note = " Patient history was incorporated into this assessment."
    else:
        history_note = " No patient history was provided; recommendation is genomic-only."

    interaction_note = ""
    if interactions_block and interactions_block != "None detected.":
        interaction_note = (
            f" Drug interaction(s) were detected — review the interactions section."
        )

    # NEW: clinical modifier logic
    modifiers_note = ""
    if modifiers_block and modifiers_block != "No clinical modifiers applied.":
        modifiers_note = (
            " Clinical modifiers were applied that adjusted the base genomic risk."
        )

    evidence_note = ""
    if guideline_pmid:
        evidence_note = f" Supported by CPIC guideline (PMID:{guideline_pmid})."

    return {
        "summary": (
            f"Patient carries {gene} {diplotype} ({phenotype} metabolizer). "
            f"Risk for {drug}: {risk_label} (severity: {severity}). "
            f"Detected variants: {variants or 'none reported'}."
            f"{history_note}"
        ),
        "mechanism": (
            f"{gene} encodes an enzyme involved in the metabolism of {drug}. "
            f"The {diplotype} diplotype results in {phenotype.lower()} enzyme "
            f"activity, altering drug exposure."
            f"{interaction_note}"
            f"{modifiers_note}"
        ),
        "justification": (
            f"CPIC guidelines indicate that {phenotype} metabolizers of {gene} "
            f"are at {risk_label.lower()} risk when taking {drug}. "
            f"Severity is rated {severity}."
            f"{evidence_note}"
            f" Evidence level: {evidence_level or 'N/A'}."
            f" Overall evidence score: {evidence_score_str or 'N/A'}."
        ),
        "recommendation": (
            f"Consult a clinical pharmacist. Consider pharmacogenomic-guided "
            f"dosing adjustment or alternative therapy for {drug}. "
            f"Refer to CPIC guidelines for {gene}."
            f"{' Review flagged drug interactions before prescribing.' if interaction_note else ''}"
            f"{' Clinical modifiers suggest additional caution — see modifier details.' if modifiers_note else ''}"
        ),
    }


# ═══════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════

async def generate_explanation(
    gene: str,
    diplotype: str,
    phenotype: str,
    drug: str,
    risk_label: str,
    severity: str,
    variant_details: List[Dict[str, str]] | None = None,
    patient_history_block: str = "No patient history provided.",
    interactions_block: str = "None detected.",
    modifiers_block: str = "No clinical modifiers applied.",  # NEW: clinical modifier logic
    evidence_level: str = "N/A",
    guideline_pmid: str = "",
    evidence_score_str: str = "N/A",
) -> Dict[str, str]:
    """
    Call Google Gemini to produce a clinical explanation.

    Parameters
    ----------
    gene, diplotype, phenotype, drug, risk_label, severity
        Core pharmacogenomic context strings.
    variant_details
        Optional list of dicts with keys ``rsid``, ``genotype``, ``zygosity``
        for richer LLM prompts.
    patient_history_block
        Formatted patient history text for the prompt.
    interactions_block
        Formatted drug interaction text for the prompt.
    modifiers_block
        Formatted clinical modifiers text for the prompt.
    evidence_level
        CPIC evidence level string (A/B/C/D).
    guideline_pmid
        PubMed ID of the relevant CPIC guideline.
    evidence_score_str
        Human-readable evidence score string.

    Returns
    -------
    dict with keys: summary, mechanism, justification, recommendation
    """
    # Build a human-readable variant summary for the prompt
    if variant_details:
        parts = []
        for v in variant_details:
            rsid = v.get("rsid", "?")
            gt = v.get("genotype", "?")
            zyg = v.get("zygosity", "?")
            parts.append(f"{rsid} (GT={gt}, {zyg})")
        variants_str = "; ".join(parts)
    else:
        variants_str = "none reported"

    model = _get_model()
    if model is None:
        return _fallback_explanation(
            gene, diplotype, phenotype, drug, risk_label, severity, variants_str,
            patient_history_block, interactions_block, modifiers_block,
            evidence_level, guideline_pmid, evidence_score_str,
        )

    prompt = PROMPT_TEMPLATE.format(
        gene=gene,
        diplotype=diplotype,
        phenotype=phenotype,
        drug=drug,
        risk_label=risk_label,
        severity=severity,
        variants=variants_str,
        patient_history_block=patient_history_block,
        interactions_block=interactions_block,
        modifiers_block=modifiers_block,
        evidence_level=evidence_level,
        guideline_pmid=guideline_pmid,
        evidence_score=evidence_score_str,
    )

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Strip markdown code fences the model sometimes wraps
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3].strip()
        if text.startswith("json"):
            text = text[4:].strip()

        parsed = json.loads(text)

        # Ensure all four required keys are present
        for key in ("summary", "mechanism", "justification", "recommendation"):
            parsed.setdefault(key, "")
        return parsed

    except json.JSONDecodeError as exc:
        logger.warning("Gemini returned non-JSON response: %s", exc)
    except Exception as exc:
        logger.warning("Gemini API call failed: %s", exc)

    # Fallback on any failure
    return _fallback_explanation(
        gene, diplotype, phenotype, drug, risk_label, severity, variants_str,
        patient_history_block, interactions_block, modifiers_block,
        evidence_level, guideline_pmid, evidence_score_str,
    )
