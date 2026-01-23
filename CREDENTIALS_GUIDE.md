# 🔑 QUICK CREDENTIAL COLLECTION GUIDE

Use this checklist to gather all your credentials step by step.

---

## 📋 STEP 1: SUPABASE (5 minutes)

### 1.1 Create Account & Project
1. Go to: https://supabase.com
2. Click "Start Your Project"
3. Sign up with GitHub or Email
4. Click "New Project"
5. Fill in:
   - Project Name: `ai-english-assessment`
   - Database Password: (choose strong password - SAVE IT!)
   - Region: Choose closest to you
   - Plan: Free tier is fine for development

### 1.2 Get Credentials
1. Once project is created, go to: **Settings > API**
2. Copy these values into **BOTH** `.env.backend` and `.env.frontend`:

```
✅ Project URL → SUPABASE_URL / VITE_SUPABASE_URL
✅ anon public key → SUPABASE_ANON_KEY / VITE_SUPABASE_ANON_KEY
✅ service_role key → SUPABASE_SERVICE_ROLE_KEY (backend only)
```

3. Go to: **Settings > Database**
4. Scroll to "Connection String" section
5. Copy "URI" format:
```
✅ Connection string → SUPABASE_DB_URL (backend only)
```
6. Replace `[YOUR-PASSWORD]` with the password you set in step 1.1

**Status:** [ ] Complete

---

## 📋 STEP 2: AZURE OPENAI (15-30 minutes)

### 2.1 Apply for Access
⚠️ **IMPORTANT:** This requires approval (1-2 business days)

1. Go to: https://aka.ms/oai/access
2. Fill out the application form:
   - Use business/educational email (not personal)
   - Explain use case: "Educational English language assessment platform"
3. Wait for approval email

### 2.2 Create Azure Account (while waiting for approval)
1. Go to: https://portal.azure.com
2. Sign up (Free tier available - $200 credit)
3. Complete verification

### 2.3 Create Azure OpenAI Resource (after approval)
1. In Azure Portal, click "+ Create a resource"
2. Search for "Azure OpenAI"
3. Click "Create"
4. Fill in:
   - Resource group: Create new → `ai-assessment-rg`
   - Region: East US (has best model availability)
   - Name: `ai-english-openai`
   - Pricing tier: Standard

### 2.4 Deploy GPT-4o Model
1. Go to: https://oai.azure.com
2. Click "Deployments"
3. Click "+ Create new deployment"
4. Select:
   - Model: `gpt-4o`
   - Deployment name: `gpt-4o` (save this name!)
5. Click "Create"

### 2.5 Get Credentials
1. Back in Azure Portal → Your OpenAI resource
2. Go to: **Keys and Endpoint**
3. Copy into `.env.backend`:

```
✅ Endpoint → AZURE_OPENAI_ENDPOINT
✅ KEY 1 → AZURE_OPENAI_API_KEY
✅ Deployment name (from 2.4) → AZURE_OPENAI_DEPLOYMENT_NAME
```

**Status:** [ ] Complete

---

## 📋 STEP 3: AZURE SPEECH SERVICES (5 minutes)

### 3.1 Create Speech Resource
1. In Azure Portal, click "+ Create a resource"
2. Search for "Speech"
3. Click "Speech" by Microsoft
4. Click "Create"
5. Fill in:
   - Resource group: Select `ai-assessment-rg`
   - Region: Same as OpenAI (East US)
   - Name: `ai-english-speech`
   - Pricing tier: Free F0 (or Standard S0)

### 3.2 Get Credentials
1. Go to your Speech resource
2. Click: **Keys and Endpoint**
3. Copy into `.env.backend`:

```
✅ KEY 1 → AZURE_SPEECH_KEY
✅ Location/Region → AZURE_SPEECH_REGION
```

**Status:** [ ] Complete

---

## 📋 STEP 4: AZURE BLOB STORAGE (5 minutes)

