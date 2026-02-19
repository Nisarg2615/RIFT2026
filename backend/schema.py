"""
PharmaGuard — backend compatibility layer (schema).

Re-exports all Pydantic models from the canonical ``src.models`` package
so that legacy ``backend.schema`` imports continue to work.
"""

from src.models import (               # noqa: F401
    ClinicalRecommendation,
    DetectedVariant,
    DrugRequest,
    LLMExplanation,
    PharmaGuardResult,
    PharmacogenomicProfile,
    Phenotype,
    QualityMetrics,
    RiskAssessment,
    RiskLabel,
    Severity,
    Zygosity,
)
