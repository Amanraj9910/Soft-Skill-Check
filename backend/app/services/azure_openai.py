"""
Azure OpenAI Service integration for conversation and scoring.
Uses GPT-4o-mini as primary, GPT-4o as fallback with retry logic.
"""
from typing import Dict, Any, List, Optional
from openai import AsyncAzureOpenAI, APIStatusError
from app.config import settings
import json
import httpx
import pybreaker
import asyncio
from app.core.circuit_breakers import openai_breaker, call_async_native
from app.core.concurrency import openai_mini_semaphore, openai_full_semaphore
from app.core.logging import error_logger


class AzureOpenAIService:
    """Service for Azure OpenAI with GPT-4o-mini primary, GPT-4o fallback."""
    
    def __init__(self):
        """Initialize Azure OpenAI clients for both mini and full models."""
        # Create explicit async client with tuned connection pool for 100+ users
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=5.0, read=60.0, write=10.0, pool=5.0),
            limits=httpx.Limits(
                max_connections=100,
                max_keepalive_connections=50,
                keepalive_expiry=30.0
            )
        )
        
        # Primary: GPT-4o-mini (faster, cheaper, higher rate limits)
        self.client_mini = AsyncAzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            http_client=self.http_client
        )
        self.deployment_mini = settings.AZURE_OPENAI_DEPLOYMENT_NAME_MINI
        
        # Secondary/Fallback: GPT-4o (higher quality, used when mini fails)
        self.client_full = AsyncAzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            http_client=self.http_client
        )
        self.deployment_full = settings.AZURE_OPENAI_DEPLOYMENT_NAME
    
    async def _call_with_retry(self, client, model, messages, max_retries=3, **kwargs):
        """
        Call OpenAI API with exponential backoff retry for 429 rate limits.
        Falls back from mini to full model if mini fails repeatedly.
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    **kwargs
                )
                return response
            except APIStatusError as e:
                last_error = e
                if e.status_code == 429:  # Rate limit
                    # Exponential backoff: 2s, 4s, 8s
                    wait_time = 2 ** (attempt + 1)
                    error_logger.warning(f"⚠️ Rate limit hit (429), retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                elif e.status_code >= 500:  # Server error
                    wait_time = 1 * (attempt + 1)
                    error_logger.warning(f"⚠️ Server error ({e.status_code}), retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    raise  # Other errors (400, 401, etc.) - don't retry
            except Exception as e:
                last_error = e
                error_logger.warning(f"⚠️ OpenAI error (attempt {attempt+1}): {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
        
        # All retries exhausted - try fallback model if using mini
        if model == self.deployment_mini:
            error_logger.warning(f"⚠️ GPT-4o-mini failed after {max_retries} retries, falling back to GPT-4o")
            try:
                response = await self.client_full.chat.completions.create(
                    model=self.deployment_full,
                    messages=messages,
                    **kwargs
                )
                return response
            except Exception as fallback_error:
                error_logger.error(f"❌ Fallback to GPT-4o also failed: {str(fallback_error)}")
                raise last_error  # Raise original error
        
        raise last_error
    
    async def generate_agent_response(
        self,
        conversation_history: List[Dict[str, str]],
        current_section: str,
        user_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate AI agent response for conversation.
        Uses GPT-4o-mini with automatic fallback to GPT-4o.
        """
        try:
            # Build system prompt based on section
            system_prompt = self._get_section_prompt(current_section)
            
            # Prepare messages
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(conversation_history)
            
            if user_message:
                messages.append({"role": "user", "content": user_message})
            
            # Call GPT-4o-mini with retry and semaphore
            try:
                async with openai_mini_semaphore:
                    response = await call_async_native(
                        openai_breaker,
                        self._call_with_retry,
                        self.client_mini,
                        self.deployment_mini,
                        messages,
                        temperature=0.7,
                        max_tokens=300,
                        top_p=0.9
                    )
            except pybreaker.CircuitBreakerError:
                return {
                    "success": False,
                    "message": "AI service temporarily unavailable. Please try again in 30 seconds.",
                    "tokens_used": 0
                }
            
            agent_message = response.choices[0].message.content
            
            return {
                "success": True,
                "message": agent_message,
                "tokens_used": response.usage.total_tokens,
                "finish_reason": response.choices[0].finish_reason
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "I apologize, but I'm having trouble responding right now."
            }
    
    async def score_assessment(
        self,
        responses: List[Dict[str, Any]],
        audio_features: Dict[str, Any],
        vision_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Score complete assessment using GPT-4o (full model for accuracy).
        """
        try:
            # Build scoring prompt
            prompt = self._build_scoring_prompt(responses, audio_features, vision_metrics)
            
            # Request structured output
            messages = [
                {"role": "system", "content": "You are an expert English language assessor. Provide detailed, constructive feedback."},
                {"role": "user", "content": prompt}
            ]
            
            async with openai_full_semaphore:
                response = await self._call_with_retry(
                    self.client_full,
                    self.deployment_full,
                    messages,
                    temperature=0.3,
                    max_tokens=1500,
                    response_format={"type": "json_object"}
                )
            
            # Parse JSON response
            scoring_result = json.loads(response.choices[0].message.content)
            
            return {
                "success": True,
                "scores": scoring_result,
                "tokens_used": response.usage.total_tokens
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def analyze_grammar(self, text: str) -> Dict[str, Any]:
        """
        Analyze grammar quality of user's speech.
        """
        try:
            prompt = f"""Analyze the grammar in this spoken English text and provide a score out of 10.

Text: "{text}"

Provide response in JSON format:
{{
    "grammar_score": <0-10>,
    "errors": [list of grammar mistakes],
    "strengths": [list of correct usage],
    "suggestions": [improvement suggestions]
}}"""
            
            async with openai_mini_semaphore:
                response = await self._call_with_retry(
                    self.client_mini,
                    self.deployment_mini,
                    [
                        {"role": "system", "content": "You are a grammar expert. Be constructive and educational."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=500,
                    response_format={"type": "json_object"}
                )
            
            result = json.loads(response.choices[0].message.content)
            return {"success": True, **result}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def evaluate_storytelling(self, story_text: str) -> Dict[str, Any]:
        """
        Evaluate storytelling quality.
        """
        try:
            prompt = f"""Evaluate this personal story for structure, engagement, and flow. Score out of 20.

Story: "{story_text}"

Provide JSON response:
{{
    "storytelling_score": <0-20>,
    "structure_quality": "description",
    "engagement_level": "description",
    "flow_assessment": "description",
    "strengths": [list],
    "improvements": [list]
}}"""
            
            async with openai_mini_semaphore:
                response = await self._call_with_retry(
                    self.client_mini,
                    self.deployment_mini,
                    [
                        {"role": "system", "content": "You are a storytelling expert. Evaluate narrative quality."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=600,
                    response_format={"type": "json_object"}
                )
            
            result = json.loads(response.choices[0].message.content)
            return {"success": True, **result}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _get_section_prompt(self, section: str) -> str:
        """Get system prompt for specific section."""
        prompts = {
            "welcome": """You are a friendly English assessment AI. Welcome the user warmly, 
            explain that you'll have a natural conversation to assess their English skills. 
            Be encouraging and reduce anxiety. Keep response under 50 words.""",
            
            "introduction": """You are conducting an introduction section. Ask natural questions 
            about their name, location, education or work. Be conversational and warm. 
            Listen actively and ask follow-up questions. Keep responses brief.""",
            
            "reading": """You are conducting a reading assessment. Present a sentence for the 
            user to read aloud. Choose a moderately complex sentence with some multisyllabic words. 
            After they read, acknowledge and move forward.""",
            
            "listening": """You are conducting a listening assessment. Speak a clear sentence 
            and ask the user to repeat it. Choose sentences with varied vocabulary. 
            After they repeat, acknowledge and proceed.""",
            
            "storytelling": """You are prompting storytelling. Ask the user to share a personal 
            experience or memorable event. Encourage them to include details. 
            Listen actively and ask one follow-up question.""",
            
            "opinion": """You are discussing technology and AI. Ask for their opinion on 
            how AI is changing education or work. Encourage them to explain their reasoning. 
            Be curious and engaged.""",
            
            "aim": """You are concluding the assessment. Ask about their future goals, 
            career aspirations, or what they hope to achieve. Be supportive and interested. 
            Then thank them warmly for participating."""
        }
        
        return prompts.get(section, prompts["introduction"])
    
    def _build_scoring_prompt(
        self,
        responses: List[Dict[str, Any]],
        audio_features: Dict[str, Any],
        vision_metrics: Dict[str, Any]
    ) -> str:
        """Build comprehensive scoring prompt."""
        
        # Aggregate transcripts
        full_transcript = "\n\n".join([
            f"[{r.get('section', 'unknown').upper()}]\n{r.get('user_transcript', '')}"
            for r in responses
        ])
        
        prompt = f"""Score this English speaking assessment across 7 categories:

USER'S COMPLETE TRANSCRIPT:
{full_transcript}

AUDIO ANALYSIS:
- Average pitch stability: {audio_features.get('pitch_stability', 'N/A')}
- Volume consistency: {audio_features.get('volume_variance', 'N/A')}
- Silence ratio: {audio_features.get('silence_ratio', 'N/A')}
- Average pause duration: {audio_features.get('average_pause_duration', 'N/A')}s

VISION ANALYSIS:
- Eye contact score: {vision_metrics.get('eye_contact_score', 'N/A')}/10
- Head stability: {vision_metrics.get('head_stability_score', 'N/A')}/10
- Overall clarity: {vision_metrics.get('overall_clarity_score', 'N/A')}/10

SCORE THESE CATEGORIES:

1. **Fluency (0-20)**: Speaking pace, flow, natural rhythm
2. **Pronunciation (0-10)**: Clarity, accent comprehensibility
3. **Grammar (0-10)**: Sentence structure, tense usage, errors
4. **Confidence (0-20)**: Voice steadiness, assertiveness
5. **Hesitation Penalty (0 to -10)**: Filler words, excessive pauses
6. **Storytelling (0-20)**: Narrative structure, engagement
7. **Vision Clarity (0-10)**: Body language, presence (from vision data)

Provide JSON response:
{{
    "fluency_score": <number>,
    "pronunciation_score": <number>,
    "grammar_score": <number>,
    "confidence_score": <number>,
    "hesitation_penalty": <negative number>,
    "storytelling_score": <number>,
    "vision_clarity_score": <number>,
    "total_score": <sum of all>,
    "grade": "<beginner|elementary|intermediate|upper_intermediate|advanced|expert>",
    "strengths": ["strength1", "strength2", "strength3"],
    "weaknesses": ["weakness1", "weakness2", "weakness3"],
    "recommendations": ["recommendation1", "recommendation2", "recommendation3"],
    "overall_feedback": "2-3 sentence summary"
}}

Be fair, constructive, and encouraging."""
        
        return prompt


# Create singleton instance
azure_openai_service = AzureOpenAIService()


def get_azure_openai_service() -> AzureOpenAIService:
    """Dependency for accessing Azure OpenAI service."""
    return azure_openai_service