### 4.1 Create Storage Account
1. In Azure Portal, click "+ Create a resource"
2. Search for "Storage account"
3. Click "Create"
4. Fill in:
   - Resource group: Select `ai-assessment-rg`
   - Storage account name: `aienglishstorage` (must be globally unique)
   - Region: Same as above
   - Performance: Standard
   - Redundancy: LRS (cheapest for dev)

### 4.2 Create Container
1. Go to your Storage Account
2. In left menu, click "Containers"
3. Click "+ Container"
4. Name: `assessment-audio`
5. Public access level: **Private**
6. Click "Create"

### 4.3 Get Credentials
1. In left menu, click **Access keys**
2. Click "Show" next to key1
3. Copy into `.env.backend`:

```
✅ Connection string → AZURE_STORAGE_CONNECTION_STRING
```

**Status:** [ ] Complete

---

## 📋 STEP 5: GENERATE SECRET KEY (1 minute)

### 5.1 Generate Random Secret
Run this command in PowerShell:

```powershell
# Option 1: Simple random string
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | ForEach-Object {[char]$_})

# Option 2: If you have OpenSSL installed
openssl rand -hex 32
```

Copy the output into `.env.backend`:
```
✅ Generated string → SECRET_KEY
```

**Status:** [ ] Complete

---

## ✅ FINAL CHECKLIST

Before proceeding to development, verify you have:

### Backend Environment (`.env.backend`)
- [ ] SUPABASE_URL
- [ ] SUPABASE_ANON_KEY
- [ ] SUPABASE_SERVICE_ROLE_KEY
- [ ] SUPABASE_DB_URL
- [ ] AZURE_OPENAI_ENDPOINT
- [ ] AZURE_OPENAI_API_KEY
- [ ] AZURE_OPENAI_DEPLOYMENT_NAME
- [ ] AZURE_SPEECH_KEY
- [ ] AZURE_SPEECH_REGION
- [ ] AZURE_STORAGE_CONNECTION_STRING
- [ ] SECRET_KEY

### Frontend Environment (`.env.frontend`)
- [ ] VITE_SUPABASE_URL
- [ ] VITE_SUPABASE_ANON_KEY

---

## 🎯 NEXT STEPS

Once all credentials are collected:

1. **Verify `.env.backend` file:**
   - All `PASTE_YOUR_*_HERE` placeholders are replaced
   - No trailing spaces
   - No quotes around values (unless they contain spaces)

2. **Verify `.env.frontend` file:**
   - Same as above

3. **Test connections:**
   ```bash
   # We'll create test scripts in Phase 1
   ```

4. **Proceed to Phase 1:**
   - Open `IMPLEMENTATION_PLAN.md`
   - Start with "PHASE 1: DATABASE FOUNDATION"

---

## 💡 TIPS

### If Azure OpenAI Access is Delayed
- Start with Phases 0 and 1 (database setup)
- Use OpenAI API as temporary alternative (not recommended for production)
- Continue with other Azure services

### If You're on Free Tier
- Supabase Free: ✅ 500MB database, 1GB file storage
- Azure Free: ✅ $200 credit for 30 days
- After credits: ~$50-100/month for moderate usage

### Cost Saving Tips
1. Use Free tier during development
2. Delete test resources after development
3. Set budget alerts in Azure
4. Use smaller audio sample rates for testing

---

## ❓ TROUBLESHOOTING

### "Connection string invalid"
- Ensure no extra spaces or quotes
- Verify you replaced `[YOUR-PASSWORD]` in Supabase DB URL

### "Azure OpenAI 404 error"
- Verify deployment name matches exactly
- Check model is deployed in Azure OpenAI Studio
- Verify API version is correct

### "Speech recognition not working"
- Check region matches (e.g., `eastus` not `East US`)
- Verify key is copied completely

---

## 📞 NEED HELP?

If you're stuck on any step:
1. Check the detailed `ENV_TEMPLATE.md`
2. Review Azure/Supabase documentation
3. Ask me for specific guidance!

**Ready to paste your credentials? Let me know when you're done! 🚀**
