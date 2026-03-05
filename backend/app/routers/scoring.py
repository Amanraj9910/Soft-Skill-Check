"""
Scoring API endpoints for assessment evaluation.
"""
from fastapi import APIRouter, HTTPException, Depends
import asyncio
from typing import Dict, Any

from app.models.schemas import ScoresResponse, SuccessResponse
from app.services.azure_openai import AzureOpenAIService, get_azure_openai_service
from app.services.supabase_client import SupabaseService, get_supabase_service

router = APIRouter(prefix="/api/v1/scoring", tags=["Scoring"])


@router.post("/{assessment_id}/calculate", response_model=SuccessResponse)
async def calculate_scores(
    assessment_id: str,
    openai_service: AzureOpenAIService = Depends(get_azure_openai_service),
    db: SupabaseService = Depends(get_supabase_service)
):
    """
    Calculate scores for a completed assessment.
    
    Args:
        assessment_id: Assessment UUID
        openai_service: Azure OpenAI service
        db: Database service
    
    Returns:
        Success message
    """
    try:
        # Get assessment
        assessment = await db.get_assessment(assessment_id)
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")
        
        # Get all responses
        client = db.get_client(use_admin=True)
        responses_result = await asyncio.to_thread(
            lambda: client.table("assessment_responses")
            .select("*")
            .eq("assessment_id", assessment_id)
            .order("section_order")
            .execute()
        )
        responses = responses_result.data
        
        if not responses:
            raise HTTPException(status_code=400, detail="No responses found for this assessment")
        
        # Get audio features (aggregate from all responses)
        audio_features_result = await asyncio.to_thread(
            lambda: client.table("audio_features")
            .select("*")
            .in_("response_id", [r["id"] for r in responses])
            .execute()
        )
        audio_features_list = audio_features_result.data
        
        # Aggregate audio features
        aggregated_audio = _aggregate_audio_features(audio_features_list)
        
        # Get vision metrics (aggregate from all responses)
        vision_metrics_result = await asyncio.to_thread(
            lambda: client.table("vision_metrics")
            .select("*")
            .in_("response_id", [r["id"] for r in responses])
            .execute()
        )
        vision_metrics_list = vision_metrics_result.data
        
        # Aggregate vision metrics
        aggregated_vision = _aggregate_vision_metrics(vision_metrics_list)
        
        # Score using Azure OpenAI
        scoring_result = await openai_service.score_assessment(
            responses=responses,
            audio_features=aggregated_audio,
            vision_metrics=aggregated_vision
        )
        
        if not scoring_result["success"]:
            raise HTTPException(status_code=500, detail="Scoring failed")
        
        scores_data = scoring_result["scores"]
        scores_data["assessment_id"] = assessment_id
        
        # Save scores to database
        saved_scores = await db.save_scores(scores_data)
        
        if not saved_scores:
            raise HTTPException(status_code=500, detail="Failed to save scores")
        
        # Update assessment with grade
        await db.update_assessment(assessment_id, {
            "grade": scores_data.get("grade"),
            "total_score": scores_data.get("total_score")
        })
        
        return SuccessResponse(message="Scores calculated and saved successfully")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{assessment_id}", response_model=ScoresResponse)
async def get_scores(
    assessment_id: str,
    db: SupabaseService = Depends(get_supabase_service)
):
    """
    Get scores for an assessment.
    
    Args:
        assessment_id: Assessment UUID
        db: Database service
    
    Returns:
        Assessment scores
    """
    try:
        client = db.get_client(use_admin=True)
        result = await asyncio.to_thread(
            lambda: client.table("assessment_scores")
            .select("*")
            .eq("assessment_id", assessment_id)
            .execute()
        )
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Scores not found for this assessment")
        
        scores = result.data[0]
        
        # Get assessment for grade
        assessment = await db.get_assessment(assessment_id)
        scores["grade"] = assessment.get("grade", "intermediate")
        
        return ScoresResponse(**scores)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _aggregate_audio_features(features_list: list) -> Dict[str, Any]:
    """Aggregate audio features from multiple responses."""
    if not features_list:
        return {
            "pitch_stability": 0,
            "volume_variance": 0,
            "silence_ratio": 0,
            "average_pause_duration": 0
        }
    
    import numpy as np
    
    return {
        "pitch_stability": float(np.mean([f.get("pitch_stability_score", 0) for f in features_list])),
        "volume_variance": float(np.mean([f.get("volume_variance", 0) for f in features_list])),
        "silence_ratio": float(np.mean([f.get("silence_ratio", 0) for f in features_list])),
        "average_pause_duration": float(np.mean([f.get("average_pause_duration", 0) for f in features_list]))
    }


def _aggregate_vision_metrics(metrics_list: list) -> Dict[str, Any]:
    """Aggregate vision metrics from multiple responses."""
    if not metrics_list:
        return {
            "eye_contact_score": 0,
            "head_stability_score": 0,
            "overall_clarity_score": 0
        }
    
    import numpy as np
    
    return {
        "eye_contact_score": float(np.mean([m.get("eye_contact_score", 0) for m in metrics_list])),
        "head_stability_score": float(np.mean([m.get("head_stability_score", 0) for m in metrics_list])),
        "overall_clarity_score": float(np.mean([m.get("overall_clarity_score", 0) for m in metrics_list]))
    }
