# PharmaGuard React Frontend

A modern React-based clinical decision support system for pharmacogenomic analysis.

## Setup Instructions

### 1. Install Dependencies

Navigate to the frontend directory and install React dependencies:

```bash
cd frontend
npm install
```

### 2. Build for Production

```bash
npm run build
```

This creates an optimized production build in the `frontend/build/` folder that the FastAPI backend will serve.

### 3. Start Backend

The FastAPI backend will automatically serve the React app:

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

Then open your browser to `http://localhost:8000`

## Features

✅ **Drug Selection** - Select from 6 available medications (Codeine, Clopidogrel, Warfarin, Simvastatin, Azathioprine, Fluorouracil)
✅ **VCF Upload** - Drag-and-drop VCF file upload with sample data support
✅ **Summary Dashboard** - Real-time risk assessment with gene count and drug analysis metrics
✅ **Gene Panel** - Visual representation of analyzed genes with phenotype data
✅ **Drug Risk Table** - Comprehensive drug risk assessment table with CPIC levels
✅ **Detailed Reports** - In-depth analysis including:
  - Clinical Risk Modifiers
  - Detected Variants (RSID, Genotype, Zygosity, Star Alleles)
  - Drug-Drug Interactions
  - Evidence-Based Accuracy Scores
  - Clinical Recommendations
  - AI-Generated Explanations
✅ **History Management** - Save and retrieve past analyses
✅ **JSON Export** - Download or copy analysis results as JSON

## Project Structure

```
frontend/
├── public/
│   └── index.html          # React entry point
├── src/
│   ├── index.js            # React app entry
│   ├── index.css           # Global styles
│   ├── App.js              # Main app component
│   ├── components/
│   │   ├── Header.js       # Navigation header
│   │   ├── UploadSection.js     # File upload & drug selection
│   │   ├── LoadingState.js      # Loading spinner
│   │   ├── ErrorMessage.js      # Error notifications
│   │   ├── SummaryDashboard.js  # Dashboard widgets
│   │   ├── GenePanel.js         # Gene analysis cards
│   │   ├── DrugTable.js         # Risk assessment table
│   │   ├── DetailedReports.js   # Comprehensive reports
│   │   └── DownloadSection.js   # JSON export buttons
│   └── utils/
│       └── historyManager.js    # History state management
├── package.json
└── build/                  # Generated production build
```

## Development

For development with hot reload:

```bash
cd frontend
npm start
```

This starts the React development server on port 3000.

## API Integration

The React frontend communicates with the FastAPI backend:

- **POST /api/analyze** - Submit VCF file and drugs for analysis
- **GET /api/health** - Health check

The backend returns detailed analysis results including:
- Risk assessment with confidence scores
- Pharmacogenomic profiles (gene, diplotype, phenotype)
- Clinical modifications and drug interactions
- Evidence-based recommendations
- AI-generated clinical explanations

## Notes

- Browser storage is used for history (localStorage)
- Results display in real-time after backend processing
- All styling is responsive and mobile-friendly
- No external UI libraries (pure React + CSS)
