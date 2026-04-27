"""
Shared concurrency primitives for external API calls.

All OpenAI clients (ConversationalAgent, AzureOpenAIService, ScoringEngine)
MUST use these semaphores to stay within Azure RPM/TPM quotas.

Two semaphores — one per deployment — so gpt-4o and gpt-4o-mini have
independent concurrency budgets matching their independent rate limits.

Tuned for 100+ concurrent users with Azure Standard tier quotas:
- gpt-4o-mini: 10,000 RPM, 1M TPM → 25 per-worker (100 global)
- gpt-4o: 300 RPM, 300K TPM → 6 per-worker (24 global)
- Azure Speech S0: 100 concurrent STT, 200 TPS TTS → 20 per-worker (80 global STT, 80 TTS)
"""
import asyncio

# Interactive deployment (gpt-4o-mini): used for conversation turns
# 25 per worker * 4 workers = 100 global concurrent (well within 10K RPM / 1M TPM)
# That's enough for 100+ simultaneous users each having a turn
openai_mini_semaphore = asyncio.Semaphore(25)   # Per-worker limit

# Full deployment (gpt-4o): used for holistic scoring + audio grading
# 6 per worker * 4 workers = 24 global concurrent
# Stays under GPT-4o RPM (300) and TPM (300K) limits
openai_full_semaphore = asyncio.Semaphore(6)    # Per-worker limit (was 12, reduced for TPM safety)

# Azure Speech Service semaphores (Standard S0 tier limits)
# S0 Limits: STT=100 concurrent, TTS=200 TPS
# With 4 Gunicorn workers, set per-worker limits so total stays within quotas:
# - STT: 20/worker × 4 = 80 global (under 100, leaves headroom)
# - TTS: 20/worker × 4 = 80 global (well under 200 TPS limit)
speech_stt_semaphore = asyncio.Semaphore(20)   # Per-worker STT limit
speech_tts_semaphore = asyncio.Semaphore(20)   # Per-worker TTS limit
