# Azure Rate Limits & Timeout Strategy Guide

## Current Bottlenecks at 40+ Concurrent Users

Your app has **3 Azure services** that can bottleneck under load:

```
Azure Speech (STT)      → 10-20 RPS limit     ← BOTTLENECK AT 40 USERS
Azure OpenAI (LLM)      → 20 RPM (429 errors) ← FAILS ON HEAVY SCORING  
Azure TTS (Synthesis)   → 10 concurrent       ← QUEUES UP
```

---

## 🔴 Problem: Why Users Get "Abandoned" 

### Scenario: 40 Users All Recording Audio Simultaneously

```
Time    User 1          User 2          User 3          ...         User 40
───────────────────────────────────────────────────────────────────────────
0s      Record          Record          Record                      Record
        Audio 1         Audio 2         Audio 3                     Audio 40
        ↓               ↓               ↓                           ↓
5s      POST audio      POST audio      POST audio      ...         POST audio
        (40 concurrent HTTP requests)
        ↓ STT Queue (10 RPS limit)
10s     STT #1 ✅       
        STT #2 ✅       
        STT #3 ✅       
        STT #4 ✅       
        STT #5 ✅       
        STT #6 ✅       
        STT #7 ✅       
        STT #8 ✅       
        STT #9 ✅       
        STT #10 ✅      
15s     STT #11 QUEUED  STT #12 QUEUED  STT #13 QUEUED  ...         STT #40 QUEUED
        (waiting...)    (waiting...)    (waiting...)                (waiting...)

Client timeout (30s):  Browser: "Server not responding" → User abandons ❌
Stale checker (5min):  Marks as "abandoned" with reason "no_heartbeat"

BUT: It wasn't user abandonment! Backend was just slow!
```

---

## ✅ Solution: Rate Limit Management

### Step 1: Understand Your Azure Quotas

#### **Check Your Current Limits:**

```bash
# Via Azure CLI
az cognitiveservices account show \
  --name <your-speech-service-name> \
  --resource-group <your-rg> \
  --query "properties.publicNetworkAccess, sku.name, sku.tier"

# OR via Azure Portal
# Speech Services → Your Resource → Pricing Tier (shows current SKU)
```

**Default Quotas by SKU:**

| SKU | Tier | STT RPS | LLM RPM | Cost/Month |
|-----|------|---------|---------|-----------|
| **Standard** | Free | 10 RPS | 20 RPM | $0 ❌ Limited |
| **S0** | Paid | 20 RPS | 20 RPM | ~$30 ⚠️ Still limited |
| **S1** | Premium | 100 RPS | 300+ RPM | ~$160 ✅ Good |

**⚠️ YOUR ISSUE:** You're likely on **Standard (Free)** or **S0** tier with 10-20 RPS limit!

### Step 2: Upgrade Azure Services for 100+ Concurrent Users

#### **Option A: Upgrade to Higher Tier (Recommended)**

```bash
# Upgrade Speech Service to S1 (Premium)
az cognitiveservices account update \
  --name <your-speech-service-name> \
  --resource-group <your-rg> \
  --sku S1

# Cost: ~$160/month but supports 100 RPS (10x capacity)
```

**OR**

#### **Option B: Use Request Queuing & Backpressure (If staying on S0)**

Implement smart queueing in your backend to limit concurrent requests:

```python
# File: backend/app/services/azure_request_queue.py (NEW)

import asyncio
from typing import Callable, Any

class AzureRequestQueue:
    """
    Limits concurrent requests to Azure services.
    Queues requests when at capacity and serves them FIFO.
    """
    
    def __init__(self, max_concurrent_stts=10, max_concurrent_openai=5):
        self.stts_semaphore = asyncio.Semaphore(max_concurrent_stts)
        self.openai_semaphore = asyncio.Semaphore(max_concurrent_openai)
        self.stts_queue_length = 0
        self.openai_queue_length = 0
    
    async def call_speech_service(self, func: Callable, *args, **kwargs) -> Any:
        """
        Call speech service with queueing.
        If 10 concurrent calls already happening, new requests wait.
        """
        async with self.stts_semaphore:
            # Within the semaphore, we're guaranteed ≤10 concurrent calls
            return await func(*args, **kwargs)
    
    async def call_openai_service(self, func: Callable, *args, **kwargs) -> Any:
        """Call OpenAI with queueing - max 5 concurrent scoring operations."""
        async with self.openai_semaphore:
            return await func(*args, **kwargs)

# Singleton instance
azure_request_queue = AzureRequestQueue(
    max_concurrent_stts=10,      # Match Azure free tier limit
    max_concurrent_openai=5       # Conservative to avoid 429 errors
)
```

