# Azure SKU Tiers Explained: S1 Across Services

## 🎯 What is "S1"? (It's service-specific)

---

## 1️⃣ **Azure Speech Service - S1 (Your Main Concern)**

### Current vs Needed

| Aspect | Your Current (Standard) | S1 (Recommended) |
|--------|------------------------|-----------------|
| **Name** | Standard (Free tier) | Standard (Paid) - Called "S0" or "S1" |
| **RPS Limit** | 10 RPS (requests/sec) | 20-100 RPS depending on region |
| **Cost** | $0 (limited) | $30-160/month |
| **Users** | ~10 concurrent ❌ | 20-100 concurrent ✅ |
| **Suitable For** | Testing only | Production |

### Your Speech Service SKU Breakdown

```
Standard (FREE TIER):
├─ 10 Requests Per Second (RPS)
├─ Good for: Testing, demos, <10 users
├─ Cost: $0
└─ Problem: Causes 429 errors at 40+ users ❌

S0 (STANDARD - PAID):
├─ 20 RPS
├─ $30/month
├─ Better than Free but still limited

S1 (STANDARD - PREMIUM):
├─ 100 RPS (in some regions, 50 RPS in others)
├─ $160/month
├─ Supports 100+ concurrent users ✅
└─ This is what you need!
```

### Check Your Current Speech Service Tier

```bash
# List your Speech Services
az cognitiveservices account list --query "[].{name:name, kind:kind, sku:sku.name}"

# Example output:
# [
#   {
#     "name": "soft-skill-speech",
#     "kind": "SpeechServices",
#     "sku": "F0"    ← F0 = Free tier! This is your problem
#   }
# ]

# Check specific details
az cognitiveservices account show \
  --name soft-skill-speech \
  --resource-group your-rg-name \
  --query "{sku: sku.name, tier: sku.tier, capabilities: properties.capabilities}"
```

---

## 2️⃣ **Azure App Service - S1 (Different Context)**

### What S1 Means Here

App Service uses **instance sizes** (not rate limits):

| SKU | CPU | RAM | Disk | Cost/month | Use Case |
|-----|-----|-----|------|-----------|----------|
| **B1** (Basic) | 1 core | 1.75 GB | 10 GB | $12 | Dev/Test |
| **B2** (Basic) | 2 cores | 3.5 GB | 10 GB | $25 | Small production |
| **S1** (Standard) | 1 core | 1.75 GB | 50 GB | $75 | Standard production |
| **S2** (Standard) | 2 cores | 3.5 GB | 50 GB | $150 | High traffic |
| **S3** (Standard) | 4 cores | 7 GB | 50 GB | $300 | Enterprise |

**S1 on App Service** = More resources, faster processing, handles more requests

### Your Situation

If you're running Gunicorn/Python backend on App Service:
- **Current tier:** Unknown (check portal)
- **Recommended for 40 users:** At least **S1 or B2**
- **Relationship to Speech Service:** Independent — they both need sizing!

---

## 3️⃣ **Azure OpenAI - S0/S1 (LLM API)**

### NOT Called "S1" - Uses Different Naming

Azure OpenAI doesn't use "S1" tier naming. Instead:

```
Pricing Model:
├─ Pay-per-token (default)
├─ Reserved Capacity (PTU - Provisioned Throughput Units)
│  ├─ Minimum: 100 PTU = $2,000/month
│  └─ Maximum: 1M+ PTU
└─ TPM Limits (tokens per minute):
   ├─ Default: 120K TPM
   └─ With PTU: Variable (100 PTU = 380K TPM approx)
```

**What you need to know:**

Your LLM is likely on **default pay-per-token** model with a rate limit of **20 requests per minute (RPM)**

When scoring 40 concurrent assessments:
- Each scoring call = 1 request
- 40 concurrent = hits 20 RPM limit immediately ❌
- Solution: Request queueing (I provided in guide) or upgrade to PTU

---

## 🎯 SUMMARY: Your Real Problem

You have **3 mismatched services**:

```
┌─────────────────────────────────────────────────────────┐
│ SERVICE              │ CURRENT          │ NEED          │
├─────────────────────────────────────────────────────────┤
│ Speech Service       │ F0 (Free, 10 RPS)  │ S1 (100 RPS) ❌
│ OpenAI (LLM)         │ Default (20 RPM)   │ PTU or queue ⚠️
│ App Service          │ Unknown            │ At least S1  ?
│ Database             │ Supabase Free      │ May need paid
└─────────────────────────────────────────────────────────┘
```

---

## ✅ HOW TO FIX - Step by Step

### Step 1: Upgrade Speech Service to S1

```bash
# Current: F0 (Free) → Change to S1 (Standard Premium)

# Check current
az cognitiveservices account show \
  --name soft-skill-speech \
  --resource-group your-resource-group \
  --query "sku"

# Upgrade to S1
az cognitiveservices account update \
  --name soft-skill-speech \
  --resource-group your-resource-group \
  --sku S1

# Verify
az cognitiveservices account show \
  --name soft-skill-speech \
  --resource-group your-resource-group \
  --query "sku"
```

**Cost:** $160/month (increases from $0)
**Benefit:** 10x capacity (100 RPS instead of 10 RPS) ✅

---

### Step 2: Check Your App Service Tier

