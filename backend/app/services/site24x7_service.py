"""
Site24x7 monitoring service integration.
Provides health status reporting and optional APM integration.
"""
import asyncio
import httpx
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.config import settings
from app.core.logging import api_logger

# Site24x7 APM Insight Python integration (optional)
# To use: pip install apminsight
# Then set SITE24X7_LICENSE_KEY in your environment
try:
    import apminsight
    apminsight.configure()
    APM_AVAILABLE = True
except ImportError:
    APM_AVAILABLE = False

class Site24x7Service:
    """Service for Site24x7 monitoring integration."""
    
    def __init__(self):
        self.api_key = settings.SITE24X7_API_KEY
        self.enabled = settings.SITE24X7_ENABLED and bool(self.api_key)
        self.base_url = "https://www.site24x7.com/api"
        
        if self.enabled:
            api_logger.info("📊 Site24x7 monitoring enabled")
        else:
            api_logger.debug("📊 Site24x7 monitoring disabled (no API key or disabled)")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status for monitoring.
        
        Returns:
            Dictionary with system health information
        """
        status = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "1.0.0",
            "environment": settings.APP_ENV,
            "checks": {}
        }
        
        # Check database connectivity
        db_status = await self._check_database()
        status["checks"]["database"] = db_status
        
        # Check Azure services (basic connectivity)
        azure_status = await self._check_azure_services()
        status["checks"]["azure"] = azure_status
        
        # Determine overall status
        if not all(check.get("status") == "healthy" for check in status["checks"].values()):
            status["status"] = "degraded"
        
        return status
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check Supabase database connectivity."""
        try:
            from app.services.supabase_client import supabase_service
            
            start = datetime.now()
            # Simple query to verify connectivity
            client = supabase_service.get_client(use_admin=True)
            result = await asyncio.to_thread(
                lambda: client.table("profiles").select("id").limit(1).execute()
            )
            latency_ms = (datetime.now() - start).total_seconds() * 1000
            
            return {
                "status": "healthy",
                "latency_ms": round(latency_ms, 2),
                "message": "Connected"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "latency_ms": None,
                "message": str(e)[:100]
            }
    
    async def _check_azure_services(self) -> Dict[str, Any]:
        """Check Azure OpenAI endpoint availability."""
        try:
            if not settings.AZURE_OPENAI_ENDPOINT:
                return {
                    "status": "unconfigured",
                    "message": "Azure OpenAI not configured"
                }
            
            start = datetime.now()
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Just check if endpoint is reachable
                response = await client.get(
                    settings.AZURE_OPENAI_ENDPOINT,
                    follow_redirects=True
                )
            latency_ms = (datetime.now() - start).total_seconds() * 1000
            
            # Any response means endpoint is reachable (401/403 is expected without auth)
            return {
                "status": "healthy",
                "latency_ms": round(latency_ms, 2),
                "message": "Endpoint reachable"
            }
        except httpx.TimeoutException:
            return {
                "status": "degraded",
                "latency_ms": None,
                "message": "Timeout checking Azure endpoint"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "latency_ms": None,
                "message": str(e)[:100]
            }
    
    async def report_incident(self, title: str, description: str, severity: str = "medium") -> bool:
        """
        Report an incident to Site24x7 (optional integration).
        
        Args:
            title: Incident title
            description: Incident description  
            severity: low, medium, high, critical
            
        Returns:
            True if reported successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/short/alert",
                    headers={
                        "Authorization": f"Zoho-oauthtoken {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "monitor_name": settings.APP_NAME,
                        "subject": title,
                        "message": description,
                        "status": severity.upper()
                    },
                    timeout=10.0
                )
                return response.status_code in (200, 201)
        except Exception as e:
            api_logger.error(f"Failed to report incident to Site24x7: {e}")
            return False


# Singleton instance
site24x7_service = Site24x7Service()


def get_site24x7_service() -> Site24x7Service:
    """Dependency for accessing Site24x7 service."""
    return site24x7_service