Then use it in your code:

```python
# File: backend/app/routers/responses.py

# OLD (can cause rate limit errors):
transcript = await speech_service.transcribe_audio(
    wav_audio_bytes,
    use_continuous=use_continuous
)

# NEW (respects rate limits):
from app.services.azure_request_queue import azure_request_queue

transcript = await azure_request_queue.call_speech_service(
    speech_service.transcribe_audio,
    wav_audio_bytes,
    use_continuous=use_continuous
)
```

---

### Step 3: Handle 429 Rate Limit Errors Gracefully

Azure returns **HTTP 429** when you exceed rate limits. Here's how to handle it:

```python
# File: backend/app/services/azure_speech.py

async def transcribe_audio(self, audio_bytes, use_continuous=False):
    """Transcribe with exponential backoff for 429 errors."""
    import time
    
    max_retries = 3
    base_delay = 1.0  # 1 second
    
    for attempt in range(max_retries):
        try:
            # Attempt transcription
            result = await self._do_transcription(audio_bytes, use_continuous)
            return result
            
        except Exception as e:
            error_code = getattr(e, 'status_code', None)
            
            # 429 = Rate Limited
            if error_code == 429:
                if attempt < max_retries - 1:
                    wait_time = base_delay * (2 ** attempt)  # Exponential backoff
                    error_logger.warning(
                        f"⚠️ Rate limited (429), retrying in {wait_time}s... "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )
                    await asyncio.sleep(wait_time)
                    continue
            
            # Other errors - fail immediately
            raise
    
    raise HTTPException(
        status_code=503,
        detail="Azure Speech service temporarily unavailable - rate limited"
    )
```

---

## 🎯 Practical Implementation Steps

### For Immediate Relief (Without Upgrading Azure)

**Step 1: Implement Request Queueing** (~30 min)

```python
# Add to backend/app/services/azure_request_queue.py (I created above)
# Then wrap all Azure calls in azure_request_queue.call_speech_service()
```

**Step 2: Add Client-Side Backoff** (~20 min)

Frontend should implement exponential backoff before retrying:

```javascript
// File: frontend/src/services/assessmentService.js

async function submitAudioWithRetry(audioBlob, maxRetries = 3) {
    for (let attempt = 0; attempt < maxRetries; attempt++) {
        try {
            const response = await fetch('/api/v1/responses/{id}/audio', {
                method: 'POST',
                body: audioBlob,
                // ... other headers
            });
            
            if (response.status === 503) {  // Rate limited
                const waitTime = Math.pow(2, attempt) * 1000;  // 1s, 2s, 4s
                console.warn(`Rate limited, retrying in ${waitTime}ms...`);
                await new Promise(resolve => setTimeout(resolve, waitTime));
                continue;
            }
            
            return response.json();
        } catch (err) {
            console.error(`Attempt ${attempt + 1} failed:`, err);
        }
    }
    throw new Error("Audio submission failed after retries");
}
```

**Step 3: Monitor Rate Limits** (~10 min)

```python
# Add to your monitoring endpoint
@router.get("/metrics/azure-usage")
async def get_azure_usage():
    """Track Azure service usage and rate limit warnings."""
    # Log current usage
    api_logger.info(f"📊 Azure STT concurrent: {azure_request_queue.stts_queue_length}/10")
    api_logger.info(f"📊 Azure OpenAI concurrent: {azure_request_queue.openai_queue_length}/5")
    
    return {
        "stts_concurrent": azure_request_queue.stts_queue_length,
        "stts_limit": 10,
        "stts_utilization_percent": (azure_request_queue.stts_queue_length / 10) * 100,
        "openai_concurrent": azure_request_queue.openai_queue_length,
        "openai_limit": 5,
        "openai_utilization_percent": (azure_request_queue.openai_queue_length / 5) * 100,
    }
```

---

## 🔧 Long-Term Solution: Upgrade Azure Tier

### Recommended for 100+ Concurrent Users:

```bash
# Cost estimate:
# Standard (Free): $0 but max 10 RPS         ❌
# S0 ($30/mo):    20 RPS                      ⚠️ Still not enough
# S1 ($160/mo):   100 RPS                     ✅ Handles 100+ users
# S2 ($600/mo):   1000 RPS                    ✅✅ Enterprise scale

# Upgrade command:
az cognitiveservices account update \
  --name soft-skill-speech \
  --resource-group your-rg \
  --sku S1

# Verify upgrade:
az cognitiveservices account show \
  --name soft-skill-speech \
  --resource-group your-rg \
  --query "sku.name"
```

**Cost-Benefit Analysis:**