```bash
# List App Services
az appservice plan list --query "[].{name:name, sku:sku.name, tier:sku.tier}"

# If you see "B1" or "FREE":
az appservice plan update \
  --name your-plan-name \
  --resource-group your-rg \
  --sku S1
```

**Cost:** ~$75/month (if currently Free or B1)
**Benefit:** More CPU/RAM for concurrent requests ✅

---

### Step 3: Monitor Your Tier Change

```bash
# After upgrading, test with 40 concurrent users
python verify_concurrent_users.py  # Script from my guide

# Monitor in real-time
watch -n 2 'curl -s http://your-api/api/v1/monitoring/health/system-status | jq .'
```

---

## 📊 Cost Breakdown - 40 Concurrent Users

### Before (Current - BROKEN):
```
Speech Service:  $0 (Free tier)    but rate limits at 40 users ❌
App Service:     $0 (Free)         but slows down ⚠️
OpenAI LLM:      $0-50/month       but 20 RPM limit ❌
Total:           ~$50/month        but DOESN'T WORK for 40 users
```

### After (Fixed - WORKS):
```
Speech Service:  $160/month        (S1 tier, 100 RPS) ✅
App Service:     $75/month         (S1, 1-2 cores) ✅
OpenAI LLM:      $100-200/month    (pay per token) ✅
Total:           ~$335-440/month   HANDLES 100+ users perfectly
```

---

## 🔍 How to Check What You Currently Have

### Azure Portal Method:

1. **Speech Service:**
   - Go to Azure Portal → Your Resource Group
   - Click "soft-skill-speech" (or your Speech Service name)
   - Look at top right corner → "Pricing Tier"
   - Shows: **F0** (Free) or **S1** (Standard)

2. **App Service:**
   - Go to Azure Portal → Your Resource Group
   - Click your App Service name
   - Left sidebar → "App Service Plan"
   - Shows: **Free**, **B1**, **B2**, **S1**, etc.

3. **Azure OpenAI:**
   - Go to Azure Portal → Your Resource Group
   - Click "your-openai-resource"
   - Left sidebar → "Keys and Endpoint"
   - Usually on default **pay-per-token** (20 RPM limit)

### CLI Method:

```bash
# One command to check everything
echo "=== Speech Service ===" && \
az cognitiveservices account show --name soft-skill-speech --resource-group your-rg --query "sku" && \
echo "=== App Service Plan ===" && \
az appservice plan show --name your-plan --resource-group your-rg --query "sku" && \
echo "=== OpenAI ===" && \
az cognitiveservices account show --name your-openai --resource-group your-rg --query "sku"
```

---

## 🎯 RECOMMENDED CONFIGURATION FOR 40+ USERS

```
Speech Service:     S1 tier ($160/month)
├─ 100 RPS limit
├─ Supports 100+ concurrent transcriptions
└─ Premium support included

App Service:        S1 tier ($75/month)
├─ 1 core CPU
├─ 1.75 GB RAM
├─ 4 Gunicorn workers
└─ Handles 100+ concurrent requests

Azure OpenAI:       Default (pay-per-token)
├─ OR upgrade to PTU if using heavily
├─ With request queueing (5 concurrent max)
└─ Prevents 429 rate limit errors

Database:           Supabase Standard or Postgres
├─ Monitor connections
└─ Currently good with 50-conn limit

Total Monthly Cost: ~$235-335
Capacity:          100+ concurrent users ✅
```

---

## 🚀 Implementation Order

1. **TODAY:**
   - [ ] Check current Speech Service tier: `az cognitiveservices account show...`
   - [ ] If F0: Upgrade to S1 (see command above)

2. **THIS WEEK:**
   - [ ] Check App Service tier
   - [ ] Upgrade if B1/Free to S1

3. **DEPLOY:**
   - [ ] Test with 40 concurrent users
   - [ ] Monitor: `curl http://api/monitoring/health/system-status`

---

## ❓ Common Confusion Cleared

| Question | Answer |
|----------|--------|
| **Is S1 same across all Azure services?** | NO - Each service defines their own SKUs |
| **What does "Standard" mean?** | For Speech: Free tier. For App Service: Entry paid tier |
| **Do I need S1 for ALL services?** | Speech Service: YES. App Service: At least S1. OpenAI: Maybe PTU |
| **What if I stay on F0?** | Works for <10 users. 40 users = constant 429 errors |
| **Can I downgrade later?** | Yes, anytime. But it takes effect next month |

---

## Final Checklist

```bash
# 1. Check Speech Service
az cognitiveservices account show \
  --name soft-skill-speech \
  --resource-group YOUR_RG \
  --query "{sku: sku.name, rpsLimit: 'check-portal'}"

# Expected if F0: {"sku": "F0", "rpsLimit": "10 RPS"}
# Need: {"sku": "S1", "rpsLimit": "100 RPS"}

# 2. If F0, upgrade
az cognitiveservices account update \
  --name soft-skill-speech \
  --resource-group YOUR_RG \
  --sku S1

# 3. Verify upgrade succeeded
az cognitiveservices account show \
  --name soft-skill-speech \
  --resource-group YOUR_RG \
  --query "sku"

# Expected: {"name": "S1", "tier": "Standard"}
```

Done! 🎉
