# 🧬 PharmaGuard — Pharmacogenomic Risk Prediction System

**PharmaGuard** predicts drug–gene interaction risks using VCF variant data, a CPIC-aligned rule engine, and Google Gemini for clinical explanations.

---

## Quick Start

### 1. Install dependencies

```bash
cd h
pip install -r requirements.txt
```

### 2. Configure Gemini API (optional)

```bash
cp .env.example .env
# Edit .env and paste your key:
# GEMINI_API_KEY=AIza...
```

> Without a key the system uses deterministic fallback explanations — fully functional for demos.

### 3. Run the server

```bash
uvicorn backend.main:app --reload --port 8000
```

### 4. Open the UI

Navigate to **http://localhost:8000** in your browser.

1. Upload the sample VCF from `sample_data/sample_patient.vcf`
2. Click drug chips or type drug names
3. Click **Analyze** → results appear instantly

---

## Project Structure

```
h/
├── backend/
│   ├── __init__.py
│   ├── main.py          # FastAPI app — routes & orchestration
│   ├── vcf_parser.py    # VCF v4.2 parser (INFO: GENE, STAR, RS, GT)
│   ├── rules.py         # CPIC-style diplotype → phenotype → risk tables
│   ├── llm.py           # Google Gemini API client + fallback
│   └── schema.py        # Pydantic models — strict JSON output contract
├── frontend/
│   └── index.html       # Single-page upload UI (vanilla HTML/JS/CSS)
├── sample_data/
│   └── sample_patient.vcf  # Demo VCF with 6-gene panel variants
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## API

### `POST /api/analyze`

| Field        | Type   | Description                          |
|-------------|--------|--------------------------------------|
| `vcf_file`  | File   | VCF v4.2 file (≤ 5 MB)              |
| `drugs`     | string | Comma-separated drug names           |
| `patient_id`| string | Optional patient identifier          |

**Response:** `PharmaGuardResult[]` — one entry per drug. See `backend/schema.py` for the exact schema.

### `GET /api/health`

Returns server status and supported drug list.

---

## Supported Panel

| Drug          | Primary Gene | Risk Range                  |
|---------------|-------------|-----------------------------|
| Codeine       | CYP2D6      | Safe → Toxic (URM)          |
| Clopidogrel   | CYP2C19     | Safe → Ineffective (PM)     |
| Warfarin      | CYP2C9      | Safe → Toxic (PM)           |
| Simvastatin   | SLCO1B1     | Safe → Toxic (PM)           |
| Azathioprine  | TPMT        | Safe → Toxic (PM)           |
| Fluorouracil  | DPYD        | Safe → Toxic (PM)           |

---

## Gemini Integration

Set `GEMINI_API_KEY` in `.env`. The system calls **Gemini 2.0 Flash** to generate:

- **Summary** — 2-3 sentence overview
- **Mechanism** — how the variant affects metabolism
- **Justification** — why the risk label was assigned
- **Recommendation** — actionable clinical advice

If the key is missing or the call fails, deterministic stub explanations are used instead.

---

## License

MIT — Hackathon project, **not for clinical use**.
