"""
PharmaGuard — /analyze route.

POST /api/analyze
    Accepts:  VCF file  +  comma-separated drug names  +  optional patient ID
              +  optional patient history (JSON)         ← NEW
    Returns:  List[PharmaGuardResult]  (one entry per drug)

Enhanced pipeline:
    VCF + Patient History → Parse → Risk + Interactions → Evidence Score → LLM → JSON
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from src.models.schemas import (
    ClinicalModifier,  # NEW: clinical modifier logic
    ClinicalRecommendation,
    DetectedVariant,
    DrugInteraction,
    EvidenceScore,
    HistoryFlag,
    LLMExplanation,
    PatientHistory,
    PharmaGuardResult,
    PharmacogenomicProfile,
    Phenotype,
    QualityMetrics,
    RiskAssessment,
    RiskLabel,
    Severity,
    Zygosity,
)
from src.services.evidence_scorer import compute_evidence_score
from src.services.interaction_checker import check_drug_interactions
from src.services.llm_client import generate_explanation
from src.services.rules_engine import assess_risk, get_primary_gene
from src.services.vcf_parser import parse_vcf
from src.utils.helpers import build_clinical_recommendation
# NEW: clinical modifier logic
from src.services.phenotype_helper import refine_phenotype
from src.services.clinical_modifiers import apply_clinical_modifiers

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["analysis"])


# ═══════════════════════════════════════════════════════════════════════════
# Helper: build human-readable blocks for LLM prompt
# ═══════════════════════════════════════════════════════════════════════════

def _format_history_block(history: PatientHistory) -> str:
    """Format patient history into a readable prompt block."""
    parts = []
    # Demographics
    if history.age is not None:
        parts.append(f"  • Age: {history.age}")
    if history.gender:
        parts.append(f"  • Gender: {history.gender}")
    if history.weight_kg is not None:
        parts.append(f"  • Weight: {history.weight_kg} kg")
    if history.ethnicity:
        parts.append(f"  • Ethnicity: {history.ethnicity}")
    if history.blood_group:
        parts.append(f"  • Blood Group: {history.blood_group}")
    # Medical history
    if history.conditions:
        parts.append(f"  • Conditions: {', '.join(history.conditions)}")
    if history.current_medications:
        parts.append(f"  • Current medications: {', '.join(history.current_medications)}")
    if history.allergies:
        parts.append(f"  • Drug allergies: {', '.join(history.allergies)}")
    if history.prior_adverse_reactions:
        parts.append(f"  • Prior adverse reactions: {', '.join(history.prior_adverse_reactions)}")
    # Organ function
    if history.kidney_function:
        parts.append(f"  • Kidney function: {history.kidney_function}")
    if history.liver_function:
        parts.append(f"  • Liver function: {history.liver_function}")
    # Lifestyle
    if history.smoking_status:
        parts.append(f"  • Smoking status: {history.smoking_status}")
    if history.alcohol_use:
        parts.append(f"  • Alcohol use: {history.alcohol_use}")
    return "\n".join(parts) if parts else "No patient history provided."


def _format_interactions_block(interactions: List[DrugInteraction], flags: List[HistoryFlag]) -> str:
    """Format interactions and history flags into a readable prompt block."""
    parts = []
    for ix in interactions:
        parts.append(
            f"  ⚠ {ix.assessed_drug} × {ix.current_medication}: "
            f"{ix.interaction_severity.value.upper()} — {ix.description}"
        )
    for fl in flags:
        parts.append(f"  🚩 [{fl.flag_type}] {fl.message}")
    return "\n".join(parts) if parts else "None detected."


# NEW: clinical modifier logic
def _format_modifiers_block(modifiers: list) -> str:
    """Format clinical modifiers into a readable prompt block."""
    if not modifiers:
        return "No clinical modifiers applied."
    parts = []
    for m in modifiers:
        parts.append(
            f"  🔧 [{m['modifier_type']}] {m['description']} "
            f"({m['impact']}: {m['original_value']} → {m['adjusted_value']})"
        )
    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════════════
# POST /api/analyze
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/analyze", response_model=List[PharmaGuardResult])
async def analyze(
    vcf_file: UploadFile = File(..., description="VCF v4.2 file (≤ 5 MB)"),
    drugs: str = Form(..., description="Comma-separated drug names"),
    patient_id: str = Form(default="", description="Optional patient identifier"),
    patient_history: str = Form(default="", description="Optional JSON patient history"),
):
    """
    Core analysis endpoint — enhanced pipeline.

    1. Validates & parses the uploaded VCF.
    2. Parses optional patient history JSON.
    3. For each requested drug:
       a. Looks up the primary gene and inferred phenotype.
       b. Calls the rules engine for risk assessment.
       c. Checks drug-drug interactions + history flags.   ← NEW
       d. Computes evidence-based accuracy score.           ← NEW
       e. Calls the Gemini LLM (with full context).
    4. Returns deterministic JSON matching PharmaGuardResult schema.
    """
    # ── Input validation ─────────────────────────────────────────────
    if not vcf_file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    raw = await vcf_file.read()
    if len(raw) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    drug_list = [d.strip().upper() for d in drugs.split(",") if d.strip()]
    if not drug_list:
        raise HTTPException(status_code=400, detail="At least one drug name is required.")

    pid = patient_id.strip() or f"PATIENT_{uuid.uuid4().hex[:6].upper()}"

    # ── Parse patient history (optional JSON) ────────────────────────
    history = PatientHistory()
    has_history = False
    if patient_history.strip():
        try:
            history_data = json.loads(patient_history)
            history = PatientHistory(**history_data)
            has_history = True
            logger.info(
                "Patient history loaded: %d conditions, %d meds, %d allergies",
                len(history.conditions),
                len(history.current_medications),
                len(history.allergies),
            )
        except (json.JSONDecodeError, Exception) as exc:
            logger.warning("Failed to parse patient_history JSON: %s", exc)
            # Continue without history rather than failing the whole request

    # ── Parse VCF ────────────────────────────────────────────────────
    vcf = parse_vcf(raw)
    if not vcf.success:
        raise HTTPException(status_code=422, detail=f"VCF parsing failed: {vcf.error}")

    logger.info(
        "VCF parsed — %d variants across genes %s",
        len(vcf.variants),
        list(vcf.gene_variants.keys()),
    )

    # ── Build one result per drug (full pipeline) ────────────────────
    results: List[PharmaGuardResult] = []

    for drug in drug_list:
        gene = get_primary_gene(drug)

        if gene is None:
            results.append(_unknown_result(pid, drug, vcf.success, has_history))
            continue

        # ── STAGE 1: Phenotype from VCF ─────────────────────────────
        phenotype_str = vcf.gene_phenotypes.get(gene, "Unknown")
        phenotype_enum = (
            Phenotype(phenotype_str)
            if phenotype_str in [p.value for p in Phenotype]
            else Phenotype.UNKNOWN
        )

        # ── STAGE 2: Risk assessment ────────────────────────────────
        risk_label, severity, confidence = assess_risk(drug, phenotype_str)
        # ── NEW STAGE 2a: Phenotype refinement (activity score) ─────
        pathogenic_ct = vcf.gene_pathogenic_count.get(gene, 0)
        hom_alt_ct = vcf.gene_hom_alt_count.get(gene, 0)
        refined_phenotype, activity_score = refine_phenotype(
            gene, phenotype_str, pathogenic_ct, hom_alt_ct,
        )

        # Keep base risk for display, then apply clinical modifiers
        base_risk_label = risk_label
        base_severity = severity

        # ── NEW STAGE 2b: Clinical modifiers ────────────────────────────
        risk_label, severity, confidence, clinical_mods = apply_clinical_modifiers(
            risk_label=risk_label,
            severity=severity,
            confidence=confidence,
            patient_history=history,
            gene=gene,
            phenotype=refined_phenotype,
            drug=drug,
            activity_score=activity_score,
        )
        # ── STAGE 3: Drug interactions + History flags  ← NEW ───────
        interactions, history_flags = check_drug_interactions(drug, history)

        # Escalate risk if critical interactions found
        if any(ix.interaction_severity.value == "contraindicated" for ix in interactions):
            from src.models.schemas import RiskLabel as RL
            risk_label = RL.CONTRAINDICATED
            severity = Severity.CRITICAL
            confidence = max(confidence, 0.95)

        # ── STAGE 4: Evidence scoring  ← NEW ────────────────────────
        gene_records = vcf.gene_variants.get(gene, [])

        evidence = compute_evidence_score(
            drug=drug,
            gene=gene,
            phenotype=refined_phenotype,  # use refined phenotype
            rule_confidence=confidence,
            pathogenic_count=pathogenic_ct,  # reuse from STAGE 2a
            total_variant_count=len(gene_records),
            interactions=interactions,
            history_flags=history_flags,
            has_history=has_history,
        )

        # ── Build enriched DetectedVariant list ──────────────────────
        detected = [
            DetectedVariant(
                rsid=rec.rsid,
                gene=rec.gene,
                genotype=rec.gt,
                zygosity=Zygosity(rec.zygosity.value),
                star_allele=f"STAR={rec.star}" if rec.star else "",
            )
            for rec in gene_records
        ]

        # Build a diplotype-like summary string
        pathogenic_rsids = [r.rsid for r in gene_records if r.is_pathogenic]
        diplotype_summary = ", ".join(pathogenic_rsids) if pathogenic_rsids else "No pathogenic variants"

        # Clinical recommendation (now includes history warnings)
        clinical = build_clinical_recommendation(
            risk_label.value, drug, gene, interactions, history_flags,
        )

        # Build variant detail dicts for LLM prompt
        variant_details = [
            {
                "rsid": rec.rsid,
                "genotype": rec.gt,
                "zygosity": rec.zygosity.value if hasattr(rec.zygosity, "value") else str(rec.zygosity),
            }
            for rec in gene_records
        ]

        # ── STAGE 5: LLM explanation (with full context) ────────────
        history_block = _format_history_block(history)
        interactions_block = _format_interactions_block(interactions, history_flags)
        # NEW: clinical modifier logic — build modifiers context for LLM
        modifiers_block = _format_modifiers_block(clinical_mods)

        explanation = await generate_explanation(
            gene=gene,
            diplotype=diplotype_summary,
            phenotype=refined_phenotype,  # use refined phenotype
            drug=drug,
            risk_label=risk_label.value,
            severity=severity.value,
            variant_details=variant_details,
            patient_history_block=history_block,
            interactions_block=interactions_block,
            modifiers_block=modifiers_block,  # NEW
            evidence_level=evidence.evidence_level.value,
            guideline_pmid=evidence.guideline_pmid,
            evidence_score_str=f"{evidence.overall_score:.0%}",
        )

        results.append(
            PharmaGuardResult(
                patient_id=pid,
                drug=drug,
                timestamp=datetime.now(timezone.utc).isoformat(),
                risk_assessment=RiskAssessment(
                    risk_label=risk_label,
                    confidence_score=round(confidence, 2),
                    severity=severity,
                ),
                pharmacogenomic_profile=PharmacogenomicProfile(
                    primary_gene=gene,
                    diplotype=diplotype_summary,
                    phenotype=phenotype_enum,
                    detected_variants=detected,
                ),
                clinical_recommendation=clinical,
                llm_generated_explanation=LLMExplanation(**explanation),
                quality_metrics=QualityMetrics(
                    vcf_parsing_success=vcf.success,
                    history_provided=has_history,
                    interactions_checked=True,
                    evidence_scored=True,
                ),
                patient_history_flags=history_flags,
                drug_interactions=interactions,
                evidence_score=evidence,
                # NEW: clinical modifier logic
                clinical_modifiers=[ClinicalModifier(**m) for m in clinical_mods],
                base_risk_label=base_risk_label.value,
                base_severity=base_severity.value,
            )
        )

    return results


# ═══════════════════════════════════════════════════════════════════════════
# Internal helpers
# ═══════════════════════════════════════════════════════════════════════════

def _unknown_result(pid: str, drug: str, vcf_ok: bool, has_history: bool = False) -> PharmaGuardResult:
    """Construct a placeholder result for an unsupported drug."""
    return PharmaGuardResult(
        patient_id=pid,
        drug=drug,
        timestamp=datetime.now(timezone.utc).isoformat(),
        risk_assessment=RiskAssessment(
            risk_label=RiskLabel.UNKNOWN,
            confidence_score=0.0,
            severity=Severity.LOW,
        ),
        pharmacogenomic_profile=PharmacogenomicProfile(
            primary_gene="Unknown",
            diplotype="Unknown",
            phenotype=Phenotype.UNKNOWN,
            detected_variants=[],
        ),
        clinical_recommendation=ClinicalRecommendation(
            action="Drug not in supported pharmacogenomic panel.",
        ),
        quality_metrics=QualityMetrics(
            vcf_parsing_success=vcf_ok,
            history_provided=has_history,
        ),
    )
