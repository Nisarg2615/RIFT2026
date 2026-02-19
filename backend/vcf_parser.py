"""
PharmaGuard — backend compatibility layer (VCF parser).

Re-exports all public symbols from the canonical ``src.services.vcf_parser``
module so that legacy ``backend.vcf_parser`` imports continue to work.
"""

from src.services.vcf_parser import (  # noqa: F401
    VCFParseResult,
    VariantRecord,
    derive_zygosity,
    parse_vcf,
)
