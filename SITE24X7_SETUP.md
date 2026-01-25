# Site24x7 Monitoring Setup Guide

This guide explains how to configure Site24x7 for monitoring the SpeakAssess application.

## Prerequisites

1. A Site24x7 account (sign up at [site24x7.com](https://www.site24x7.com/))
2. Your Site24x7 API key

## Backend Configuration

### 1. Configure Environment Variables

Add your Site24x7 API key to `.env.backend`:

```env
# ============================================
# SITE24X7 MONITORING
# ============================================
SITE24X7_API_KEY=your-api-key-here
SITE24X7_ENABLED=True
```

### 2. Available Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/health` | Simple health check (returns "healthy") |
| `/status` | Comprehensive status with database & Azure checks |

## Site24x7 Dashboard Configuration

### Option 1: Website Monitor (Recommended)

1. Go to **Site24x7 Dashboard** → **Admin** → **Inventory** → **Add Monitor**
2. Select **Website**
3. Configure:
   - **Display Name**: SpeakAssess API
   - **Website URL**: `https://your-domain.com/status`
   - **Check Frequency**: 5 minutes
   - **HTTP Method**: GET
   - **Match Content**: `"status":"healthy"`
   - **Alert Threshold**: 2 consecutive failures

### Option 2: REST API Monitor (Advanced)

For detailed monitoring:

1. Select **REST API**
2. Configure the `/status` endpoint
3. Add assertions:
   - Status code = 200 (healthy) or 503 (unhealthy)
   - Response contains `status` field

## Alert Configuration

### Recommended Alerts

1. **High Priority**: 
   - Database connectivity failures
   - 503 status responses (system unhealthy)

2. **Medium Priority**:
   - Response time > 5 seconds
   - Degraded status responses

3. **Low Priority**:
   - Azure services unreachable

### Status Response Example

When the `/status` endpoint is called, it returns:

```json
{
  "status": "healthy",
  "timestamp": "2026-01-25T12:00:00+00:00",
  "version": "1.0.0",
  "environment": "development",
  "checks": {
    "database": {
      "status": "healthy",
      "latency_ms": 45.23,
      "message": "Connected"
    },
    "azure": {
      "status": "healthy",
      "latency_ms": 120.45,
      "message": "Endpoint reachable"
    }
  }
}
```

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | System healthy or degraded but operational |
| 503 | System unhealthy - critical services down |

## Troubleshooting

### Common Issues

1. **"Site24x7 monitoring disabled" in logs**
   - Ensure `SITE24X7_ENABLED=True` in `.env.backend`
   - Verify API key is set

2. **Database check fails**
   - Verify Supabase credentials
   - Check network connectivity to Supabase

3. **Azure check shows degraded**
   - This may be normal if Azure endpoint requires authentication
   - Only indicates endpoint is reachable, not authenticated
