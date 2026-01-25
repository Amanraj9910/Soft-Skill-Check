# Security Configuration Notes

## PostgreSQL Security

### Function Search Path

All PostgreSQL functions now include `SET search_path = ''` to prevent search path injection attacks. This was applied via migration `008_security_fixes.sql`.

**Functions secured:**
- `handle_updated_at`
- `handle_new_user`
- `calculate_assessment_duration`
- `update_user_stats_on_assessment`
- `calculate_wpm`
- `calculate_word_count`
- `calculate_total_score`
- `sync_score_to_assessment`
- `calculate_audio_metrics`
- `calculate_vision_ratios`
- `user_owns_assessment`

### RLS Policy Performance

All Row Level Security policies have been optimized to use `(select auth.uid())` instead of `auth.uid()` directly. This prevents the function from being re-evaluated for each row, improving query performance at scale.

---

## Supabase Auth Security

### Enable HaveIBeenPwned Password Check

To protect users from compromised passwords:

1. Go to **Supabase Dashboard** → **Authentication** → **Settings**
2. Under **Security**, find **Leaked Password Protection**
3. Enable **"Reject passwords found in data breaches"**

This checks passwords against the HaveIBeenPwned database during signup/password change.

---

## Additional Recommendations

1. **Enable SSL/TLS**: Ensure all API endpoints use HTTPS in production
2. **Rate Limiting**: Already configured via `RATE_LIMIT_PER_MINUTE` in settings
3. **JWT Expiration**: Set to 30 minutes by default (`ACCESS_TOKEN_EXPIRE_MINUTES`)
4. **CORS**: Configured to allow only specific origins
