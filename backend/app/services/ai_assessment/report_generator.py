"""
Report Generator.
Aggregates scores from all steps and generates a final report using GPT-4o.
"""
from openai import AzureOpenAI
from app.config import settings
from .models import AssessmentStepScore
import json

# Import logging
from app.core.logging import ai_logger, error_logger

class ReportGenerator:
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        self.deployment_name = settings.AZURE_OPENAI_DEPLOYMENT_NAME

    def generate_report(self, scores_list: list[dict]) -> dict:
        """
        Generates a final comprehensive report based on all step scores.
        """
        if not scores_list:
            return {"error": "No data available for report"}

        # Calculate averages
        count = len(scores_list)
        avg_scores = {
            "fluency": sum(s.get("fluency", 0) for s in scores_list) / count,
            "pronunciation": sum(s.get("pronunciation", 0) for s in scores_list) / count,
            "grammar": sum(s.get("grammar", 0) for s in scores_list) / count,
            "confidence": sum(s.get("confidence", 0) for s in scores_list) / count,
            "hesitation": sum(s.get("hesitation", 0) for s in scores_list) / count,
            "storytelling": sum(s.get("storytelling", 0) for s in scores_list) / count,
            "vision_clarity": sum(s.get("vision_clarity", 0) for s in scores_list) / count,
            "total_score": sum(s.get("total_step_score", 0) for s in scores_list) / count
        }

        # Generate qualitative feedback with GPT-4o
        system_prompt = """
        You are an expert report writer. Analyze the following English assessment scores and provide a comprehensive report in JSON format.
        
        Return JSON with:
        {
            "summary": "Overall perfromance summary string",
            "strengths": ["list of strings"],
            "weaknesses": ["list of strings"],
            "recommendations": ["list of strings"]
        }
        """
        user_content = json.dumps(avg_scores)

        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze these scores: {user_content}"}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            feedback_json = json.loads(response.choices[0].message.content)
            
            return {
                "metrics": avg_scores,
                "summary": feedback_json.get("summary", ""),
                "strengths": feedback_json.get("strengths", []),
                "weaknesses": feedback_json.get("weaknesses", []),
                "recommendations": feedback_json.get("recommendations", []),
                "detailed_history": scores_list
            }
        except Exception as e:
            error_logger.error(f"Report generation failed: {str(e)}")
            return {
                "metrics": avg_scores,
                "summary": "Generated report unavailable.",
                "strengths": [],
                "weaknesses": [],
                "recommendations": [],
                "detailed_history": scores_list
            }

# Singleton
report_generator = ReportGenerator()
