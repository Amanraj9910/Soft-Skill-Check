# Production Analysis & Optimization Guide

## 🔴 Critical Bugs & Production Issues

### 1. **Duplicate Function Definition (CRITICAL BUG)**
**Location:** `backend/app/services/ai_assessment/scoring_engine.py`

**Issue:** `analyze_full_assessment()` is defined **twice** (lines 137-269 and 271-403). This will cause the second definition to override the first, potentially causing unexpected behavior.

**Fix:**
```python
# Remove the duplicate definition (lines 271-403)
# Keep only the first one (lines 137-269)
```

**Impact:** High - Could cause runtime errors or incorrect behavior.

---

### 2. **Missing Import (RUNTIME ERROR)**
**Location:** `backend/app/services/ai_assessment/scoring_engine.py:202`

**Issue:** Uses `asyncio.to_thread()` but `asyncio` is not imported.

**Fix:**
```python
import asyncio  # Add at top of file
```

**Impact:** High - Will crash when `analyze_full_assessment()` is called.

---

### 3. **In-Memory Session Storage (DATA LOSS RISK)**
**Location:** `backend/app/services/session_manager.py`

**Issue:** Sessions stored in memory will be lost on:
- Server restart
- Deployment
- Container restart
- Auto-scaling events

**Impact:** High - Users will lose conversation state mid-assessment.

**Recommendation:**
- Store sessions in Redis or database
- Add session persistence layer
- Implement session recovery on restart

---

### 4. **Unverified JWT Token (SECURITY VULNERABILITY)**
**Location:** `backend/app/routers/assessments.py:40`

**Issue:** Uses `jwt.get_unverified_claims()` - **does not verify token signature**.

**Code:**
```python
payload = jwt.get_unverified_claims(token)  # ⚠️ UNSAFE
```

**Fix:**
```python
from jose import jwt
from app.config import settings

# Verify token with Supabase JWT secret
try:
    payload = jwt.decode(
        token,
        settings.SUPABASE_JWT_SECRET,  # Add to config
        algorithms=["RS256"],
        audience="authenticated"
    )
    user_id = payload.get("sub")
except jwt.ExpiredSignatureError:
    raise HTTPException(status_code=401, detail="Token expired")
except jwt.JWTError:
    raise HTTPException(status_code=401, detail="Invalid token")
```

**Impact:** Critical - Anyone can forge tokens and access any user's data.

---

### 5. **No Audio File Size Validation**
**Location:** `backend/app/routers/responses.py:238`

**Issue:** Audio files uploaded without size check. Could cause:
- Memory exhaustion
- Storage quota exceeded
- Slow processing

**Fix:**
```python
MAX_AUDIO_SIZE = 10 * 1024 * 1024  # 10MB

audio_bytes = await audio_file.read()
if len(audio_bytes) > MAX_AUDIO_SIZE:
    raise HTTPException(
        status_code=413, 
        detail=f"Audio file too large. Max size: {MAX_AUDIO_SIZE / 1024 / 1024}MB"
    )
```

---

### 6. **Race Condition in Session Management**
**Location:** `backend/app/services/session_manager.py:19-39`

**Issue:** Multiple concurrent requests for same `response_id` could create duplicate sessions or lose data.

**Fix:**
```python
import threading

def __init__(self):
    self.sessions: Dict[str, Dict[str, Any]] = {}
    self._lock = threading.Lock()

def get_session(self, response_id: str) -> Dict[str, Any]:
    with self._lock:
        if response_id not in self.sessions:
            # ... create session
        return self.sessions[response_id]
```

---

### 7. **Background Task Failures Silent**
**Location:** `backend/app/routers/responses.py:63-121`

**Issue:** Background tasks catch exceptions but only log. No retry mechanism or user notification.

**Fix:**
- Add retry logic with exponential backoff
- Store failed tasks in database for manual retry
- Send alerts for critical failures

---

### 8. **Memory Leak: Audio Blob URLs Not Revoked**
**Location:** `frontend/src/hooks/useAudioRecorder.js:100-101`

**Issue:** `URL.createObjectURL()` creates blob URLs that must be revoked. Multiple recordings create memory leaks.

**Fix:**
```javascript
// In stopRecording, before creating new URL:
if (audioUrl) {
    URL.revokeObjectURL(audioUrl);
}
```

---

### 9. **No Timeout for Azure Speech STT**
**Location:** `backend/app/services/ai_assessment/azure_speech.py:131`

**Issue:** `recognize_once_async().get()` blocks indefinitely if Azure service hangs.

**Fix:**
```python
import asyncio

result = asyncio.wait_for(
    asyncio.to_thread(lambda: speech_recognizer.recognize_once_async().get()),
    timeout=30.0
)
```

