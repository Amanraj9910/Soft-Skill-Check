# Assessment Fix Implementation Plan

## Overview
This document outlines the step-by-step implementation plan to fix the critical issues identified in the assessment system.

## Phase 1: Immediate Critical Fixes (Day 1)

### 1.1 Fix ASSESSMENT_COMPLETED Event Logging
**Files to modify**: `backend/app/api/v1/endpoints/assessments.py`

```python
# Add completion event logging in assessment completion endpoint
@router.post("/assessments/{assessment_id}/complete")
async def complete_assessment_endpoint(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        # Process completion
        assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")
        
        # Calculate final score
        final_score = calculate_final_assessment_score(assessment_id, db)
        
        # Mark as completed
        assessment.status = "completed"
        assessment.completed_at = datetime.utcnow()
        assessment.final_score = final_score
        
        db.commit()
        
        # CRITICAL: Log completion event
        logger.info("ASSESSMENT_COMPLETED", extra={
            "event_type": "ASSESSMENT_COMPLETED",
            "assessment_id": assessment_id,
            "student_name": assessment.student_name,
            "final_score": final_score,
            "total_time_seconds": (datetime.utcnow() - assessment.created_at).total_seconds(),
            "completion_timestamp": datetime.utcnow().isoformat()
        })
        
        return {"status": "completed", "final_score": final_score}
    except Exception as e:
        logger.error(f"Assessment completion failed: {str(e)}", extra={
            "event_type": "ASSESSMENT_COMPLETION_ERROR",
            "assessment_id": assessment_id,
            "error": str(e)
        })
        raise
```

### 1.2 Fix Profile Validation Before Assessment Creation
**Files to modify**: `backend/app/api/v1/endpoints/assessments.py`

```python
# Update assessment creation to validate profile exists
@router.post("/assessments")
async def create_assessment_endpoint(
    assessment_request: AssessmentCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # CRITICAL: Validate profile exists and has name before creating assessment
    profile = db.query(Profile).filter(Profile.user_id == current_user["id"]).first()
    if not profile or not profile.name or profile.name.strip() == "":
        logger.error("Attempt to create assessment with incomplete profile", extra={
            "event_type": "PROFILE_VALIDATION_ERROR",
            "user_id": current_user["id"],
            "profile_exists": bool(profile),
            "profile_name": getattr(profile, 'name', None)
        })
        raise HTTPException(
            status_code=400, 
            detail="User profile must be complete before starting assessment"
        )
    
    # Create assessment with validated profile data
    assessment = Assessment(
        id=generate_unique_id(),
        student_name=profile.name,  # Now guaranteed to be valid
        user_id=current_user["id"],
        status="in_progress",
        current_stage="greeting",
        created_at=datetime.utcnow(),
        last_heartbeat_at=datetime.utcnow(),  # Proper heartbeat initialization
        started_at=datetime.utcnow()
    )
    
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    
    logger.info("ASSESSMENT_CREATED", extra={
        "event_type": "ASSESSMENT_CREATED",
        "assessment_id": assessment.id,
        "student_name": assessment.student_name,
        "user_id": current_user["id"]
    })
    
    return assessment
```

### 1.3 Update Environment Configuration
**Files to modify**: `.env.backend` (template update)

```bash
# Production environment settings
ENVIRONMENT=production
DEBUG_MODE=false
LOG_LEVEL=INFO
WORKERS=4
TIMEOUT=300
GRACEFUL_TIMEOUT=30
KEEP_ALIVE=5

# Audio processing timeouts
AUDIO_PROCESSING_TIMEOUT=30
AZURE_SPEECH_TIMEOUT=25
TTS_TIMEOUT=25

# Database settings
DATABASE_POOL_SIZE=20
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600

# CORS for production
ALLOWED_ORIGINS=https://your-production-frontend.com
```

## Phase 2: Performance Improvements (Day 2-3)

### 2.1 Implement Async Audio Processing
**Files to modify**: `backend/app/api/v1/endpoints/responses.py`

