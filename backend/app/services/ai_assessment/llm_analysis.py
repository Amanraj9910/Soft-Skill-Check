import json
from openai import AsyncAzureOpenAI
from app.config import settings
from app.core.logging import ai_logger, error_logger
from typing import Dict, Any
import httpx

class LLMAnalysisService:
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=60.0)
        self.client = AsyncAzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            http_client=self.http_client
        )
        self.deployment_name = settings.AZURE_OPENAI_DEPLOYMENT_NAME

    async def analyze_responses(self, combined_transcript: str) -> Dict[str, Any]:
        """
        Analyzes the combined transcript using GPT-4o.
        Returns: grammar_score, storytelling_score, aim_clarity_score, textual_confidence.
        """
        if not combined_transcript or len(combined_transcript.strip()) < 10:
             return self._get_fallback_result("Insufficient text for analysis")

        prompt = """
        You are an expert English language assessor. Analyze the following transcript of a candidate's spoken responses.
        
        ### Scoring Guidelines & Rubrics
        
        **1. Grammar Score (0-10) - LENIENT / CONVERSATIONAL**
        - Judge based on natural spoken English, NOT formal written academic standards.
        - Ignore minor slips common in speech (e.g., "gonna", mild run-on sentences).
        - **Rubric:**
          - **9-10**: Grammatically accurate and natural.
          - **7-8**: Minor errors, mostly correct. Meaning is clear.
          - **5-6**: Noticeable errors but understandable.
          - **3-4**: Many errors, meaning sometimes unclear.
          - **0-2**: Frequent errors, hard to understand.

        **2. Storytelling Score (0-20)**
        - **Rubric:**
          - **17-20**: Well-structured, engaging, and coherent story.
          - **13-16**: Clear and mostly coherent narrative.
          - **9-12**: Basic structure, limited clarity.
          - **5-8**: Very weak structure, hard to follow.
          - **0-4**: No structure, disjointed ideas.

        **3. Aim & Vision Clarity Score (0-20)**
        - How clearly does the candidate express their goals/ideas?
        - **Rubric:**
          - **17-20**: Clear, planned, motivated.
          - **13-16**: Clear & realistic.
          - **9-12**: Basic clarity.
          - **5-8**: Vague, unclear.
          - **0-4**: No clear aim.

        **4. Textual Confidence (0-10)**
        - How confident the speaker sounds based on CHOICE OF WORDS (assertive vs tentative).
        - **Rubric:**
          - **9-10**: Uses "I can," "I will," "I am sure."
          - **5-8**: Uses "I think," "maybe," "I hope."
          - **0-4**: Uses "I guess," "I don't know," highly uncertain.

        Output MUST be a valid JSON object with this structure:
        {
            "grammar_score": int,
            "storytelling_score": int,
            "aim_clarity_score": int,
            "textual_confidence": int,
            "grammar_reasoning": "string",
            "storytelling_reasoning": "string",
            "aim_reasoning": "string",
            "confidence_reasoning": "string"
        }
        """

        try:
            response = await self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Transcript:\n{combined_transcript}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=500
            )

            result_json = json.loads(response.choices[0].message.content)
            
            # Validation / Normalization Layer (as requested)
            return self._validate_and_sanitize(result_json)

        except Exception as e:
            error_logger.error(f"LLM Analysis Failed: {e}")
            return self._get_fallback_result(str(e))

    def _validate_and_sanitize(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Clamp scores and ensure non-null."""
        def clamp(val, max_v):
            try:
                if val is None: return 0
                v = float(val)
                return max(0, min(v, max_v))
            except:
                return 0
        
        sanitized = {}
        sanitized["grammar_score"] = clamp(result.get("grammar_score"), 10)
        sanitized["storytelling_score"] = clamp(result.get("storytelling_score"), 20)
        sanitized["aim_clarity_score"] = clamp(result.get("aim_clarity_score"), 20)
        sanitized["textual_confidence"] = clamp(result.get("textual_confidence"), 10)
        
        sanitized["grammar_reasoning"] = str(result.get("grammar_reasoning", "N/A"))
        sanitized["storytelling_reasoning"] = str(result.get("storytelling_reasoning", "N/A"))
        sanitized["aim_reasoning"] = str(result.get("aim_reasoning", "N/A"))
        sanitized["confidence_reasoning"] = str(result.get("confidence_reasoning", "N/A"))
        
        return sanitized

    def _get_fallback_result(self, reason: str) -> Dict[str, Any]:
        return {
            "grammar_score": 0,
            "storytelling_score": 0,
            "aim_clarity_score": 0,
            "textual_confidence": 0,
            "grammar_reasoning": f"Analysis failed: {reason}",
            "storytelling_reasoning": f"Analysis failed: {reason}",
            "aim_reasoning": f"Analysis failed: {reason}",
            "confidence_reasoning": f"Analysis failed: {reason}"
        }

llm_analysis_service = LLMAnalysisService()