---

### 10. **Missing Error Handling in Audio Conversion**
**Location:** `backend/app/services/ai_assessment/azure_speech.py:79`

**Issue:** `subprocess.run()` with `check=False` - errors are silently ignored.

**Fix:**
```python
result = subprocess.run(cmd, check=False, capture_output=True, text=True)
if result.returncode != 0:
    error_logger.error(f"FFmpeg failed: {result.stderr}")
    raise Exception(f"Audio conversion failed: {result.stderr}")
```

---

## ⚠️ Production Risks

### 11. **No Rate Limiting on Expensive Endpoints**
**Location:** `backend/app/routers/responses.py:203`

**Issue:** Audio upload endpoint calls:
- STT (Azure Speech)
- GPT-4o (expensive)
- TTS (Azure Speech)
- Blob upload

No rate limiting = potential cost explosion.

**Fix:** Add rate limiting middleware:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/{response_id}/audio")
@limiter.limit("5/minute")  # 5 requests per minute per IP
async def upload_response_audio(...):
```

---

### 12. **No Connection Pooling for Supabase**
**Location:** `backend/app/services/supabase_client.py`

**Issue:** Each request may create new connections, causing connection exhaustion under load.

**Fix:** Use connection pooling or persistent client.

---

### 13. **Large Payloads in Background Tasks**
**Location:** `backend/app/routers/responses.py:361-372`

**Issue:** Passing entire `session` object to background task. If session is large, this consumes memory.

**Fix:** Pass only necessary data:
```python
background_tasks.add_task(
    process_transition_background,
    response_id,
    user_id,
    assessment_id,
    section_name,
    list(session['conversation_history']),  # Copy list, not entire session
    update_payload,
    client
)
```

---

### 14. **No Health Check Endpoint**
**Issue:** No `/health` endpoint for load balancer/probe.

**Fix:** Add to `main.py`:
```python
@router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}
```

---

### 15. **Frontend: No Retry Logic for Failed Requests**
**Location:** `frontend/src/services/api.js`

**Issue:** Network failures cause permanent errors. No automatic retry.

**Fix:** Add retry interceptor:
```javascript
import axiosRetry from 'axios-retry';

axiosRetry(api, {
    retries: 3,
    retryDelay: axiosRetry.exponentialDelay,
    retryCondition: (error) => {
        return axiosRetry.isNetworkOrIdempotentRequestError(error) ||
               error.response?.status >= 500;
    }
});
```

---

## 🚀 Latency Optimization Recommendations

### 1. **Parallelize Sequential Operations (HIGH IMPACT)**

**Current Flow (Sequential):**
```
STT (2-5s) → GPT-4o (3-8s) → TTS (1-3s) → Upload (1-2s) = 7-18s total
```

**Optimized Flow (Parallel where possible):**
```python
# In upload_response_audio():
import asyncio

# 1. Transcribe (must be first)
transcript = await asyncio.to_thread(speech_service.transcribe_audio, wav_audio_bytes)

# 2. Get agent response (depends on transcript)
agent_result = await asyncio.to_thread(
    conversational_agent.get_response,
    user_message=transcript,
    section=section_name,
    conversation_history=session['conversation_history'],
    turn_count=session['turn_count']
)

# 3. Generate TTS in parallel with scoring (if not transitioning)
if should_transition:
    # Calculate scores
    analysis_result = await asyncio.to_thread(
        scoring_engine.analyze_response,
        transcript=user_full_transcript,
        question=section_name,
        context={"history": session['conversation_history']}
    )
    
    # Generate TTS in parallel
    ai_audio_task = asyncio.create_task(
        asyncio.to_thread(speech_service.synthesize_speech_bytes, ai_response_text)
    )
    
    # Wait for both
    ai_audio_bytes = await ai_audio_task
```

**Expected Improvement:** 30-40% faster (5-11s instead of 7-18s)

---

### 2. **Cache Greeting Audio (MEDIUM IMPACT)**

**Location:** `frontend/src/pages/Assessment.jsx:70`

**Issue:** Greeting audio generated on every stage entry.

**Fix:**
```javascript
// Cache greetings by stage
const greetingCache = new Map();

const playGreeting = async () => {
    if (greetingCache.has(currentStage.id)) {
        const cachedUrl = greetingCache.get(currentStage.id);
        const audio = new Audio(cachedUrl);
        await audio.play();
        return;
    }
    
    const response = await conversationService.getGreeting(currentStage.id);
    if (response.audio_url) {
        greetingCache.set(currentStage.id, response.audio_url);
        // ... play audio
    }
};
```

**Expected Improvement:** 1-3s saved per stage (greeting already cached)

---

### 3. **Stream Audio Upload (MEDIUM IMPACT)**

**Location:** `frontend/src/services/assessmentService.js:82-88`

**Issue:** Entire audio blob loaded into memory before upload.

**Fix:** Use streaming upload:
```javascript
const formData = new FormData();
formData.append('audio_file', responseData.audio, 'recording.wav');

