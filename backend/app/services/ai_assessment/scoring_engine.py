"""
Scoring Engine.
Analyzes user responses using Azure OpenAI (GPT-4o) against the assessment rubric.
"""
from openai import AzureOpenAI
from app.config import settings
from .models import AIAnalysisResult, AssessmentStepScore
import json

class ScoringEngine:
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
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
        | Pronunciation | 10 | Clarity and accuracy of sounds. |
        | Grammar | 10 | Sentence structure and correctness. |
        | Confidence | 20 | Tone assertiveness and steadiness. |
        | Hesitation | -10 | PENALTY. 0 if smooth, up to -10 for excessive fillers (um, ah). |
        | Storytelling | 20 | Narrative quality, structure (Beginning/Middle/End). |
        | Vision Clarity | 10 | (Assume 10 unless told otherwise). |
        
        Total Score = Sum of all above (Max 100).

        You must return a valid JSON object with the following structure:
        {
            "fluency": int,
            "pronunciation": int,
            "grammar": int,
            "confidence": int,
            "hesitation": int (negative or zero),
            "storytelling": int,
            "vision_clarity": int,
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

        # No try/except block - let exceptions propagate so they can be seen in main logs
        # or caught by the router with 500 details.
        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )

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