```python
import asyncio
from contextlib import asynccontextmanager

@router.post("/responses/{response_id}/audio")
async def upload_audio_for_response(
    response_id: str,
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Start processing immediately but respond quickly to client
    response = db.query(Response).filter(Response.id == response_id).first()
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    
    # Send immediate acknowledgment to client
    asyncio.create_task(process_audio_async(response_id, audio_file))
    
    return {
        "status": "processing_started", 
        "response_id": response_id,
        "message": "Audio processing initiated, please wait..."
    }

async def process_audio_async(response_id: str, audio_file: UploadFile):
    """Background task to process audio with timeout protection"""
    try:
        # Set timeout for the entire processing
        with timeout(30):  # 30 seconds max
            # Read and validate audio file
            audio_data = await audio_file.read()
            if len(audio_data) == 0:
                raise ValueError("Empty audio file received")
            
            # Upload to Azure blob storage
            blob_url = await upload_audio_to_blob(audio_data, response_id)
            
            # Perform speech recognition
            transcription = await recognize_speech_from_audio(blob_url)
            
            # Generate AI response
            ai_response = await generate_ai_response(transcription)
            
            # Update response with results
            await update_response_with_results(response_id, transcription, ai_response)
            
            logger.info("AUDIO_PROCESSING_COMPLETE", extra={
                "event_type": "AUDIO_PROCESSING_COMPLETE",
                "response_id": response_id,
                "transcription_length": len(transcription),
                "processing_time_seconds": time.time() - start_time
            })
            
    except asyncio.TimeoutError:
        logger.error("Audio processing timed out", extra={
            "event_type": "AUDIO_PROCESSING_TIMEOUT",
            "response_id": response_id,
            "timeout_limit": 30
        })
        await mark_response_as_failed(response_id, "processing_timeout")
    except Exception as e:
        logger.error(f"Audio processing failed: {str(e)}", extra={
            "event_type": "AUDIO_PROCESSING_ERROR",
            "response_id": response_id,
            "error": str(e)
        })
        await mark_response_as_failed(response_id, str(e))
```

### 2.2 Optimize Database Queries
**Files to modify**: `backend/app/database/session.py`

```python
from sqlalchemy.pool import QueuePool
import time

# Enhanced database session with optimized pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,   # Recycle connections every hour
    echo=False           # Disable SQL logging in production
)

# Add query timing middleware
class QueryTimingMiddleware:
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        start_time = time.time()
        await self.app(scope, receive, send)
        duration = time.time() - start_time
        
        if duration > 0.5:  # Log slow queries (>500ms)
            logger.warning(f"Slow query detected: {duration:.2f}s", extra={
                "event_type": "SLOW_QUERY",
                "duration_seconds": duration
            })

# Apply middleware to FastAPI app
app.middleware("http")(QueryTimingMiddleware)
```

## Phase 3: Infrastructure Improvements (Day 4-5)

### 3.1 Single Worker Stale Checker
**Files to modify**: `backend/app/tasks/stale_checker.py`

```python
import os
import time
from threading import Thread
from datetime import datetime, timedelta
import logging

class SingletonStaleChecker:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            # Only run in master worker (PID == main process)
            self.is_master_worker = os.getppid() == 1 or os.environ.get('GUNICORN_PID') == '1'
            self.running = False
            self._initialized = True
    
    def start_checker(self):
        if not self.is_master_worker:
            logging.info("Stale checker disabled - not master worker")
            return
        
        if not self.running:
            self.running = True
            thread = Thread(target=self._run_stale_check_loop, daemon=True)
            thread.start()
            logging.info("Stale checker started in master worker")
    
    def _run_stale_check_loop(self):
        while self.running:
            try:
                self.check_stale_assessments()
                time.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logging.error(f"Stale checker error: {e}")
    
    def check_stale_assessments(self):
        """Check for and abandon stale assessments"""
        from app.database.session import get_db
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=30)  # 30 min timeout
        
        db = next(get_db())
        try:
            stale_assessments = db.query(Assessment).filter(
                Assessment.status != "completed",
                Assessment.last_heartbeat_at < cutoff_time
            ).all()
            
            for assessment in stale_assessments:
                assessment.status = "abandoned"
                assessment.abandoned_reason = "no_heartbeat_timeout"
                assessment.abandoned_at = datetime.utcnow()
                
                logger.info("ASSESSMENT_ABANDONED", extra={
                    "event_type": "ASSESSMENT_ABANDONED",
                    "assessment_id": assessment.id,
                    "student_name": assessment.student_name,
                    "reason": "no_heartbeat_timeout",
                    "last_activity": assessment.last_heartbeat_at.isoformat()
                })
            
            db.commit()
        finally:
            db.close()

# Initialize and start the singleton checker
stale_checker = SingletonStaleChecker()
stale_checker.start_checker()
```

