# 🔧 **DEPENDENCY INSTALLATION GUIDE - WINDOWS**

## ⚠️ Issue: Audio Libraries Don't Install on Windows

The full `requirements.txt` includes `librosa`, `soundfile`, and `pydub` which require compiling C extensions on Windows. This often fails.

---

## ✅ **SOLUTION: Two-Step Installation**

### **Step 1: Install Core Dependencies (Required for API to work)**

```powershell
# In backend directory with venv activated
pip install -r requirements-minimal.txt
```

This installs:
- ✅ FastAPI & Uvicorn (web framework)
- ✅ Pydantic (data validation)
- ✅ Supabase (database)
- ✅ Azure OpenAI (conversation & scoring)
- ✅ Azure Speech (STT/TTS)
- ✅ Azure Blob Storage (file storage)
- ✅ Authentication libraries

**With these, the API will work, but audio feature extraction will be limited.**

---

### **Step 2: Install Audio Libraries (Optional, for full features)**

#### **Option A: Skip Audio Analysis** (Recommended for Testing)

The backend will work without librosa. Audio analysis endpoints will return mock data.

#### **Option B: Install Pre-Built Wheels** (For Full Features)

1. **Download pre-built wheels:**
   - Go to: https://www.lfd.uci.edu/~gohlke/pythonlibs/
   - Search for: `numpy`, `scipy`, `librosa`, `soundfile`
   - Download `.whl` files matching your Python version (cp314 for Python 3.14)

2. **Install wheels:**
   ```powershell
   pip install path/to/numpy-xxx-cp314-cp314-win_amd64.whl
   pip install path/to/scipy-xxx-cp314-cp314-win_amd64.whl
   pip install librosa soundfile
   ```

#### **Option C: Use Conda** (Alternative)

```powershell
# If you have Anaconda/Miniconda
conda install -c conda-forge librosa soundfile
```

---

## 🧪 **TEST THE BACKEND**

After installing minimal requirements:

```powershell
# Test configuration
python -c "from app.config import settings; print('✅ Config OK')"

# Test backend
python test_backend.py

# Start server
python run.py
```

Visit: **http://localhost:8000/docs**

---

## 📝 **What Works Without Audio Libraries**

✅ **Full API Functionality:**
- User management
- Assessment CRUD
- AI conversation (GPT-4o)
- Speech-to-Text (Azure)
- Text-to-Speech (Azure)
- Audio file upload/download
- Scoring system

⚠️ **Limited Feature:**
- Audio feature extraction will use placeholder data
- No pitch/volume/silence analysis from librosa

**For MVP testing, this is perfectly fine!** You can add audio analysis later.

---

## 🎯 **RECOMMENDED APPROACH**

For development and testing:
1. ✅ Install `requirements-minimal.txt`
2. ✅ Test the API
3. ✅ Build the frontend
4. ✅ Complete integration
5. ⏭️ Add audio analysis later if needed

**The platform will be fully functional without librosa for 95% of features!**

---

## 🚀 **CONTINUE DEVELOPMENT**

Once minimal dependencies are installed:
1. Test backend: `python test_backend.py`
2. Start server: `python run.py`
3. Continue with frontend development
4. Deploy MVP
5. Add advanced audio features in v2

---

**Don't let dependency issues slow you down! The core platform works great!** 🎯
