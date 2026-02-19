"""
Tests for VCF parser service.
"""

from pathlib import Path

from src.models.schemas import Zygosity
from src.services.vcf_parser import derive_zygosity, parse_vcf

SAMPLE_VCF = Path(__file__).resolve().parent.parent / "sample_data" / "sample_patient.vcf"


class TestParseVCF:
    def test_parses_sample_successfully(self):
        result = parse_vcf(SAMPLE_VCF.read_bytes())
        assert result.success is True
        assert result.error is None
        assert len(result.variants) > 0

    def test_captures_file_format(self):
        result = parse_vcf(SAMPLE_VCF.read_bytes())
        assert result.file_format == "VCFv4.2"

    def test_finds_all_six_genes(self):
        result = parse_vcf(SAMPLE_VCF.read_bytes())
        expected = {"CYP2D6", "CYP2C19", "CYP2C9", "SLCO1B1", "TPMT", "DPYD"}
        assert set(result.gene_variants.keys()) == expected

    def test_extracts_diplotypes(self):
        result = parse_vcf(SAMPLE_VCF.read_bytes())
        assert result.gene_diplotypes["CYP2D6"] == "*1/*4"
        assert result.gene_diplotypes["DPYD"] == "*1/*2A"

    def test_extracts_rsids(self):
        result = parse_vcf(SAMPLE_VCF.read_bytes())
        assert "rs3892097" in result.gene_rsids["CYP2D6"]
        assert "rs4149056" in result.gene_rsids["SLCO1B1"]

    def test_variants_have_zygosity(self):
        result = parse_vcf(SAMPLE_VCF.read_bytes())
        for v in result.variants:
            assert v.zygosity is not None
            assert isinstance(v.zygosity, Zygosity)

    def test_het_variant_detected(self):
        """Sample VCF has GT=0/1 for most variants → HET."""
        result = parse_vcf(SAMPLE_VCF.read_bytes())
        het_variants = [v for v in result.variants if v.zygosity == Zygosity.HET]
        assert len(het_variants) > 0

    def test_hom_ref_variant_detected(self):
        """Sample VCF has GT=0/0 for some variants → HOM_REF."""
        result = parse_vcf(SAMPLE_VCF.read_bytes())
        hom_ref = [v for v in result.variants if v.zygosity == Zygosity.HOM_REF]
        assert len(hom_ref) > 0

    def test_variants_carry_gene_and_star(self):
        result = parse_vcf(SAMPLE_VCF.read_bytes())
        cyp2d6 = result.gene_variants["CYP2D6"]
        assert all(v.gene == "CYP2D6" for v in cyp2d6)
        stars = [v for v in cyp2d6 if v.star]
        assert len(stars) >= 1

    def test_empty_file_returns_success_but_no_variants(self):
        result = parse_vcf(b"")
        assert result.success is True
        assert len(result.variants) == 0

    def test_oversized_file_returns_error(self):
        huge = b"x" * (6 * 1024 * 1024)  # 6 MB
        result = parse_vcf(huge)
        assert result.success is False
        assert "limit" in result.error.lower()

    def test_header_only_vcf(self):
        vcf = b"##fileformat=VCFv4.2\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
        result = parse_vcf(vcf)
        assert result.success is True
        assert len(result.variants) == 0

    def test_missing_info_fields_handled_gracefully(self):
        """A data line with INFO=. should not crash; gene is empty → skipped."""
        vcf = (
            b"##fileformat=VCFv4.2\n"
            b"#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
            b"1\t100\t.\tA\tG\t50\tPASS\t.\n"
        )
        result = parse_vcf(vcf)
        assert result.success is True
        assert len(result.variants) == 0   # no GENE → filtered out

    def test_missing_gt_gives_unknown_zygosity(self):
        """Variant with GENE but no FORMAT/GT → zygosity=UNKNOWN."""
        vcf = (
            b"##fileformat=VCFv4.2\n"
            b"#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
            b"22\t100\trs999\tC\tT\t50\tPASS\tGENE=CYP2D6;STAR=*1/*1\n"
        )
        result = parse_vcf(vcf)
        assert result.success is True
        assert len(result.variants) == 1
        assert result.variants[0].zygosity == Zygosity.UNKNOWN


class TestDeriveZygosity:
    def test_hom_ref(self):
        assert derive_zygosity("0/0") == Zygosity.HOM_REF

    def test_het_unphased(self):
        assert derive_zygosity("0/1") == Zygosity.HET

    def test_het_phased(self):
        assert derive_zygosity("0|1") == Zygosity.HET

    def test_hom_alt(self):
        assert derive_zygosity("1/1") == Zygosity.HOM_ALT

    def test_multiallelic_het(self):
        assert derive_zygosity("1/2") == Zygosity.HET

    def test_haploid(self):
        assert derive_zygosity("1") == Zygosity.HEMIZYGOUS

    def test_missing_dot(self):
        assert derive_zygosity(".") == Zygosity.UNKNOWN

    def test_empty_string(self):
        assert derive_zygosity("") == Zygosity.UNKNOWN

    def test_partial_missing(self):
        assert derive_zygosity("./1") == Zygosity.HEMIZYGOUS
