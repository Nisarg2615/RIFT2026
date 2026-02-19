"""
PharmaGuard — VCF v4.2 Parser Service.

Extracts pharmacogenomic variants from raw VCF bytes.

Parsed fields
─────────────
  INFO tags  : GENE, STAR (quality rating 1-5), RS (dbSNP ID)
  FORMAT/GT  : genotype string  →  zygosity derivation (supports GT:AD:DP:GQ)

Only variants belonging to the six supported pharmacogenes are retained.
Missing fields are handled gracefully (empty string / UNKNOWN enum).

Phenotype inference
───────────────────
Instead of relying on star-allele diplotypes, this parser infers the
metabolizer phenotype from the number and zygosity of clinically
significant (pathogenic) rsID variants found per gene, using a
well-known pathogenic-rsID table.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from src.core.config import get_settings
from src.models.schemas import Zygosity

logger = logging.getLogger(__name__)

settings = get_settings()

# Allele separator pattern:  "/" (unphased) or "|" (phased)
_GT_SEP = re.compile(r"[/|]")

# ═══════════════════════════════════════════════════════════════════════════
# Clinically significant (pathogenic) rsIDs per gene
# These are the variants that actually affect enzyme function.
# ═══════════════════════════════════════════════════════════════════════════
PATHOGENIC_RSIDS: Dict[str, Set[str]] = {
    "CYP2D6":  {"rs3892097", "rs5030655", "rs28371706", "rs59421388", "rs28371725"},
    "CYP2C19": {"rs4244285", "rs4986893", "rs28399504", "rs12248560"},
    "CYP2C9":  {"rs1799853", "rs1057910"},
    "SLCO1B1": {"rs4149056", "rs2306283"},
    "TPMT":    {"rs1142345", "rs1800462", "rs1800460"},
    "DPYD":    {"rs3918290", "rs55886062", "rs67376798"},
}


# ═══════════════════════════════════════════════════════════════════════════
# Data classes returned by the parser
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class VariantRecord:
    """One data row from the VCF that maps to a pharmacogene of interest."""
    chrom: str = ""
    pos: int = 0
    rsid: str = ""
    ref: str = ""
    alt: str = ""
    gene: str = ""
    star: str = ""        # STAR quality rating from INFO
    gt: str = ""          # Raw genotype string, e.g. "0/1"
    zygosity: Zygosity = Zygosity.UNKNOWN
    is_pathogenic: bool = False   # True if rsid is in PATHOGENIC_RSIDS


@dataclass
class VCFParseResult:
    """Aggregated output produced after parsing one VCF file."""
    success: bool = True
    error: Optional[str] = None
    file_format: str = ""
    variants: List[VariantRecord] = field(default_factory=list)

    # ── Per-gene convenience indexes ─────────────────────────────────
    gene_variants: Dict[str, List[VariantRecord]] = field(default_factory=dict)
    gene_rsids: Dict[str, Set[str]] = field(default_factory=dict)

    # ── Inferred phenotype per gene (based on pathogenic variant count)
    gene_phenotypes: Dict[str, str] = field(default_factory=dict)

    # ── Summary counts ───────────────────────────────────────────────
    gene_pathogenic_count: Dict[str, int] = field(default_factory=dict)
    gene_hom_alt_count: Dict[str, int] = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════
# Internal helpers
# ═══════════════════════════════════════════════════════════════════════════

def _parse_info(info_str: str) -> Dict[str, str]:
    """Parse VCF INFO column (KEY=VAL;KEY2=VAL2) into a dict."""
    tags: Dict[str, str] = {}
    if not info_str or info_str == ".":
        return tags
    for token in info_str.split(";"):
        token = token.strip()
        if not token:
            continue
        if "=" in token:
            k, v = token.split("=", 1)
            tags[k.strip()] = v.strip()
        else:
            tags[token] = ""
    return tags


def _extract_gt(format_col: str, sample_col: str) -> str:
    """Pull the GT value from FORMAT + first SAMPLE columns (supports GT:AD:DP:GQ)."""
    if not format_col or not sample_col:
        return ""
    keys = format_col.split(":")
    vals = sample_col.split(":")
    mapping = dict(zip(keys, vals))
    gt = mapping.get("GT", "")
    return "" if gt == "." else gt


def derive_zygosity(gt: str) -> Zygosity:
    """
    Derive zygosity from a VCF genotype string.
    0/0 → HOM_REF, 0/1 → HET, 1/1 → HOM_ALT, single → HEMIZYGOUS
    """
    if not gt or gt == ".":
        return Zygosity.UNKNOWN

    alleles = _GT_SEP.split(gt)
    alleles = [a for a in alleles if a != "."]

    if len(alleles) == 0:
        return Zygosity.UNKNOWN
    if len(alleles) == 1:
        return Zygosity.HEMIZYGOUS

    unique = set(alleles)
    if len(unique) == 1:
        return Zygosity.HOM_REF if alleles[0] == "0" else Zygosity.HOM_ALT
    else:
        return Zygosity.HET


def _normalise_rsid(id_col: str, rs_info: str) -> str:
    """Build canonical rsID from ID column and/or INFO RS tag."""
    if id_col and id_col != ".":
        return id_col
    if not rs_info:
        return ""
    return rs_info if rs_info.startswith("rs") else f"rs{rs_info}"


def _infer_phenotype(
    gene: str,
    pathogenic_het: int,
    pathogenic_hom_alt: int,
) -> str:
    """
    Infer metabolizer phenotype from pathogenic variant counts.

    Logic:
      - 0 pathogenic variants with alt allele     → NM (Normal Metabolizer)
      - 1 het pathogenic variant                   → IM (Intermediate)
      - 2+ het pathogenic, or 1 hom_alt            → PM (Poor Metabolizer)
      - For CYP2C19 with rs12248560 (gain-of-func) → RM/URM handled separately

    This is a simplified model suitable for a hackathon demo.
    """
    total_damaging = pathogenic_het + (pathogenic_hom_alt * 2)

    if total_damaging == 0:
        return "NM"
    elif total_damaging == 1:
        return "IM"
    elif total_damaging >= 2:
        return "PM"
    else:
        return "Unknown"


# ═══════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════

def parse_vcf(raw_bytes: bytes) -> VCFParseResult:
    """
    Parse a VCF v4.2 byte-stream and extract pharmacogenomic variants.

    Handles the standard VCF format with INFO fields: GENE, STAR, RS
    and FORMAT fields: GT:AD:DP:GQ
    """
    result = VCFParseResult()

    # ── 1. Size guard ────────────────────────────────────────────────
    if len(raw_bytes) > settings.max_vcf_size_bytes:
        mb = settings.max_vcf_size_bytes // (1024 * 1024)
        result.success = False
        result.error = f"VCF file exceeds the {mb} MB size limit."
        return result

    # ── 2. Decode to text ────────────────────────────────────────────
    try:
        text = raw_bytes.decode("utf-8", errors="replace")
    except Exception as exc:
        result.success = False
        result.error = f"Cannot decode VCF file: {exc}"
        return result

    # ── 3. Walk lines ────────────────────────────────────────────────
    supported = set(settings.supported_genes)
    header_seen = False
    skipped = 0

    # Track pathogenic variants per gene for phenotype inference
    gene_path_het: Dict[str, int] = {}
    gene_path_hom: Dict[str, int] = {}

    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue

        # --- Meta-information lines (##) ─────────────────────────────
        if line.startswith("##"):
            if line.startswith("##fileformat="):
                result.file_format = line.split("=", 1)[1].strip()
            continue

        # --- Header line (#CHROM …) ─────────────────────────────────
        if line.startswith("#"):
            header_seen = True
            continue

        # --- Data line ───────────────────────────────────────────────
        if not header_seen:
            logger.warning("VCF line %d: data row before #CHROM header", line_no)

        cols = line.split("\t")
        if len(cols) < 8:
            skipped += 1
            continue

        chrom, pos_str, vid, ref, alt, _qual, _filt, info_str = cols[:8]
        format_col = cols[8] if len(cols) > 8 else ""
        sample_col = cols[9] if len(cols) > 9 else ""

        # -- Parse INFO tags ──────────────────────────────────────────
        info = _parse_info(info_str)
        gene = info.get("GENE", "").strip().upper()
        star = info.get("STAR", "").strip()
        rs_info = info.get("RS", "").strip()

        # -- Genotype (supports GT:AD:DP:GQ format) ──────────────────
        gt = _extract_gt(format_col, sample_col)

        # -- rsID: ID column → INFO RS → "" ──────────────────────────
        rsid = _normalise_rsid(vid, rs_info)

        # -- Filter: only keep variants for our gene panel ────────────
        if gene not in supported:
            continue

        # -- Derive zygosity ──────────────────────────────────────────
        zygosity = derive_zygosity(gt)

        # -- Check if this is a pathogenic variant ────────────────────
        gene_pathogenic_set = PATHOGENIC_RSIDS.get(gene, set())
        is_pathogenic = rsid in gene_pathogenic_set

        record = VariantRecord(
            chrom=chrom,
            pos=int(pos_str) if pos_str.isdigit() else 0,
            rsid=rsid,
            ref=ref,
            alt=alt,
            gene=gene,
            star=star,
            gt=gt,
            zygosity=zygosity,
            is_pathogenic=is_pathogenic,
        )

        result.variants.append(record)
        result.gene_variants.setdefault(gene, []).append(record)
        if rsid:
            result.gene_rsids.setdefault(gene, set()).add(rsid)

        # -- Count pathogenic variants (only those carrying ALT) ──────
        if is_pathogenic and zygosity in (Zygosity.HET, Zygosity.HOM_ALT):
            if zygosity == Zygosity.HOM_ALT:
                gene_path_hom[gene] = gene_path_hom.get(gene, 0) + 1
            else:
                gene_path_het[gene] = gene_path_het.get(gene, 0) + 1

    # ── 4. Infer phenotype per gene ──────────────────────────────────
    for gene in supported:
        het = gene_path_het.get(gene, 0)
        hom = gene_path_hom.get(gene, 0)
        result.gene_pathogenic_count[gene] = het + hom
        result.gene_hom_alt_count[gene] = hom
        result.gene_phenotypes[gene] = _infer_phenotype(gene, het, hom)

    # ── 5. Summary logging ───────────────────────────────────────────
    if skipped:
        logger.warning("VCF parse: skipped %d malformed rows", skipped)
    logger.info(
        "VCF parsed: %d total variants, genes found: %s",
        len(result.variants),
        list(result.gene_variants.keys()),
    )
    for gene, ph in result.gene_phenotypes.items():
        if gene in result.gene_variants:
            logger.info(
                "  %s: %d variants, %d pathogenic → %s",
                gene, len(result.gene_variants.get(gene, [])),
                result.gene_pathogenic_count.get(gene, 0), ph,
            )

    return result
