# Backend Setup for PharmaGuard

## Quick Start

The frontend expects the backend API to be running on `http://localhost:8000`.

### 1. Start the Backend Server

From the project root directory:

```bash
# Activate virtual environment (if using one)
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Start the FastAPI server
uvicorn src.main:app --reload --port 8000
```

### 2. Start the Frontend Dev Server

In a separate terminal, from the `frontend` directory:

```bash
cd frontend
npm run dev
```

The frontend will run on `http://localhost:3000` and automatically proxy API requests to `http://localhost:8000`.

## API Endpoint

- **POST** `/api/analyze`
  - Accepts: `FormData` with `vcf_file` (File) and `drugs` (comma-separated string)
  - Returns: `List[PharmaGuardResult]`

## Troubleshooting

### "Analysis failed: Not Found" Error

This means the backend server is not running or not accessible. Check:

1. ✅ Backend server is running on port 8000
2. ✅ No firewall blocking port 8000
3. ✅ Vite proxy is configured correctly (already done in `vite.config.js`)

### Check Backend Health

Visit `http://localhost:8000/api/health` in your browser to verify the backend is running.

### CORS Issues

The backend should already have CORS configured. If you see CORS errors, check `src/main.py` CORS settings.