### 3.2 Graceful Shutdown with Session Recovery
**Files to modify**: `backend/app/main.py`

```python
import asyncio
import signal
from contextlib import asynccontextmanager
from app.tasks.stale_checker import stale_checker

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Application starting up...")
    
    # Start singleton stale checker
    stale_checker.start_checker()
    
    yield
    
    # Shutdown
    logger.info("Application shutting down gracefully...")
    
    # Stop stale checker
    stale_checker.running = False
    
    # Save active assessment states
    await save_active_sessions_before_shutdown()
    
    # Allow time for cleanup
    await asyncio.sleep(5)
    
    logger.info("Application shutdown complete")

app = FastAPI(
    title="AI English Assessment Backend",
    version="1.0.0",
    lifespan=lifespan
)

async def save_active_sessions_before_shutdown():
    """Save active assessment states before shutdown"""
    from app.database.session import get_db
    
    db = next(get_db())
    try:
        active_assessments = db.query(Assessment).filter(
            Assessment.status.in_(["in_progress", "pending"])
        ).all()
        
        for assessment in active_assessments:
            # Save recovery state
            recovery_state = AssessmentRecoveryState(
                assessment_id=assessment.id,
                current_stage=assessment.current_stage,
                user_data=assessment.user_data,  # Store current progress
                saved_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=24)  # 24h recovery window
            )
            db.add(recovery_state)
            
            logger.info("SESSION_SAVED_FOR_RECOVERY", extra={
                "event_type": "SESSION_SAVED_FOR_RECOVERY",
                "assessment_id": assessment.id,
                "current_stage": assessment.current_stage
            })
        
        db.commit()
        logger.info(f"Saved {len(active_assessments)} active sessions for recovery")
    except Exception as e:
        logger.error(f"Failed to save active sessions: {e}")
    finally:
        db.close()

# Heartbeat endpoint to maintain session activity
@app.post("/assessments/{assessment_id}/heartbeat")
async def update_heartbeat(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if assessment:
        assessment.last_heartbeat_at = datetime.utcnow()
        db.commit()
    
    return {"status": "alive", "timestamp": datetime.utcnow()}
```

## Phase 4: Monitoring and Testing

### 4.1 Add Comprehensive Logging
**Files to modify**: `backend/app/core/logging_config.py`

```python
import logging
from pythonjsonlogger import jsonlogger
import sys

def setup_logging():
    # Configure structured logging
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # JSON formatter for structured logs
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S.%fZ'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Suppress overly verbose libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    return logger

logger = setup_logging()
```

### 4.2 Create Health Check Endpoints
**Files to modify**: `backend/app/api/v1/endpoints/health.py`

```python
from fastapi import APIRouter
from datetime import datetime
import time

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": "tracking...",
        "version": "1.0.0"
    }

@router.get("/metrics")
async def get_metrics():
    """Get current system metrics"""
    from app.database.session import get_db
    
    db = next(get_db())
    try:
        # Get assessment statistics
        total_assessments = db.query(Assessment).count()
        active_assessments = db.query(Assessment).filter(
            Assessment.status == "in_progress"
        ).count()
        completed_assessments = db.query(Assessment).filter(
            Assessment.status == "completed"
        ).count()
        
        return {
            "total_assessments": total_assessments,
            "active_assessments": active_assessments,
            "completed_assessments": completed_assessments,
            "completion_rate": completed_assessments / max(total_assessments, 1) * 100,
            "timestamp": datetime.utcnow().isoformat()
        }
    finally:
        db.close()
```

## Deployment Checklist

### Pre-deployment
- [ ] Test all changes in staging environment
- [ ] Verify ASSESSMENT_COMPLETED events are firing
- [ ] Confirm no "Unknown" student names in new assessments
- [ ] Validate audio processing time reduction
- [ ] Check single worker stale checker is running
- [ ] Verify graceful shutdown procedures

### During deployment
- [ ] Deploy with blue-green deployment strategy
- [ ] Monitor during deployment for any issues
- [ ] Verify new environment variables are applied
- [ ] Check that production mode is active

### Post-deployment
- [ ] Monitor completion rates for improvement
- [ ] Track audio processing performance
- [ ] Verify no duplicate log entries
- [ ] Confirm session recovery works
- [ ] Set up alerts for key metrics

This implementation plan addresses all critical issues identified in the analysis and should significantly improve the assessment completion rate and user experience.