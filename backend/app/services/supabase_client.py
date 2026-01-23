"""
Supabase client service for database operations and authentication.
"""
from typing import Optional, Dict, Any
from supabase import create_client, Client
from app.config import settings


class SupabaseService:
    """Service for interacting with Supabase database and auth."""
    
    def __init__(self):
        """Initialize Supabase client."""
        self.url = settings.SUPABASE_URL
        self.anon_key = settings.SUPABASE_ANON_KEY
        self.service_key = settings.SUPABASE_SERVICE_ROLE_KEY
        
        # Client for authenticated requests (uses user JWT)
        self.client: Client = create_client(self.url, self.anon_key)
        
        # Admin client for backend operations (bypasses RLS)
        self.admin_client: Client = create_client(self.url, self.service_key)
    
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
        try:
            user = self.client.auth.get_user(token)
            return user.dict() if user else None
        except Exception as e:
            print(f"Error verifying user: {e}")
            return None
    
    async def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile by ID.
        
        Args:
            user_id: User UUID
        
        Returns:
            Profile data or None
        """
        try:
            response = self.admin_client.table("profiles").select("*").eq("id", user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error getting profile: {e}")
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
        try:
            data = {
                "user_id": user_id,
                "status": "in_progress",
                **(metadata or {})
            }
            response = self.admin_client.table("assessments").insert(data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error creating assessment: {e}")
            return None
    
    async def get_assessment(self, assessment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get assessment by ID.
        
        Args:
            assessment_id: Assessment UUID
        
        Returns:
            Assessment data or None
        """
        try:
            response = self.admin_client.table("assessments").select("*").eq("id", assessment_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error getting assessment: {e}")
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
        try:
            response = self.admin_client.table("assessments").update(updates).eq("id", assessment_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error updating assessment: {e}")
            return None
    
    async def create_response(self, response_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create assessment response.
        
        Args:
            response_data: Response data including assessment_id, section, transcript, etc.
        
        Returns:
            Created response data
        """
        try:
            response = self.admin_client.table("assessment_responses").insert(response_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error creating response: {e}")
            return None
    
    async def save_scores(self, scores_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Save assessment scores.
        
        Args:
            scores_data: Scores data including assessment_id and all category scores
        
        Returns:
            Created scores data
        """
        try:
            response = self.admin_client.table("assessment_scores").insert(scores_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error saving scores: {e}")
            return None
    
    async def save_audio_features(self, features_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Save audio features.
        
        Args:
            features_data: Audio features data
        
        Returns:
            Created features data
        """
        try:
            response = self.admin_client.table("audio_features").insert(features_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error saving audio features: {e}")
            return None
    
    async def save_vision_metrics(self, metrics_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Save vision metrics.
        
        Args:
            metrics_data: Vision metrics data
        
        Returns:
            Created metrics data
        """
        try:
            response = self.admin_client.table("vision_metrics").insert(metrics_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error saving vision metrics: {e}")
            return None


# Create singleton instance
supabase_service = SupabaseService()


def get_supabase_service() -> SupabaseService:
    """Dependency for accessing Supabase service."""
    return supabase_service
