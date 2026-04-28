"""
Supabase client service for database operations and authentication.
"""
import asyncio
import time
from datetime import datetime
from typing import Optional, Dict, Any
from supabase import create_client, Client, ClientOptions
from app.config import settings
import httpx

# Import logging
from app.core.logging import db_logger, error_logger
from app.core import log_messages


class SupabaseService:
    """Service for interacting with Supabase database and auth."""
    
    def __init__(self):
        """Initialize Supabase client with optimized connection pool."""
        self.url = settings.SUPABASE_URL
        self.anon_key = settings.SUPABASE_ANON_KEY
        self.service_key = settings.SUPABASE_SERVICE_ROLE_KEY
        
        # Configure HTTP connection pool for 100+ concurrent users
        # With 4 Gunicorn workers, limit each client (user + admin) to 20 connections = 40 per worker, 160 total
        # (Supabase Free tier: 200 max connections, leaves buffer for overhead)
        http_limits = httpx.Limits(
            max_connections=20,
            max_keepalive_connections=10,
            keepalive_expiry=30.0
        )
        
        # Build pre-configured httpx clients with pooling limits
        user_httpx = httpx.Client(limits=http_limits)
        admin_httpx = httpx.Client(limits=http_limits)
        
        # Client for authenticated requests (uses user JWT)
        self.client: Client = create_client(
            self.url, 
            self.anon_key,
            options=ClientOptions(httpx_client=user_httpx)
        )
        
        # Admin client for backend operations (bypasses RLS)
        self.admin_client: Client = create_client(
            self.url, 
            self.service_key,
            options=ClientOptions(httpx_client=admin_httpx)
        )
        
        db_logger.info("🗄️ Supabase service initialized with connection pool (max: 20 per client)")
    
    def _execute_with_retry(self, operation_func):
        """
        Execute a synchronous Supabase operation with retries.
        
        Args:
            operation_func: Lambda/function to execute
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return operation_func()
            except Exception as e:
                error_msg = str(e)
                # Retry on network-related errors
                # "Server disconnected" is typical for httpx remote closure
                if attempt < max_retries - 1 and any(x in error_msg for x in ["Server disconnected", "RemoteProtocolError", "Connection pool"]):
                    wait_time = 0.2 * (2 ** attempt)
                    db_logger.warning(f"🗄️ ⚠️ Supabase retry {attempt+1}/{max_retries} in {wait_time:.1f}s: {error_msg}")
                    time.sleep(wait_time)
                    continue
                raise e
    
    def get_client(self, use_admin: bool = False) -> Client:
        """
        Get Supabase client.
        
        Args:
            use_admin: If True, returns service role client (bypasses RLS)
        
        Returns:
            Supabase client instance
        """
        return self.admin_client if use_admin else self.client
    
    async def verify_user(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify user JWT token.
        
        Args:
            token: JWT token from Authorization header
        
        Returns:
            User data if valid, None otherwise
        """
        start_time = time.time()
        try:
            db_logger.debug("🔐 Verifying user token...")
            user = await asyncio.to_thread(
                lambda: self._execute_with_retry(lambda: self.client.auth.get_user(token))
            )
            duration = (time.time() - start_time) * 1000
            db_logger.info(f"🗄️ User verified in {duration:.0f}ms")
            return user.dict() if user else None
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            error_logger.error(f"❌ Token verification failed in {duration:.0f}ms: {str(e)}")
            return None
    
    async def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile by ID.
        
        Args:
            user_id: User UUID
        
        Returns:
            Profile data or None
        """
        start_time = time.time()
        try:
            db_logger.debug(f"📋 Fetching profile for user: {user_id[:8]}...")
            response = await asyncio.to_thread(
                lambda: self._execute_with_retry(lambda: self.admin_client.table("profiles").select("*").eq("id", user_id).execute())
            )
            duration = (time.time() - start_time) * 1000
            db_logger.info(f"🗄️ Profile fetched in {duration:.0f}ms (found: {len(response.data) > 0})")
            return response.data[0] if response.data else None
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            error_logger.error(f"❌ Profile fetch failed in {duration:.0f}ms: {str(e)}")
            error_logger.error(log_messages.db_connection_error(str(e)))
            return None

    async def create_profile(self, user_id: str, profile_data: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Create a new user profile.
        
        Args:
            user_id: User UUID
            profile_data: Optional initial profile data
            
        Returns:
            Created profile data
        """
        start_time = time.time()
        try:
            db_logger.info(f"➕ Creating profile for user: {user_id[:8]}...")
            data = {"id": user_id, **(profile_data or {})}
            response = await asyncio.to_thread(
                lambda: self.admin_client.table("profiles").insert(data).execute()
            )
            duration = (time.time() - start_time) * 1000
            db_logger.info(f"🗄️ Profile created in {duration:.0f}ms")
            return response.data[0] if response.data else None
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            error_logger.error(f"❌ Profile creation failed in {duration:.0f}ms: {str(e)}")
            return None
    
    async def create_assessment(self, user_id: str, metadata: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """
        Create a new assessment.
        
        Args:
            user_id: User UUID
            metadata: Optional metadata (user_agent, ip_address)
        
        Returns:
            Created assessment data
        """
        start_time = time.time()
        try:
            db_logger.info(f"🚀 Creating assessment for user: {user_id[:8]}...")
            data = {
                "user_id": user_id,
                "status": "in_progress",
                **(metadata or {})
            }
            response = await asyncio.to_thread(
                lambda: self.admin_client.table("assessments").insert(data).execute()
            )
            duration = (time.time() - start_time) * 1000
            if response.data:
                assessment_id = response.data[0].get("id", "unknown")
                db_logger.info(f"🗄️ Assessment {assessment_id[:8]} created in {duration:.0f}ms")
            return response.data[0] if response.data else None
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            error_logger.error(f"❌ Assessment creation failed in {duration:.0f}ms: {str(e)}")
            return None
    
    async def get_assessment(self, assessment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get assessment by ID.
        
        Args:
            assessment_id: Assessment UUID
        
        Returns:
            Assessment data or None
        """
        start_time = time.time()
        try:
            db_logger.debug(f"📋 Fetching assessment: {assessment_id[:8]}...")
            response = await asyncio.to_thread(
                lambda: self._execute_with_retry(lambda: self.admin_client.table("assessments").select("*").eq("id", assessment_id).execute())
            )
            duration = (time.time() - start_time) * 1000
            db_logger.info(f"🗄️ Assessment fetched in {duration:.0f}ms (found: {len(response.data) > 0})")
            return response.data[0] if response.data else None
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            error_logger.error(f"❌ Assessment fetch failed in {duration:.0f}ms: {str(e)}")
            return None
    
    async def update_assessment(self, assessment_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update assessment.
        
        Args:
            assessment_id: Assessment UUID
            updates: Fields to update
        
        Returns:
            Updated assessment data
        """
        start_time = time.time()
        try:
            db_logger.info(f"📝 Updating assessment: {assessment_id[:8]}... (fields: {list(updates.keys())})")
            response = await asyncio.to_thread(
                lambda: self._execute_with_retry(lambda: self.admin_client.table("assessments").update(updates).eq("id", assessment_id).execute())
            )
            duration = (time.time() - start_time) * 1000
            db_logger.info(f"🗄️ Assessment updated in {duration:.0f}ms")
            return response.data[0] if response.data else None
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            error_logger.error(f"❌ Assessment update failed in {duration:.0f}ms: {str(e)}")
            return None

    async def delete_assessment(self, assessment_id: str) -> bool:
        """
        Delete assessment and all related DB data.
        
        Args:
            assessment_id: Assessment UUID
        
        Returns:
            True if success, False otherwise
        """
        start_time = time.time()
        try:
            db_logger.info(f"🗑️ Deleting assessment: {assessment_id[:8]}...")
            
            # Delete from assessments table (relies on CASCADE for child tables like responses/scores)
            await asyncio.to_thread(
                lambda: self._execute_with_retry(lambda: self.admin_client.table("assessments").delete().eq("id", assessment_id).execute())
            )
            
            duration = (time.time() - start_time) * 1000
            db_logger.info(f"🗄️ Assessment deleted in {duration:.0f}ms")
            return True
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            error_logger.error(f"❌ Assessment deletion failed in {duration:.0f}ms: {str(e)}")
            return False
    
    async def create_response(self, response_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create assessment response.
        
        Args:
            response_data: Response data including assessment_id, section, transcript, etc.
        
        Returns:
            Created response data
        """
        start_time = time.time()
        section = response_data.get("section", "unknown")
        assessment_id = response_data.get("assessment_id", "unknown")[:8]
        try:
            db_logger.info(f"💬 Creating response for assessment {assessment_id}, section: {section}...")
            
            # Check if response already exists for this assessment and section
            existing = await asyncio.to_thread(
                lambda: self.admin_client.table("assessment_responses")
                .select("*")
                .eq("assessment_id", response_data["assessment_id"])
                .eq("section", section)
                .execute()
            )
            
            if existing.data:
                db_logger.info(f"🗄️ Found existing response for {section}, returning it")
                return existing.data[0]

            response = await asyncio.to_thread(
                lambda: self.admin_client.table("assessment_responses").insert(response_data).execute()
            )
            duration = (time.time() - start_time) * 1000
            db_logger.info(f"🗄️ Response created in {duration:.0f}ms (section: {section})")
            return response.data[0] if response.data else None
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            error_logger.error(f"❌ Response creation/fetch failed in {duration:.0f}ms: {str(e)}")
            return None
    
    async def save_scores(self, scores_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Save assessment scores.
        
        Args:
            scores_data: Scores data including assessment_id and all category scores
        
        Returns:
            Created scores data
        """
        start_time = time.time()
        assessment_id = scores_data.get("assessment_id", "unknown")[:8]
        total_score = scores_data.get("total_score", 0)
        try:
            db_logger.info(f"📊 Saving scores for assessment {assessment_id} (total: {total_score})...")
            response = await asyncio.to_thread(
                lambda: self.admin_client.table("assessment_scores").upsert(
                    scores_data, on_conflict="assessment_id"
                ).execute()
            )
            duration = (time.time() - start_time) * 1000
            db_logger.info(f"🗄️ Scores saved in {duration:.0f}ms")
            return response.data[0] if response.data else None
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            error_logger.error(f"❌ Scores save failed in {duration:.0f}ms: {str(e)}")
            return None
    
    async def save_audio_features(self, features_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Save audio features.
        
        Args:
            features_data: Audio features data
        
        Returns:
            Created features data
        """
        start_time = time.time()
        response_id = features_data.get("response_id", "unknown")[:8]
        try:
            db_logger.info(f"🎵 Saving audio features for response {response_id}...")
            response = await asyncio.to_thread(
                lambda: self.admin_client.table("audio_features").insert(features_data).execute()
            )
            duration = (time.time() - start_time) * 1000
            db_logger.info(f"🗄️ Audio features saved in {duration:.0f}ms")
            return response.data[0] if response.data else None
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            error_logger.error(f"❌ Audio features save failed in {duration:.0f}ms: {str(e)}")
            return None
    
    async def save_vision_metrics(self, metrics_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Save vision metrics.
        
        Args:
            metrics_data: Vision metrics data
        
        Returns:
            Created metrics data
        """
        start_time = time.time()
        response_id = metrics_data.get("response_id", "unknown")[:8]
        try:
            db_logger.info(f"👁️ Saving vision metrics for response {response_id}...")
            
            # Validate and normalize score fields to 0-10 range
            score_fields = [
                "eye_contact_score", "gaze_stability", "head_stability_score",
                "facial_confidence_score", "overall_clarity_score"
            ]
            for field in score_fields:
                if field in metrics_data and metrics_data[field] is not None:
                    value = float(metrics_data[field])
                    # If value seems to be on 0-100 scale, normalize to 0-10
                    if value > 10:
                        value = value / 10.0
                    # Clamp to 0-10 range
                    metrics_data[field] = max(0.0, min(10.0, value))
            
            response = await asyncio.to_thread(
                lambda: self.admin_client.table("vision_metrics").insert(metrics_data).execute()
            )
            duration = (time.time() - start_time) * 1000
            db_logger.info(f"🗄️ Vision metrics saved in {duration:.0f}ms")
            return response.data[0] if response.data else None
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            error_logger.error(f"❌ Vision metrics save failed in {duration:.0f}ms: {str(e)}")
            return None
    
    async def list_assessments(self, user_id: str, limit: int = 10, offset: int = 0) -> tuple:
        """
        List user's assessments with pagination.
        
        Args:
            user_id: User UUID
            limit: Max results to return
            offset: Pagination offset
        
        Returns:
            Tuple of (assessments list, total count)
        """
        start_time = time.time()
        try:
            db_logger.info(f"📋 Listing assessments for user: {user_id[:8]}... (limit: {limit}, offset: {offset})")
            
            # Run both queries concurrently using asyncio.gather
            response, count_response = await asyncio.gather(
                asyncio.to_thread(
                    lambda: self._execute_with_retry(lambda: self.admin_client.table("assessments")
                        .select("*")
                        .eq("user_id", user_id)
                        .order("created_at", desc=True)
                        .range(offset, offset + limit - 1)
                        .execute())
                ),
                asyncio.to_thread(
                    lambda: self._execute_with_retry(lambda: self.admin_client.table("assessments")
                        .select("id", count="exact")
                        .eq("user_id", user_id)
                        .execute())
                )
            )
            
            duration = (time.time() - start_time) * 1000
            total = count_response.count if hasattr(count_response, 'count') else len(response.data)
            db_logger.info(f"🗄️ Listed {len(response.data)} assessments (total: {total}) in {duration:.0f}ms")
            
            return response.data, total
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            error_logger.error(f"❌ List assessments failed in {duration:.0f}ms: {str(e)}")
            return [], 0
            


    async def get_student_identity(self, user_id: str) -> Dict[str, str]:
        """
        Lightweight fetch of student name and email for logging purposes.
        
        Returns:
            Dict with 'name' and 'email' keys, defaults if not found.
        """
        try:
            response = await asyncio.to_thread(
                lambda: self._execute_with_retry(
                    lambda: self.admin_client.table("profiles")
                    .select("full_name, email")
                    .eq("id", user_id)
                    .limit(1)
                    .execute()
                )
            )
            if response.data:
                row = response.data[0]
                return {
                    "name": row.get("full_name") or "Unknown",
                    "email": row.get("email") or "",
                }
        except Exception:
            pass
        return {"name": "Unknown", "email": ""}

    async def ping(self) -> bool:
        """Lightweight connectivity check — single row query."""
        await asyncio.to_thread(
            lambda: self.admin_client.table("profiles").select("id").limit(1).execute()
        )
        return True


# Create singleton instance
supabase_service = SupabaseService()


def get_supabase_service() -> SupabaseService:
    """Dependency for accessing Supabase service."""
    return supabase_service
