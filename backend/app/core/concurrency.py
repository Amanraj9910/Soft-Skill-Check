"""
Shared concurrency primitives for external API calls.

All OpenAI clients (ConversationalAgent, AzureOpenAIService, ScoringEngine)
MUST use these semaphores to stay within Azure RPM quotas.

Two semaphores — one per deployment — so gpt-4o and gpt-4o-mini have
independent concurrency budgets matching their independent rate limits.
"""
import asyncio

# Interactive deployment (gpt-4o-mini): used for conversation turns
# Allow more concurrency since mini has its own quota and is faster
# Tuned for 30+ concurrent users (each user drives ~1 concurrent turn)
openai_mini_semaphore = asyncio.Semaphore(25)

# Full deployment (gpt-4o): used for holistic scoring + audio grading
# Lower because scoring is heavy and we want to leave headroom
# Tuned for 30+ users: scoring runs as background tasks, so burst is smaller
openai_full_semaphore = asyncio.Semaphore(12)
