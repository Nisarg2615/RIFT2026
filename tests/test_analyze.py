"""
Tests for POST /api/analyze endpoint.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)

SAMPLE_VCF = Path(__file__).resolve().parent.parent / "sample_data" / "sample_patient.vcf"


class TestHealthEndpoint:
    def test_health_returns_ok(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert isinstance(body["supported_drugs"], list)

    def test_health_lists_all_drugs(self):
        resp = client.get("/api/health")
        drugs = resp.json()["supported_drugs"]
        assert "CODEINE" in drugs
        assert "WARFARIN" in drugs


class TestAnalyzeEndpoint:
    def test_missing_file_returns_422(self):
        resp = client.post("/api/analyze", data={"drugs": "CODEINE"})
        assert resp.status_code == 422  # FastAPI validation

    def test_missing_drugs_returns_422(self):
        vcf = SAMPLE_VCF.read_bytes()
        resp = client.post(
            "/api/analyze",
            files={"vcf_file": ("test.vcf", vcf, "text/plain")},
        )
        assert resp.status_code == 422

    def test_single_drug_returns_one_result(self):
        vcf = SAMPLE_VCF.read_bytes()
        resp = client.post(
            "/api/analyze",
            files={"vcf_file": ("test.vcf", vcf, "text/plain")},
            data={"drugs": "CODEINE"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["drug"] == "CODEINE"

    def test_multiple_drugs_returns_multiple_results(self):
        vcf = SAMPLE_VCF.read_bytes()
        resp = client.post(
            "/api/analyze",
            files={"vcf_file": ("test.vcf", vcf, "text/plain")},
            data={"drugs": "CODEINE,WARFARIN,FLUOROURACIL"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        drugs_returned = [r["drug"] for r in data]
        assert "CODEINE" in drugs_returned
        assert "WARFARIN" in drugs_returned
        assert "FLUOROURACIL" in drugs_returned

    def test_result_schema_matches(self):
        """Verify every required top-level key is present."""
        vcf = SAMPLE_VCF.read_bytes()
        resp = client.post(
            "/api/analyze",
            files={"vcf_file": ("test.vcf", vcf, "text/plain")},
            data={"drugs": "CODEINE"},
        )
        result = resp.json()[0]
        required_keys = {
            "patient_id", "drug", "timestamp",
            "risk_assessment", "pharmacogenomic_profile",
            "clinical_recommendation", "llm_generated_explanation",
            "quality_metrics",
        }
        assert required_keys.issubset(result.keys())

    def test_unsupported_drug_returns_unknown(self):
        vcf = SAMPLE_VCF.read_bytes()
        resp = client.post(
            "/api/analyze",
            files={"vcf_file": ("test.vcf", vcf, "text/plain")},
            data={"drugs": "ASPIRIN"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data[0]["risk_assessment"]["risk_label"] == "Unknown"
