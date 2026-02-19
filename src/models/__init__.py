"""
PharmaGuard — Pydantic v2 models defining the **strict** JSON output contract.

Every API response conforms exactly to these models.  Field names, types,
and nesting must not deviate from the specification.

Pipeline: VCF + Patient History → Parse → Risk + Interactions → Evidence Score → LLM → JSON
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════════════

class RiskLabel(str, Enum):
    """Possible risk outcomes from the CPIC rule engine."""
    SAFE = "Safe"
    ADJUST_DOSAGE = "Adjust Dosage"
    TOXIC = "Toxic"
    INEFFECTIVE = "Ineffective"
    CONTRAINDICATED = "Contraindicated"
    UNKNOWN = "Unknown"


class Severity(str, Enum):
    """Clinical severity tier."""
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class Phenotype(str, Enum):
    """Metabolizer phenotype classification."""
    PM = "PM"       # Poor Metabolizer
    IM = "IM"       # Intermediate Metabolizer
    NM = "NM"       # Normal Metabolizer
    RM = "RM"       # Rapid Metabolizer
    URM = "URM"     # Ultra-Rapid Metabolizer
    UNKNOWN = "Unknown"


class Zygosity(str, Enum):
    """Zygosity derived from the VCF GT field."""
    HOM_REF = "HOM_REF"     # e.g. 0/0  — homozygous reference
    HET = "HET"             # e.g. 0/1  — heterozygous
    HOM_ALT = "HOM_ALT"     # e.g. 1/1  — homozygous alternate
    HEMIZYGOUS = "HEMIZYGOUS"  # e.g. 1   — haploid / X-linked
    UNKNOWN = "Unknown"     # GT missing or unparseable


class InteractionSeverity(str, Enum):
    """Drug-drug interaction severity classification."""
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CONTRAINDICATED = "contraindicated"


class EvidenceLevel(str, Enum):
    """CPIC clinical evidence level classification."""
    LEVEL_A = "A"    # Strong: preponderance of evidence is high quality
    LEVEL_B = "B"    # Moderate: evidence is moderate quality
    LEVEL_C = "C"    # Optional: evidence is weak
    LEVEL_D = "D"    # Informational: limited evidence
    NA = "N/A"


# ═══════════════════════════════════════════════════════════════════════════
# Patient History models  (NEW — mentor feedback)
# ═══════════════════════════════════════════════════════════════════════════

class PatientHistory(BaseModel):
    """Patient medical history input for personalised risk assessment."""

    # ── Demographics ─────────────────────────────────────────────────
    age: Optional[int] = Field(
        default=None, ge=0, le=150, description="Patient age in years",
    )
    gender: Optional[str] = Field(
        default=None,
        description="Patient gender: male, female, or other",
    )
    weight_kg: Optional[float] = Field(
        default=None, ge=0, description="Patient weight in kilograms",
    )
    ethnicity: Optional[str] = Field(
        default=None,
        description="Self-reported ethnicity (affects allele frequency priors)",
    )
    blood_group: Optional[str] = Field(
        default=None,
        description="Blood group, e.g. A+, B-, O+, AB+",
    )

    # ── Medical history ──────────────────────────────────────────────
    conditions: List[str] = Field(
        default_factory=list,
        description="Active medical conditions, e.g. ['diabetes', 'hypertension']",
    )
    current_medications: List[str] = Field(
        default_factory=list,
        description="Medications patient is currently taking",
    )
    allergies: List[str] = Field(
        default_factory=list,
        description="Known drug allergies",
    )
    prior_adverse_reactions: List[str] = Field(
        default_factory=list,
        description="Prior adverse drug reactions, e.g. 'Codeine → nausea'",
    )

    # ── Organ function ───────────────────────────────────────────────
    kidney_function: Optional[str] = Field(
        default=None,
        description="Renal status: normal, mild impairment, moderate impairment, severe impairment, dialysis",
    )
    liver_function: Optional[str] = Field(
        default=None,
        description="Hepatic status: normal, mild impairment (Child-Pugh A), moderate impairment (Child-Pugh B), severe impairment (Child-Pugh C)",
    )

    # ── Lifestyle factors ────────────────────────────────────────────
    smoking_status: Optional[str] = Field(
        default=None,
        description="Smoking status: never, former, current",
    )
    alcohol_use: Optional[str] = Field(
        default=None,
        description="Alcohol use: none, occasional, moderate, heavy",
    )


class HistoryFlag(BaseModel):
    """One flag raised from patient history analysis."""
    flag_type: str = Field(
        ..., description="allergy | condition_risk | prior_reaction | age_risk",
    )
    severity: Severity
    message: str = Field(..., description="Human-readable warning message")


# ═══════════════════════════════════════════════════════════════════════════
# Drug Interaction models  (NEW — interactions layer)
# ═══════════════════════════════════════════════════════════════════════════

class DrugInteraction(BaseModel):
    """One drug-drug interaction between the assessed drug and a current medication."""
    current_medication: str = Field(..., description="The medication the patient is already taking")
    assessed_drug: str = Field(..., description="The drug being evaluated by PharmaGuard")
    interaction_severity: InteractionSeverity
    interaction_type: str = Field("", description="e.g. pharmacokinetic, pharmacodynamic")
    description: str = Field("", description="Clinical description of the interaction")
    recommendation: str = Field("", description="What to do about the interaction")


# ═══════════════════════════════════════════════════════════════════════════
# Evidence Score models  (NEW — accuracy justification)
# ═══════════════════════════════════════════════════════════════════════════

class EvidenceComponent(BaseModel):
    """One component contributing to the overall evidence score."""
    name: str = Field(..., description="e.g. cpic_guideline, variant_confidence")
    score: float = Field(..., ge=0.0, le=1.0, description="Component score 0–1")
    detail: str = Field("", description="Human-readable explanation")


class EvidenceScore(BaseModel):
    """Aggregated evidence-based accuracy justification for the recommendation."""
    overall_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Weighted composite accuracy score (0–1)",
    )
    evidence_level: EvidenceLevel = Field(
        ..., description="CPIC evidence level A/B/C/D",
    )
    guideline_source: str = Field(
        "", description="e.g. CPIC, DPWG, FDA label",
    )
    guideline_pmid: str = Field(
        "", description="PubMed ID for the primary guideline reference",
    )
    components: List[EvidenceComponent] = Field(
        default_factory=list,
        description="Breakdown of how the score was derived",
    )
    accuracy_justification: str = Field(
        "", description="Narrative explaining why this recommendation is accurate",
    )


# ═══════════════════════════════════════════════════════════════════════════
# Clinical Modifier model  (NEW — clinical modifier logic)
# ═══════════════════════════════════════════════════════════════════════════

class ClinicalModifier(BaseModel):
    """One clinical modifier that adjusted the base genomic risk."""
    modifier_type: str = Field(
        ..., description="e.g. liver_impairment, cyp_inhibitor, renal_impairment, advanced_age",
    )
    description: str = Field(
        ..., description="Human-readable explanation of the modifier",
    )
    impact: str = Field(
        ..., description="e.g. severity_escalated, risk_upgraded, dose_flag, monitoring_recommended",
    )
    original_value: str = Field(
        "", description="Value before this modifier was applied",
    )
    adjusted_value: str = Field(
        "", description="Value after this modifier was applied",
    )


# ═══════════════════════════════════════════════════════════════════════════
# Sub-models  (nested objects inside the top-level result)
# ═══════════════════════════════════════════════════════════════════════════

class DetectedVariant(BaseModel):
    """One variant detected in the VCF for a pharmacogene."""
    rsid: str = Field("", examples=["rs3892097"], description="dbSNP rsID (empty if absent)")
    gene: str = Field("", description="Gene symbol this variant belongs to")
    genotype: str = Field("", examples=["0/1"], description="Raw GT string from the VCF")
    zygosity: Zygosity = Field(Zygosity.UNKNOWN, description="Zygosity inferred from GT")
    star_allele: str = Field("", examples=["*1/*4"], description="Star-allele diplotype from INFO STAR")


class RiskAssessment(BaseModel):
    """Rule-engine output: risk label + confidence + severity."""
    risk_label: RiskLabel
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Rule-engine confidence (0–1)",
    )
    severity: Severity


class PharmacogenomicProfile(BaseModel):
    """Genomic context extracted from the VCF for one gene–drug pair."""
    primary_gene: str = Field(..., examples=["CYP2D6"], description="HGNC gene symbol")
    diplotype: str = Field(..., examples=["*1/*4"], description="Star-allele diplotype")
    phenotype: Phenotype
    detected_variants: List[DetectedVariant] = []


class ClinicalRecommendation(BaseModel):
    """Structured clinical guidance (extensible)."""
    action: Optional[str] = None
    alternative_drugs: Optional[List[str]] = None
    monitoring: Optional[str] = None
    history_based_warnings: Optional[str] = None


class LLMExplanation(BaseModel):
    """Fields populated by the Gemini LLM call."""
    summary: str = ""
    mechanism: str = ""
    justification: str = ""
    recommendation: str = ""


class QualityMetrics(BaseModel):
    """Pipeline quality flags."""
    vcf_parsing_success: bool = True
    history_provided: bool = False
    interactions_checked: bool = False
    evidence_scored: bool = False


# ═══════════════════════════════════════════════════════════════════════════
# Top-level response model  (the canonical PharmaGuard output)
# ═══════════════════════════════════════════════════════════════════════════

class PharmaGuardResult(BaseModel):
    """
    One result object per (patient, drug) pair.
    The /analyze endpoint returns ``List[PharmaGuardResult]``.

    Pipeline: VCF + Patient History → Parse → Risk + Interactions
              → Evidence Score → LLM → JSON
    """
    patient_id: str = Field(..., examples=["PATIENT_A1B2C3"], description="Patient identifier")
    drug: str = Field(..., examples=["CODEINE"], description="Upper-case drug name")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO-8601 UTC timestamp",
    )
    risk_assessment: RiskAssessment
    pharmacogenomic_profile: PharmacogenomicProfile
    clinical_recommendation: ClinicalRecommendation = ClinicalRecommendation()
    llm_generated_explanation: LLMExplanation = LLMExplanation()
    quality_metrics: QualityMetrics = QualityMetrics()

    # ── NEW: Patient-history-aware fields ────────────────────────────
    patient_history_flags: List[HistoryFlag] = Field(
        default_factory=list,
        description="Warnings raised from patient history (allergies, conditions, etc.)",
    )
    drug_interactions: List[DrugInteraction] = Field(
        default_factory=list,
        description="Drug-drug interactions with the patient's current medications",
    )
    evidence_score: Optional[EvidenceScore] = Field(
        default=None,
        description="Evidence-based accuracy justification for this recommendation",
    )

    # NEW: clinical modifier logic — base vs adjusted risk
    clinical_modifiers: List[ClinicalModifier] = Field(
        default_factory=list,
        description="Clinical modifiers applied on top of base genomic risk",
    )
    base_risk_label: Optional[str] = Field(
        default=None,
        description="Original risk label before clinical modifiers",
    )
    base_severity: Optional[str] = Field(
        default=None,
        description="Original severity before clinical modifiers",
    )


# ═══════════════════════════════════════════════════════════════════════════
# Request helper
# ═══════════════════════════════════════════════════════════════════════════

class DrugRequest(BaseModel):
    """Parsed drug input from the form."""
    drugs: str = Field(
        ..., description="Comma-separated drug names, e.g. CODEINE,WARFARIN",
    )
    patient_id: Optional[str] = Field(
        default=None, description="Optional patient identifier; auto-generated if omitted",
    )
