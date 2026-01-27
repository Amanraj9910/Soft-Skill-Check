"""
Scoring Engine.
Analyzes user responses using Azure OpenAI (GPT-4o) against the assessment rubric.
"""
from openai import AzureOpenAI
from app.config import settings
from .models import AIAnalysisResult, AssessmentStepScore
import json
import httpx

# Import logging
from app.core.logging import ai_logger, error_logger

class ScoringEngine:
    def __init__(self):
        # Create explicit client to avoid potential environment/transport issues
        self.http_client = httpx.Client(timeout=60.0)
        
        self.client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            http_client=self.http_client
        )
        self.deployment_name = settings.AZURE_OPENAI_DEPLOYMENT_NAME

    def analyze_response(
        self, 
        transcript: str, 
        question: str, 
        context: dict = None,
        previous_history: list = None
    ) -> AIAnalysisResult:
        """
        Analyzes the user's response transcript using GPT-4o.
        """
        if not transcript:
            return AIAnalysisResult(
                transcript="",
                scores=AssessmentStepScore(
                    fluency=0, pronunciation=0, grammar=0, confidence=0,
                    hesitation=0, storytelling=0, vision_clarity=0,
                    total_step_score=0, feedback="No audio detected.", improvement_tips=["Check microphone."]
                ),
                ai_response_text="I couldn't hear you. Could you please repeat that?"
            )

        system_prompt = """
        You are an expert English language assessor. Your job is to evaluate a spoken response based on the following strict rubric (Max 100 points):

        | Category | Max Score | Description |
        |----------|-----------|-------------|
        | Fluency | 20 | Speaking pace and flow. Deduct for long pauses. |
        | Pronunciation | 20 | Clarity and accuracy of sounds. |
        | Grammar | 10 | Sentence structure and correctness. |
        | Confidence | 20 | Tone assertiveness and steadiness. |
        | Hesitation | -10 | PENALTY. 0 if smooth, up to -10 for excessive fillers (um, ah). |
        | Storytelling | 20 | Narrative quality, structure (Beginning/Middle/End). |
        | Vision Clarity | 10 | (Assume 10 unless told otherwise). |
        
        Total Score = Sum of positive scores (100) + Hesitation Penalty.

        You must return a valid JSON object with the following structure:
        {
            "fluency": int (0-20),
            "pronunciation": int (0-20),
            "grammar": int (0-10),
            "confidence": int (0-20),
            "hesitation": int (negative -10 to 0),
            "storytelling": int (0-20),
            "vision_clarity": int (0-10),
            "feedback": "string (brief specific feedback)",
            "improvement_tips": ["tip1", "tip2"],
            "ai_response_text": "string (natural conversational reply to the user to keep the chat going)"
        }
        """

        user_content = f"""
        Question: {question}
        User Response Transcript: "{transcript}"
        Context: {context or {}}
        """

        try:
            ai_logger.info(f"Calling Azure OpenAI with model: {self.deployment_name}")
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )
        except Exception as api_err:
            import traceback
            error_details = traceback.format_exc()
            error_logger.error(f"Azure OpenAI Call Failed: {str(api_err)}\nTraceback:\n{error_details}")
            # Re-raise to be caught by the outer block
            raise api_err

        result_json = json.loads(response.choices[0].message.content)
        
        # Calculate total
        total = (
            result_json.get("fluency", 0) + 
            result_json.get("pronunciation", 0) + 
            result_json.get("grammar", 0) + 
            result_json.get("confidence", 0) + 
            result_json.get("hesitation", 0) + # This is negative
            result_json.get("storytelling", 0) + 
            result_json.get("vision_clarity", 10)
        )
        
        # Ensure boundaries
        total = max(0, min(100, total))

        scores = AssessmentStepScore(
            fluency=result_json.get("fluency", 0),
            pronunciation=result_json.get("pronunciation", 0),
            grammar=result_json.get("grammar", 0),
            confidence=result_json.get("confidence", 0),
            hesitation=result_json.get("hesitation", 0),
            storytelling=result_json.get("storytelling", 0),
            vision_clarity=result_json.get("vision_clarity", 10),
            total_step_score=total,
            feedback=result_json.get("feedback", ""),
            improvement_tips=result_json.get("improvement_tips", [])
        )

        return AIAnalysisResult(
            transcript=transcript,
            scores=scores,
            ai_response_text=result_json.get("ai_response_text", "Thank you.")
        )

# Singleton
scoring_engine = ScoringEngine()
