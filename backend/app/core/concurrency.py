"""
Shared concurrency primitives for external API calls.

All OpenAI clients (ConversationalAgent, AzureOpenAIService, ScoringEngine)
MUST use these semaphores to stay within Azure RPM quotas.

Two semaphores — one per deployment — so gpt-4o and gpt-4o-mini have
independent concurrency budgets matching their independent rate limits.

Tuned for 100+ concurrent users with Azure Standard tier quotas:
- gpt-4o-mini: 300 RPM, 150K TPM → 25 concurrent
- gpt-4o: 150 RPM, 30K TPM → 12 concurrent
- Azure Speech S0: 50 concurrent STT, 20 concurrent TTS
"""
import asyncio

# Interactive deployment (gpt-4o-mini): used for conversation turns
# Allow more concurrency since mini has its own quota and is faster
# Tuned for 100+ concurrent users (each user drives ~1 concurrent turn)
openai_mini_semaphore = asyncio.Semaphore(25)

# Full deployment (gpt-4o): used for holistic scoring + audio grading
# Lower because scoring is heavy and we want to leave headroom
# Tuned for 100+ users: scoring runs as background tasks, so burst is smaller
openai_full_semaphore = asyncio.Semaphore(12)

# Azure Speech Service semaphores (Standard S0 tier limits)
# STT: 50 concurrent, TTS: 20 concurrent - leave 20% headroom
speech_stt_semaphore = asyncio.Semaphore(40)
speech_tts_semaphore = asyncio.Semaphore(16)