// Use streaming upload
const response = await fetch(`${API_BASE_URL}/api/v1/responses/${responseId}/audio`, {
    method: 'POST',
    body: formData,
    headers: {
        'Authorization': `Bearer ${token}`
    }
});
```

**Expected Improvement:** Faster perceived upload, lower memory usage

---

### 4. **Optimize Database Queries (MEDIUM IMPACT)**

**Location:** `backend/app/routers/responses.py:219-224`

**Issue:** Multiple separate queries that could be combined.

**Current:**
```python
response_result = client.table("assessment_responses")
    .select("*, assessments!inner(user_id)")
    .eq("id", response_id)
    .execute()
```

**Optimized:** Already using join, but could batch more operations.

---

### 5. **Use Async Supabase Client (MEDIUM IMPACT)**

**Issue:** Using synchronous Supabase client blocks event loop.

**Fix:** Use `supabase-py` async client or wrap in `asyncio.to_thread()` consistently.

---

### 6. **Pre-generate Common AI Responses (LOW-MEDIUM IMPACT)**

**Issue:** Same questions get different AI responses each time.

**Fix:** Cache common responses (e.g., "Could you tell me more?") to reduce GPT-4o calls.

---

### 7. **Compress Audio Before Upload (LOW IMPACT)**

**Location:** `frontend/src/services/assessmentService.js:82`

**Issue:** Uploading raw WebM/MP4. Could compress to reduce upload time.

**Fix:**
```javascript
// Compress audio before upload (if size > threshold)
if (audioBlob.size > 1024 * 1024) {  // > 1MB
    const compressed = await compressAudio(audioBlob);
    formData.append('audio_file', compressed, 'recording.wav');
}
```

---

### 8. **Add Request Deduplication (LOW IMPACT)**

**Issue:** User double-clicking "Submit" sends duplicate requests.

**Fix:**
```javascript
let isSubmitting = false;

const handleStopRecording = async () => {
    if (isSubmitting) return;  // Prevent duplicate
    isSubmitting = true;
    try {
        // ... existing logic
    } finally {
        isSubmitting = false;
    }
};
```

---

## 📊 Performance Metrics to Monitor

1. **API Response Times:**
   - `/api/v1/responses/{id}/audio` - Target: < 15s
   - `/api/v1/assessments/{id}/complete` - Target: < 10s

2. **Azure Service Latency:**
   - STT: < 3s
   - GPT-4o: < 8s
   - TTS: < 2s

3. **Database Query Times:**
   - Assessment queries: < 100ms
   - Response queries: < 50ms

4. **Memory Usage:**
   - Session storage: Monitor growth
   - Audio blob memory: Monitor leaks

---

## 🔧 Quick Wins (Implement First)

1. ✅ Fix duplicate function definition
2. ✅ Add missing `asyncio` import
3. ✅ Add audio file size validation
4. ✅ Add request deduplication
5. ✅ Fix JWT token verification
6. ✅ Add health check endpoint
7. ✅ Add rate limiting
8. ✅ Fix memory leaks (revoke blob URLs)

---

## 🎯 Long-term Optimizations

1. **Move sessions to Redis** - Persist across restarts
2. **Implement request queuing** - Handle traffic spikes
3. **Add CDN for audio files** - Faster delivery
4. **Implement WebSocket** - Real-time progress updates
5. **Add database indexing** - Faster queries
6. **Implement caching layer** - Reduce API calls

---

## 📝 Testing Checklist

Before production deployment, test:

- [ ] Server restart during active assessment (session recovery)
- [ ] Concurrent requests from same user
- [ ] Large audio files (10MB+)
- [ ] Network interruptions during upload
- [ ] Azure service outages (graceful degradation)
- [ ] Token expiration during long assessment
- [ ] Memory usage under load (100+ concurrent users)
- [ ] Database connection pool exhaustion

---

## 🚨 Emergency Rollback Plan

If issues occur in production:

1. **Disable new assessments:**
   ```python
   @router.post("/")
   async def create_assessment(...):
       raise HTTPException(503, "Service temporarily unavailable")
   ```

2. **Enable maintenance mode:**
   - Return 503 for all endpoints
   - Show maintenance page on frontend

3. **Database backup:**
   - Ensure daily backups
   - Test restore procedure

---

**Last Updated:** 2026-01-27
**Priority:** Fix critical bugs before production deployment.