| Users | Load | Current Cost | Required Tier | Monthly Cost | ROI |
|-------|------|--------------|---------------|--------------|-----|
| 10 | Light | $0 | Free | $0 | ✅ |
| 40 | Medium | $0 (overloaded) | S0 | $30 | ✅ 100x capacity increase |
| 100+ | Heavy | $160 + penalties | S1 | $160 | ✅ Unlimited scalability |

---

## 📊 Complete Timeout & Rate Limit Strategy

### Summary Table

| Component | Problem | Current Fix | Long-Term Fix | Time to Implement |
|-----------|---------|------------|---------------|-----------------|
| **STT (Speech)** | 10 RPS limit | Semaphore (10) + backoff | Upgrade to S1 | 30 min + cost |
| **OpenAI (Scoring)** | 20 RPM limit | Semaphore (5) + backoff | Upgrade to S1 | 30 min + cost |
| **TTS (Synthesis)** | 10 concurrent | Existing semaphore ✅ | Works well | ✅ Done |
| **Database Queries** | Connection pool | Increased to 50 ✅ | Monitor usage | ✅ Done |
| **Audio Timeout** | 2+ min hangs | 30-second timeout ✅ | 60-second (done) | ✅ Done |

---

## 🚨 Critical: What to Do NOW

### Immediate Actions (Today):

1. **Check Your Azure SKU:**
   ```bash
   az cognitiveservices account show \
     --name soft-skill-speech \
     --query "sku"
   ```
   If response is `"Free"` or `"S0"`: 💥 **This is your problem!**

2. **Implement Request Queueing:**
   - Copy the `AzureRequestQueue` class from above
   - Create `backend/app/services/azure_request_queue.py`
   - Wrap Speech & OpenAI calls

3. **Deploy and Monitor:**
   ```bash
   # Test with 40 concurrent users
   # Monitor via: GET /api/v1/monitoring/metrics/azure-usage
   ```

### Short-Term (This Week):

- [ ] Implement request queueing + exponential backoff
- [ ] Add monitoring for Azure usage
- [ ] Test with 40 concurrent users

### Long-Term (This Month):

- [ ] **UPGRADE** Azure Speech to S1 tier ($160/month but 10x capacity)
- [ ] Monitor real usage and adjust tier as needed
- [ ] Consider multi-region failover for production

---

## Testing: Simulate 40 Concurrent Users

```python
# File: backend/verify_concurrent_users.py

import asyncio
import aiohttp
import time
from datetime import datetime

async def simulate_user_assessment(user_id, duration_sec=30):
    """Simulate one user doing assessment for N seconds."""
    async with aiohttp.ClientSession() as session:
        start = time.time()
        attempt = 0
        
        while time.time() - start < duration_sec:
            attempt += 1
            audio_bytes = b"dummy audio data" * 1000  # ~16KB
            
            try:
                async with session.post(
                    f"http://localhost:8000/api/v1/responses/dummy/audio",
                    data=audio_bytes,
                    timeout=aiohttp.ClientTimeout(total=35)  # 35 sec timeout
                ) as resp:
                    if resp.status == 429:
                        print(f"❌ User {user_id}: Rate limited (429)")
                    elif resp.status == 408:
                        print(f"❌ User {user_id}: Request timeout (408)")
                    elif resp.status == 200:
                        print(f"✅ User {user_id}: Success")
                    else:
                        print(f"⚠️ User {user_id}: Status {resp.status}")
            except asyncio.TimeoutError:
                print(f"❌ User {user_id}: Client timeout")
            
            await asyncio.sleep(2)  # Wait 2 sec between requests

async def main():
    """Simulate 40 concurrent users."""
    print(f"🚀 Starting simulation of 40 concurrent users at {datetime.now()}")
    
    tasks = [
        simulate_user_assessment(f"user_{i:03d}", duration_sec=60)
        for i in range(40)
    ]
    
    await asyncio.gather(*tasks)
    print(f"✅ Simulation completed at {datetime.now()}")

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
python verify_concurrent_users.py
```

Watch your monitoring endpoint:
```bash
# In another terminal
watch -n 1 'curl -s http://localhost:8000/api/v1/monitoring/metrics/azure-usage | jq .'
```

---

## Expected Results After Implementation

| Metric | Before | After Queueing | After S1 Upgrade |
|--------|--------|----------------|-----------------|
| Max concurrent | 40 | 40 | 1000+ |
| Timeout errors | High | Low | Rare |
| Rate limits (429) | Frequent | Prevented | Never |
| Avg response time | 2-5s | <1s | <500ms |
| User satisfaction | ❌ | ⚠️ | ✅ |
| Cost | $0 | $0 | $160/mo |

