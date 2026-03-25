"""
Centralized JWT authentication using Supabase JWKS (public keys).

Supabase OAuth tokens (e.g. Google Sign-In) are signed with ES256.
We fetch the public keys from the JWKS endpoint and verify accordingly,
with a fallback to HS256 for tokens signed with the JWT secret.
"""
import httpx
from typing import Optional
from fastapi import Header, HTTPException
from jose import jwt, JWTError, ExpiredSignatureError

from app.config import settings
from app.core.logging import api_logger

# ---------------------------------------------------------------------------
# JWKS cache
# ---------------------------------------------------------------------------
_jwks_cache: dict | None = None


def _get_jwks_url() -> str:
    """Build the JWKS URL from the Supabase project URL."""
    base = settings.SUPABASE_URL.rstrip("/")
    return f"{base}/auth/v1/.well-known/jwks.json"


def _fetch_jwks() -> dict:
    """Fetch JWKS from Supabase (synchronous – called rarely)."""
    global _jwks_cache
    url = _get_jwks_url()
    try:
        api_logger.info(f"🔑 Fetching JWKS from {url}")
        resp = httpx.get(url, timeout=10)
        resp.raise_for_status()
        _jwks_cache = resp.json()
        api_logger.info(f"🔑 JWKS fetched: {len(_jwks_cache.get('keys', []))} key(s)")
        return _jwks_cache
    except Exception as e:
        api_logger.error(f"❌ Failed to fetch JWKS: {e}")
        if _jwks_cache:
            api_logger.warning("⚠️ Using previously cached JWKS")
            return _jwks_cache
        raise RuntimeError(f"Cannot fetch JWKS and no cache available: {e}")


def _get_jwks() -> dict:
    """Return cached JWKS or fetch if not yet cached."""
    if _jwks_cache is not None:
        return _jwks_cache
    return _fetch_jwks()


def _find_key(kid: str, jwks: dict) -> dict | None:
    """Find a key by 'kid' in the JWKS key set."""
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
    return None


# ---------------------------------------------------------------------------
# Main dependency
# ---------------------------------------------------------------------------
async def get_current_user_id(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract and verify user ID from the Authorization header.

    1. Try JWKS (ES256) verification — works for OAuth tokens.
    2. Fall back to HS256 with SUPABASE_JWT_SECRET — works for
       tokens issued directly by Supabase client-side auth.
    """
    if not authorization or not authorization.startswith("Bearer "):
        api_logger.error(f"Invalid auth header: {authorization}")
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header",
        )

    token = authorization.replace("Bearer ", "")

    # ---- Attempt 1: JWKS / ES256 ----
    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        alg = unverified_header.get("alg", "unknown")
        api_logger.info(f"🔐 Token alg={alg}, kid={kid}")

        if kid:
            jwks = _get_jwks()
            key = _find_key(kid, jwks)

            # If kid not found, maybe keys rotated – refetch once
            if key is None:
                api_logger.warning("⚠️ kid not in cache, refetching JWKS...")
                jwks = _fetch_jwks()
                key = _find_key(kid, jwks)

            if key is not None:
                payload = jwt.decode(
                    token,
                    key,
                    algorithms=["ES256"],
                    audience="authenticated",
                )
                user_id = payload.get("sub")
                if not user_id:
                    raise HTTPException(status_code=401, detail="Invalid token: no user ID")
                api_logger.info(f"🔐 JWKS/ES256 verified for user {user_id[:8]}...")
                return user_id

        # ---- Attempt 2: HS256 fallback ----
        api_logger.info("🔄 Falling back to HS256 verification")
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: no user ID")
        api_logger.info(f"🔐 HS256 verified for user {user_id[:8]}...")
        return user_id

    except ExpiredSignatureError:
        api_logger.error("Token expired")
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError as e:
        api_logger.error(f"JWT verification failed: {type(e).__name__} – {e}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Unexpected auth error: {type(e).__name__} – {e}")
        raise HTTPException(status_code=401, detail=f"Invalid authentication token: {e}")
