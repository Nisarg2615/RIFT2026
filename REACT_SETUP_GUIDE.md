# PharmaGuard React Conversion - Setup Guide

## Overview
The frontend has been converted from vanilla HTML/CSS/JavaScript to a modern React application with all the same functionality and styling preserved.

## Files Structure

### React Components Created:
- `frontend/src/App.js` - Main application component
- `frontend/src/index.js` - React entry point
- `frontend/src/index.css` - Global styles (same as original)
- `frontend/public/index.html` - HTML entry point
- `frontend/src/utils/historyManager.js` - History management utilities

### React Components (in `frontend/src/components/`):
1. **Header.js** - Navigation bar with history button
2. **UploadSection.js** - VCF upload, drug selection, and submit controls
3. **LoadingState.js** - Loading spinner animation
4. **ErrorMessage.js** - Error notification display
5. **SummaryDashboard.js** - Overview widgets (risk level, genes, drugs, alerts)
6. **GenePanel.js** - Gene analysis cards with phenotype data
7. **DrugTable.js** - Drug risk assessment table
8. **DetailedReports.js** - Comprehensive drug-by-drug reports including:
   - Clinical Risk Modifiers visualization
   - Detected Variants table (RSID, Genotype, Zygosity, Star Alleles)
   - Drug-Drug Interactions
   - Evidence-Based Accuracy Scores with progress bars
   - Clinical Recommendations
   - AI-Generated Explanations
9. **DownloadSection.js** - JSON download and copy functionality

## Backend Updates

Updated `src/main.py` to serve React build:
- Serves from `frontend/build/` after production build
- SPA fallback routing (all unmatched routes serve index.html)
- API routes (/api/*) work as before
- Maintains CORS and all middleware

## Step-by-Step Setup

### 1. Install Node.js
If not already installed, download from https://nodejs.org/

### 2. Install Frontend Dependencies
```bash
cd c:\Users\Hp\Downloads\pharm\h\frontend
npm install
```
This installs React and all required dependencies based on package.json

### 3. Build Production Version
```bash
npm run build
```
Creates optimized build in `frontend/build/` folder (~5 min)

### 4. Start Backend (if not running)
```bash
cd c:\Users\Hp\Downloads\pharm\h
python -m uvicorn backend.main:app --reload --port 8000
```

### 5. Access Application
Open browser to: http://localhost:8000

## Features Preserved/Enhanced

✅ Modern React architecture with component reusability
✅ Same visual design and styling (100% CSS compatible)
✅ All original functionality:
  - VCF file upload with validation
  - Drug selection (6 medications)
  - Sample data with one click
  - Real-time analysis submission
  - Complete detailed reports
  
✅ Added features:
  - Component-based code (easier to maintain)
  - Better state management
  - Reusable components
  - Cleaner separation of concerns
  - Mobile-responsive design

✅ All detailed output preserved:
  - Summary Dashboard with metrics
  - Gene analysis panel
  - Drug risk table
  - Detailed drug-by-drug reports including:
    - Patient info grid
    - Clinical Risk Modifiers
    - Drug-Drug Interactions
    - Evidence-Based Accuracy Scores
    - Detected Variants table
    - Clinical Recommendations
    - AI-Generated Explanations
  - History management (localStorage)
  - JSON download and copy

## Troubleshooting

### Issue: "npm: command not found"
**Solution:** Node.js not installed. Download from https://nodejs.org/

### Issue: "Module not found" errors
**Solution:** Run `npm install` in frontend directory

### Issue: Build fails
**Solution:** 
- Clear npm cache: `npm cache clean --force`
- Delete node_modules: `rm -r node_modules`
- Reinstall: `npm install`

### Issue: Shows blank page
**Solution:** 
- Check browser console for errors (F12)
- Ensure backend is running on port 8000
- Try hard refresh (Ctrl+Shift+R)

## Development Mode

For local development with hot reload:
```bash
cd frontend
npm start
```
This starts dev server on http://localhost:3000 (auto-reloads on file changes)

## Production Build

The `npm run build` command creates optimized, minified files in `frontend/build/` folder. The backend automatically serves these files.

## Dependencies

From `frontend/package.json`:
- react@^18.2.0 - Core React library
- react-dom@^18.2.0 - React DOM renderer
- react-scripts@5.0.1 - Build scripts and configuration

All components use only React and vanilla JavaScript (no additional UI libraries).

---

The React conversion maintains 100% feature parity with the original while providing a modern, maintainable codebase for future enhancements!
