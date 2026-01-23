# 🔐 ENVIRONMENT VARIABLES CONFIGURATION GUIDE

This document lists **all required environment variables** for both the **Backend** and **Frontend** of the AI English Speaking Assessment Platform.

---

## 📝 INSTRUCTIONS

1. **Copy the templates** below into your respective `.env` files:
   - `.env.backend` (for FastAPI backend)
   - `.env.frontend` (for React frontend)

2. **Fill in the values** with your actual credentials and connection strings

3. **Never commit** these files to Git (they're in `.gitignore`)

4. **For production:** Use Azure Key Vault or environment variables in Azure App Service

---

## 🔧 BACKEND ENVIRONMENT VARIABLES

### File: `.env.backend`

```env
# ============================================
# APPLICATION SETTINGS
# ============================================
APP_NAME=AI_English_Assessment_Backend
APP_ENV=development
# Options: development, staging, production
DEBUG=True
# Set to False in production

# ============================================
# SERVER CONFIGURATION
# ============================================
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
# Comma-separated list of allowed origins

# ============================================
# SUPABASE DATABASE
# ============================================
SUPABASE_URL=
# Example: https://xxxxxxxxxxxxx.supabase.co
# Where to get it:
# 1. Go to https://app.supabase.com
# 2. Select your project
# 3. Go to Settings > API
# 4. Copy "Project URL"

SUPABASE_ANON_KEY=
# Example: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
# Where to get it:
# 1. Same location as SUPABASE_URL
# 2. Copy "anon public" key
# Note: This is safe to use client-side

SUPABASE_SERVICE_ROLE_KEY=
# Example: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
# Where to get it:
# 1. Same location as SUPABASE_URL
# 2. Copy "service_role" key
# ⚠️ WARNING: Keep this SECRET! Never expose client-side!

SUPABASE_DB_URL=
# Example: postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxxxxx.supabase.co:5432/postgres
# Where to get it:
# 1. Go to Settings > Database
# 2. Copy "Connection string" > "URI"
# 3. Replace [YOUR-PASSWORD] with your database password

# ============================================
# AZURE OPENAI SERVICE
# ============================================
AZURE_OPENAI_ENDPOINT=
# Example: https://your-resource-name.openai.azure.com/
# Where to get it:
# 1. Go to https://portal.azure.com
# 2. Navigate to your OpenAI resource
# 3. Go to "Keys and Endpoint"
# 4. Copy "Endpoint"

AZURE_OPENAI_API_KEY=
# Example: 1234567890abcdef1234567890abcdef
# Where to get it:
# 1. Same location as endpoint
# 2. Copy "KEY 1" or "KEY 2"

AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
# Your deployment name for GPT-4o
# Where to get it:
# 1. Go to Azure OpenAI Studio
# 2. Navigate to "Deployments"
# 3. Copy your GPT-4o deployment name

AZURE_OPENAI_API_VERSION=2024-02-15-preview
# API version for Azure OpenAI
# Check latest: https://learn.microsoft.com/en-us/azure/ai-services/openai/reference

# ============================================
# AZURE SPEECH SERVICES
# ============================================
AZURE_SPEECH_KEY=
# Example: 1234567890abcdef1234567890abcdef
# Where to get it:
# 1. Go to https://portal.azure.com
# 2. Navigate to your Speech Service resource
# 3. Go to "Keys and Endpoint"
# 4. Copy "KEY 1"

AZURE_SPEECH_REGION=
# Example: eastus, westeurope, etc.
# Where to get it:
# 1. Same location as AZURE_SPEECH_KEY
# 2. Copy "Location/Region"

AZURE_SPEECH_LANGUAGE=en-US
# Speech recognition language
# Options: en-US, en-GB, en-IN, etc.

AZURE_TTS_VOICE_NAME=en-US-JennyNeural
# Neural voice for Text-to-Speech
# Options: en-US-JennyNeural, en-US-GuyNeural, etc.
# Full list: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support

# ============================================
# AZURE BLOB STORAGE
# ============================================
AZURE_STORAGE_CONNECTION_STRING=
# Example: DefaultEndpointsProtocol=https;AccountName=youraccount;AccountKey=yourkey;EndpointSuffix=core.windows.net
# Where to get it:
# 1. Go to https://portal.azure.com
# 2. Navigate to your Storage Account
# 3. Go to "Access keys"
# 4. Copy "Connection string"

AZURE_STORAGE_CONTAINER_NAME=assessment-audio
# Name of the blob container for audio files
# You'll create this in Azure Storage

AZURE_BLOB_SAS_EXPIRY_HOURS=24
# Hours before SAS URLs expire

# ============================================
# SECURITY & JWT (for custom auth if needed)
# ============================================
SECRET_KEY=
# Generate with: openssl rand -hex 32
# Example: 09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7

ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ============================================
# RATE LIMITING
# ============================================
RATE_LIMIT_PER_MINUTE=60
# Max API calls per minute per user

# ============================================
# AUDIO PROCESSING
# ============================================
MAX_AUDIO_DURATION_SECONDS=300
# Maximum recording duration (5 minutes)

AUDIO_SAMPLE_RATE=16000
# Sample rate for audio processing

AUDIO_FORMAT=wav
# Supported: wav, mp3

# ============================================
# LOGGING
# ============================================
LOG_LEVEL=INFO
# Options: DEBUG, INFO, WARNING, ERROR, CRITICAL

# ============================================
# OPTIONAL: THIRD-PARTY SERVICES
# ============================================

# Sentry (Error Tracking)
SENTRY_DSN=
# Get from: https://sentry.io

# SendGrid (Email Service)
SENDGRID_API_KEY=
# Get from: https://sendgrid.com
```

---

## 🌐 FRONTEND ENVIRONMENT VARIABLES

### File: `.env.frontend`

**Important:** All Vite environment variables must be prefixed with `VITE_`

```env
# ============================================
# SUPABASE CLIENT
# ============================================
VITE_SUPABASE_URL=
# Example: https://xxxxxxxxxxxxx.supabase.co
# Same as backend SUPABASE_URL

VITE_SUPABASE_ANON_KEY=
# Example: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
# Same as backend SUPABASE_ANON_KEY
# This is the PUBLIC key, safe to expose

# ============================================
# BACKEND API
# ============================================
VITE_API_BASE_URL=http://localhost:8000
# Your backend API URL
# Production: https://your-backend.azurewebsites.net

VITE_API_TIMEOUT=30000
# API request timeout in milliseconds

# ============================================
# MEDIAPIPE (Optional, if self-hosting models)
# ============================================
VITE_MEDIAPIPE_MODEL_URL=https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite
# Default MediaPipe CDN URL
# You can leave this as-is or host the model yourself

# ============================================
# FEATURE FLAGS
# ============================================
VITE_ENABLE_VIDEO_ANALYSIS=true
# Enable/disable MediaPipe vision features

VITE_ENABLE_AUDIO_PLAYBACK=true
# Allow users to playback their recordings

VITE_ENABLE_DARK_MODE=true
# Enable dark mode toggle

# ============================================
# APPLICATION SETTINGS
# ============================================
VITE_APP_NAME=AI English Assessment
VITE_APP_VERSION=1.0.0

# ============================================
# ANALYTICS (Optional)
# ============================================
VITE_GA_MEASUREMENT_ID=
# Google Analytics Measurement ID
# Example: G-XXXXXXXXXX

VITE_HOTJAR_ID=
# Hotjar tracking ID

# ============================================
# SENTRY (Frontend Error Tracking)
# ============================================
VITE_SENTRY_DSN=
# Sentry DSN for frontend error tracking
```

---

## 📋 CHECKLIST: GETTING YOUR CREDENTIALS

### ✅ Supabase Setup

1. **Sign up:** https://supabase.com
2. **Create project**
3. **Get credentials:**
   - [ ] Project URL
   - [ ] Anon/Public Key
   - [ ] Service Role Key
   - [ ] Database Connection String (with password)

**Documentation:** https://supabase.com/docs/guides/getting-started

---

### ✅ Azure OpenAI Setup

1. **Apply for access:** https://aka.ms/oai/access
   - ⚠️ Approval can take 1-2 business days
2. **Create Azure OpenAI resource** in Azure Portal
3. **Deploy GPT-4o model**
4. **Get credentials:**
   - [ ] Endpoint URL
   - [ ] API Key
   - [ ] Deployment Name
   - [ ] API Version

**Documentation:** https://learn.microsoft.com/en-us/azure/ai-services/openai/quickstart

---

### ✅ Azure Speech Services Setup

1. **Create Speech Service** in Azure Portal
2. **Get credentials:**
   - [ ] Subscription Key
   - [ ] Region

**Documentation:** https://learn.microsoft.com/en-us/azure/ai-services/speech-service/overview

---

### ✅ Azure Blob Storage Setup

1. **Create Storage Account** in Azure Portal
2. **Create container:** `assessment-audio`
3. **Set access level:** Private
4. **Get credentials:**
   - [ ] Connection String

**Documentation:** https://learn.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-portal

---

## 🔒 SECURITY BEST PRACTICES

1. **Never commit `.env` files** to Git
2. **Use different credentials** for development and production
3. **Rotate keys regularly** (every 90 days)
4. **Use Azure Key Vault** for production secrets
5. **Limit permissions** (principle of least privilege)
6. **Monitor usage** for unusual activity

---

## 🚀 NEXT STEPS

1. **Copy templates** into actual `.env` files:
   ```bash
   # In the backend directory
   touch .env.backend
   
   # In the frontend directory  
   touch .env.frontend
   ```

2. **Fill in all values** using the guides above

3. **Test configuration:**
   ```bash
   # Backend
   cd backend
   python -m app.config  # Should print loaded config
   
   # Frontend
   cd frontend
   npm run dev  # Check console for loaded env vars
   ```

4. **Proceed to Phase 1** of the implementation plan!

---

## ❓ QUESTIONS?

If you need help getting any of these credentials, let me know and I'll provide detailed step-by-step instructions!
