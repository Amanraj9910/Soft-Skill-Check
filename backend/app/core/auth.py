"""
Shared authentication dependency.
Verifies JWT signature using the Supabase JWT secret.
"""
from typing import Optional
from fastapi import Header, HTTPException
from jose import jwt, ExpiredSignatureError, JWTError
from app.config import settings


async def get_current_user_id(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract and verify user ID from authorization header.
    
    Verifies the JWT signature using the Supabase JWT secret,
    checks token expiry, and returns the `sub` (user ID) claim.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_exp": True},
        )
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: no user ID")
            
        return user_id
        
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid authentication token: {str(e)}")
