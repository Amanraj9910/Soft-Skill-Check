"""
Deep health check endpoint.
Reports the real status of all external dependencies (Supabase, Azure OpenAI, Blob Storage).
Returns 503 if any critical dependency is down, enabling Container Apps auto-restart.
"""
import time
import asyncio
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.services.supabase_client import supabase_service
from app.services.azure_openai import azure_openai_service
from app.services.ai_assessment.azure_storage import storage_service
from app.core.logging import api_logger

router = APIRouter(tags=["Health"])


async def _check_supabase() -> dict:
    start = time.monotonic()
    try:
        await asyncio.wait_for(supabase_service.ping(), timeout=3.0)
        return {"ok": True, "latency_ms": round((time.monotonic() - start) * 1000)}
    except asyncio.TimeoutError:
        return {"ok": False, "error": "timeout (>3s)"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:120]}


async def _check_blob_storage() -> dict:
    start = time.monotonic()
    try:
        if not storage_service.container_client:
            return {"ok": False, "error": "not configured"}
        exists = await asyncio.wait_for(
            asyncio.to_thread(storage_service.container_client.exists),
            timeout=3.0
        )
        return {"ok": exists, "latency_ms": round((time.monotonic() - start) * 1000)}
    except asyncio.TimeoutError:
        return {"ok": False, "error": "timeout (>3s)"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:120]}


async def _check_openai() -> dict:
    start = time.monotonic()
    try:
        # Cheapest possible call: 1 token in, 1 token out
        resp = await asyncio.wait_for(
            azure_openai_service.client.chat.completions.create(
                model=azure_openai_service.deployment_name,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1,
            ),
            timeout=10.0,
        )
        return {"ok": True, "latency_ms": round((time.monotonic() - start) * 1000)}
    except asyncio.TimeoutError:
        return {"ok": False, "error": "timeout (>10s)"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:120]}


@router.get("/health")
async def health_check():
    """
    Deep health check — probes all external dependencies.
    Returns 200 if all ok, 503 if any critical service is degraded.
    Used by Container Apps for liveness/readiness probes.
    """
    checks = await asyncio.gather(
        _check_supabase(),
        _check_blob_storage(),
        _check_openai(),
        return_exceptions=True,
    )

    results = {}
    labels = ["supabase", "blob_storage", "azure_openai"]
    for label, result in zip(labels, checks):
        if isinstance(result, Exception):
            results[label] = {"ok": False, "error": str(result)[:120]}
        else:
            results[label] = result

    all_ok = all(v.get("ok") for v in results.values())
    status = "healthy" if all_ok else "degraded"
    status_code = 200 if all_ok else 503

    if not all_ok:
        api_logger.warning(f"Health check degraded: {results}")

    return JSONResponse(
        content={"status": status, "checks": results},
        status_code=status_code,
    )


@router.get("/health/live")
async def liveness():
    """Lightweight liveness probe — just confirms the process is running."""
    return {"status": "alive"}
