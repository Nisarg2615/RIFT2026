"""
PharmaGuard — backend compatibility layer (rules engine).

Re-exports all public symbols from the canonical ``src.services.rules_engine``
module so that legacy ``backend.rules`` imports continue to work.
"""

from src.services.rules_engine import (  # noqa: F401
    DIPLOTYPE_PHENOTYPE,
    DRUG_GENE_MAP,
    RISK_TABLE,
    SUPPORTED_DRUGS,
    SUPPORTED_GENES,
    assess_risk,
    get_primary_gene,
    resolve_phenotype,
    validate_drug,
)
