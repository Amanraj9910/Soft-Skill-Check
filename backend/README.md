# 🚀 Backend Setup & Development Guide

FastAPI backend for AI English Speaking Assessment Platform.

---

## 🏗️ Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Configuration management
│   ├── dependencies.py         # FastAPI dependencies
│   ├── models/                 # Pydantic models
│   ├── routers/                # API route handlers
│   ├── services/               # Business logic services
│   │   ├── supabase_client.py  # Database operations
│   │   ├── azure_speech.py     # Speech services
│   │   ├── azure_openai.py     # AI scoring
│   │   ├── blob_storage.py     # File storage
│   │   └── audio_analysis.py   # Audio feature extraction
│   └── utils/                  # Helper functions
├── tests/                      # Test files
├── requirements.txt            # Python dependencies
├── .env.backend               # Environment variables (DO NOT COMMIT)
└── README.md                  # This file
```

---

## 🛠️ Setup Instructions

### Step 1: Create Virtual Environment

```powershell
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1

# If you get execution policy error:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Step 2: Install Dependencies

```powershell
# Install all requirements
pip install -r requirements.txt

# Verify installation
pip list
```

### Step 3: Configure Environment

```powershell
# Ensure .env.backend exists in the backend directory
# (Should already be filled from project setup)

# Test configuration loading
python -m app.config
```

Expected output:
```
✅ Configuration loaded successfully!
App Name: AI English Assessment Backend
Environment: development
Debug Mode: True
Supabase URL: https://...
Azure OpenAI Endpoint: https://...
CORS Origins: ['http://localhost:5173', 'http://localhost:3000']
```

---

## 🚀 Running the Server

### Development Mode (with auto-reload)

```powershell
# Method 1: Using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Method 2: Using Python module
python -m app.main

# Method 3: Using the run script (after creation)
python run.py
```

The server will start at: **http://localhost:8000**

### Access API Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

---

## 🧪 Testing the API

### Test Health Check

```powershell
# Using PowerShell
Invoke-WebRequest -Uri http://localhost:8000/health | Select-Object -Expand Content

# Using curl
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "environment": "development"
}
```

### Test Configuration

```powershell
curl http://localhost:8000/api/v1/config/test
```

Expected response:
```json
{
  "supabase_configured": true,
  "azure_openai_configured": true,
  "azure_speech_configured": true,
  "azure_storage_configured": true
}
```

---

## 📦 Dependencies Explained

### Core Framework
- **fastapi** - Modern web framework
- **uvicorn** - ASGI server
- **pydantic** - Data validation

### Database
- **supabase** - Database client
- **psycopg2-binary** - PostgreSQL adapter

### Azure Services
- **openai** - Azure OpenAI SDK
- **azure-cognitiveservices-speech** - Speech services
- **azure-storage-blob** - Blob storage

### Audio Processing
- **librosa** - Audio analysis
- **pydub** - Audio manipulation
- **soundfile** & **numpy** - Audio I/O

### Security
- **python-jose** - JWT tokens
- **passlib** - Password hashing

---

## 🔧 Development Workflow

### 1. Create New Endpoint

```python
# In app/routers/your_router.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/your-resource", tags=["Your Resource"])

@router.get("/")
async def list_resources():
    return {"items": []}
```

### 2. Register Router

```python
# In app/main.py
from app.routers import your_router

app.include_router(your_router.router)
```

### 3. Test Endpoint

Visit: http://localhost:8000/docs

---

## 🧪 Running Tests

```powershell
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api.py

# Run with verbose output
pytest -v
```

---

## 🐛 Troubleshooting

### Import Error: "No module named 'app'"

**Solution:** Run from the backend directory:
```powershell
cd backend
python -m app.main
```

### "Address already in use" Error

**Solution:** Kill the process on port 8000:
```powershell
# Find process
netstat -ano | findstr :8000

# Kill process (replace PID with actual number)
taskkill /PID <PID> /F
```

### Configuration Not Loading

**Solution:** Ensure `.env.backend` is in the `backend` directory:
```powershell
# Check if file exists
Test-Path .env.backend

# Verify contents
Get-Content .env.backend | Select-String "SUPABASE_URL"
```

### Azure SDK Errors

**Solution:** Verify your API keys are correct:
```python
python -m app.config
# Check if all services show as configured
```

---

## 📝 Environment Variables Checklist

Before running the server, ensure these are set in `.env.backend`:

- [ ] SUPABASE_URL
- [ ] SUPABASE_ANON_KEY
- [ ] SUPABASE_SERVICE_ROLE_KEY
- [ ] AZURE_OPENAI_ENDPOINT
- [ ] AZURE_OPENAI_API_KEY
- [ ] AZURE_SPEECH_KEY
- [ ] AZURE_SPEECH_REGION
- [ ] AZURE_STORAGE_CONNECTION_STRING
- [ ] SECRET_KEY

---

## 🚢 Production Deployment

### Build for Production

```powershell
# Install production dependencies only
pip install --no-dev -r requirements.txt

# Run with production server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Environment Variables

Set `APP_ENV=production` and `DEBUG=False` in production.

---

## 📚 Next Steps

1. ✅ Verify server runs successfully
2. ⏭️ Implement Azure Speech service (`app/services/azure_speech.py`)
3. ⏭️ Implement Azure OpenAI service (`app/services/azure_openai.py`)
4. ⏭️ Implement Blob Storage service (`app/services/blob_storage.py`)
5. ⏭️ Create API routers for assessments
6. ⏭️ Implement scoring engine

---

**Need help?** Check the main IMPLEMENTATION_PLAN.md or ask for assistance!
