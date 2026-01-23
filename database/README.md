# 📊 Database Migrations Guide

This directory contains all SQL migrations for the AI English Assessment Platform database.

---

## 🎯 How to Run Migrations

### Option 1: Supabase Dashboard (Recommended for First-Time Setup)

1. **Go to your Supabase project dashboard**
   - Visit: https://app.supabase.com
   - Select your project

2. **Open SQL Editor**
   - Click "SQL Editor" in the left sidebar
   - Click "New Query"

3. **Run each migration in order:**
   - Copy the contents of `001_create_profiles.sql`
   - Paste into the SQL Editor
   - Click "Run" or press `Ctrl+Enter`
   - **Verify success** (you should see "Success. No rows returned")
   - Repeat for migrations `002` through `007`

### Option 2: Using Supabase CLI

```bash
# Install Supabase CLI
npm install -g supabase

# Login to Supabase
supabase login

# Run migrations
supabase db push
```

### Option 3: Using psql (PostgreSQL CLI)

```bash
# Connect to your database
psql "postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres"

# Run each migration
\i database/migrations/001_create_profiles.sql
\i database/migrations/002_create_assessments.sql
\i database/migrations/003_create_assessment_responses.sql
\i database/migrations/004_create_assessment_scores.sql
\i database/migrations/005_create_audio_features.sql
\i database/migrations/006_create_vision_metrics.sql
\i database/migrations/007_setup_rls_policies.sql
```

---

## 📋 Migration Order

**IMPORTANT:** Run migrations in this exact order!

1. ✅ **001_create_profiles.sql** - Creates user profiles table
2. ✅ **002_create_assessments.sql** - Creates main assessments table
3. ✅ **003_create_assessment_responses.sql** - Creates responses table
4. ✅ **004_create_assessment_scores.sql** - Creates scores table
5. ✅ **005_create_audio_features.sql** - Creates audio analysis table
6. ✅ **006_create_vision_metrics.sql** - Creates vision metrics table
7. ✅ **007_setup_rls_policies.sql** - Enables security policies

---

## 🔍 Verify Migrations Success

After running all migrations, execute this SQL to verify:

```sql
-- Check all tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY table_name;

-- Expected tables:
-- assessment_responses
-- assessment_scores
-- assessments
-- audio_features
-- profiles
-- vision_metrics

-- Check RLS is enabled
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public';
-- All should show rowsecurity = true

-- Check policies exist
SELECT tablename, policyname 
FROM pg_policies 
WHERE schemaname = 'public'
ORDER BY tablename;
-- Should show multiple policies per table
```

---

## 🗄️ Database Schema Overview

### Tables Created:

#### 1. **profiles**
- Extends Supabase auth.users
- Stores user profile info
- Auto-created on signup

#### 2. **assessments**
- Main assessment records
- Tracks status, scores, audio URLs
- Links to user profiles

#### 3. **assessment_responses**
- Individual section responses
- Stores transcripts, audio, metrics
- One per conversation stage

#### 4. **assessment_scores**
- Detailed category scoring
- 7 scoring dimensions
- Strengths/weaknesses/recommendations

#### 5. **audio_features**
- Extracted audio characteristics
- Volume, pitch, silence, pace
- For confidence scoring

#### 6. **vision_metrics**
- MediaPipe face detection data
- Eye contact, head stability
- For clarity scoring

---

## 🔐 Security Features

### Row Level Security (RLS)
- All tables have RLS enabled
- Users can only access their own data
- Backend uses service_role for admin operations

### Policies Applied:
- Users can view/update own profile
- Users can create/view own assessments
- Users can view own scores
- Backend (service_role) has full access

---

## 🛠️ Rollback Migrations

If you need to undo migrations:

```sql
-- Drop all tables (DANGER: This deletes all data!)
DROP TABLE IF EXISTS public.vision_metrics CASCADE;
DROP TABLE IF EXISTS public.audio_features CASCADE;
DROP TABLE IF EXISTS public.assessment_scores CASCADE;
DROP TABLE IF EXISTS public.assessment_responses CASCADE;
DROP TABLE IF EXISTS public.assessments CASCADE;
DROP TABLE IF EXISTS public.profiles CASCADE;

-- Drop custom types
DROP TYPE IF EXISTS assessment_status CASCADE;
DROP TYPE IF EXISTS assessment_grade CASCADE;
DROP TYPE IF EXISTS assessment_section CASCADE;

-- Drop functions
DROP FUNCTION IF EXISTS public.handle_updated_at CASCADE;
DROP FUNCTION IF EXISTS public.handle_new_user CASCADE;
DROP FUNCTION IF EXISTS public.calculate_assessment_duration CASCADE;
DROP FUNCTION IF EXISTS public.update_user_stats_on_assessment CASCADE;
DROP FUNCTION IF EXISTS public.calculate_wpm CASCADE;
DROP FUNCTION IF EXISTS public.calculate_word_count CASCADE;
DROP FUNCTION IF EXISTS public.calculate_total_score CASCADE;
DROP FUNCTION IF EXISTS public.sync_score_to_assessment CASCADE;
DROP FUNCTION IF EXISTS public.calculate_audio_metrics CASCADE;
DROP FUNCTION IF EXISTS public.calculate_vision_ratios CASCADE;
DROP FUNCTION IF EXISTS public.user_owns_assessment CASCADE;
```

---

## ✅ Next Steps After Migration

1. **Verify all tables exist** (run verification queries above)
2. **Test RLS policies** in Supabase dashboard
3. **Create a test user** via Supabase Auth
4. **Verify profile auto-creation** (check profiles table)
5. **Proceed to backend setup** (Phase 2 of implementation)

---

## 📞 Troubleshooting

### "relation already exists" error
- Table already created, you can skip that migration
- Or drop and recreate (see Rollback section)

### "permission denied" error
- Ensure you're using the correct database password
- Check your Supabase connection string

### "syntax error" near a line
- Ensure you copied the entire SQL file
- Check for encoding issues (use UTF-8)

### RLS policies not working
- Verify `auth.uid()` is not NULL (user must be authenticated)
- Check policies with: `SELECT * FROM pg_policies;`

---

**Need help?** Check the main documentation or ask for assistance!
