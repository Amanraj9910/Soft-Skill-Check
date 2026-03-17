"""
Scoring Engine.
Analyzes user responses using Azure OpenAI (GPT-4o) against the assessment rubric.
"""
from openai import AsyncAzureOpenAI
import openai
from fastapi import HTTPException
from app.config import settings
from .models import AIAnalysisResult, AssessmentStepScore
import json
import httpx
import asyncio

# Import logging
from app.core.logging import ai_logger, error_logger
from app.core.concurrency import openai_full_semaphore, openai_mini_semaphore


class ScoringEngine:
    def __init__(self):
        # Create async HTTP client with tuned pool (background, lower priority)
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=5.0, read=60.0, write=10.0, pool=10.0),
            limits=httpx.Limits(
                max_connections=10,
                max_keepalive_connections=5,
                keepalive_expiry=30.0
            )
        )
        
        self.client = AsyncAzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            http_client=self.http_client
        )
        self.deployment_name = settings.AZURE_OPENAI_DEPLOYMENT_NAME
        self.deployment_name_mini = settings.AZURE_OPENAI_DEPLOYMENT_NAME_MINI
    async def analyze_response(
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
            async with openai_full_semaphore:
                response = await self.client.chat.completions.create(
                    model=self.deployment_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.7
                )
        except openai.RateLimitError:
            raise HTTPException(503, "AI service temporarily busy, retry in 5s")
        except Exception as api_err:
            import traceback
            error_details = traceback.format_exc()
            error_logger.error(f"Azure OpenAI Call Failed: {str(api_err)}\nTraceback:\n{error_details}")
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

    async def analyze_full_assessment(
        self,
        full_transcript: str, 
        conversation_history: list
    ) -> AIAnalysisResult:
        """
        Performs a holistic analysis of the entire assessment session.
        Returns detailed scores and reasoning for each category.
        """
        if not full_transcript and not conversation_history:
            return AIAnalysisResult(
                transcript="",
                scores=AssessmentStepScore(
                   fluency=0, pronunciation=0, grammar=0, confidence=0, vocal_confidence=0, textual_confidence=0,
                   hesitation=0, storytelling=0, vision_clarity=0, aim_clarity=0,
                   total_step_score=0, feedback="No input provided.", improvement_tips=[]
                ),
                ai_response_text="Assessment incompelete."
            )
            
        system_prompt = """
        You are an expert English language assessor.
        
        You must evaluate the entire conversation based on the following RELAXED and ENCOURAGING rubric:

        1️⃣ Fluency — 20 Marks
        Speaking pace, flow, natural pauses.
        What we judge:
        - Is the speech continuous?
        - Pauses for thought are COMPLETELY NATURAL and ACCEPTABLE.
        - Occasional stutters or restarts should NOT be heavily penalized.
        - Focus on the ability to keep communicating.
        
        Marking Guide:
        - 17–20: Smooth flow, comfortable pace (breaks for thought allowed)
        - 13–16: Good flow, some noticeable pauses/hesitations
        - 9–12: Understandable flow, frequent pauses but keeps going
        - 5–8: Very broken, struggle to maintain any flow
        - 0–4: Impossible to follow

        2️⃣ Pronunciation — 10 Marks
        Clarity of sounds.
        What we judge:
        - Can the words be understood?
        - If you understand the word, it is correct enough.
        - Accent is NEVER penalized.
        
        Marking Guide:
        - 9–10: Clear and easy to understand
        - 7–8: Mostly clear, minor indistinct sounds
        - 5–6: Understandable with effort
        - 3–4: Many words unclear
        - 0–2: Unintelligible

        3️⃣ Grammar — 10 Marks
        Sentence structure and meaning.
        What we judge:
        - Can you understand the meaning?
        - Spoken grammar is flexible. STRICT grammar rules do NOT apply.
        - "I went to shop" is fine even if "the" is missing.
        
        Marking Guide:
        - 9–10: Meaning is clear, natural phrasing
        - 7–8: Minor errors, meaning always clear
        - 5–6: Frequent errors but meaning is mostly clear
        - 3–4: Errors make understanding difficult
        - 0–2: Meaning lost due to grammar

        4️⃣ Vocal Confidence — 10 Marks
        Voice steadiness.
        What we judge:
        - Does the speaker try to speak up?
        - Nervousness is normal. Look for effort to communicate.
        
        Marking Guide:
        - 9–10: Good volume, generally steady
        - 7–8: A bit nervous but clearly audible
        - 5–6: Shaky but trying
        - 3–4: Very quiet/timid
        - 0–2: Whispering/Silent

        5️⃣ Textual Confidence — 10 Marks
        Assertiveness.
        What we judge:
        - "I think", "maybe" are conversational fillers, NOT necessarily lack of confidence.
        - Look for the intent to answer the question.
        
        Marking Guide:
        - 9–10: Direct answers
        - 7–8: Mostly direct, some hedging ("I think")
        - 5–6: Indirect but relevant
        - 3–4: Very evasive
        - 0–2: No clear answer

        6️⃣ Storytelling — 20 Marks
        Structure and engagement.
        What we judge:
        - Does it have a simple sequence (Beginning -> End)?
        - Simple stories are GOOD stories.
        - jumping betweeen ideas is allowed as long as the main point is there.
        
        Marking Guide:
        - 17–20: Clear sequence, easy to follow
        - 13–16: Basic beginning/middle/end, some jumping around
        - 9–12: Loose structure but tells a story
        - 5–8: Hard to follow the thread
        - 0–4: No story

        7️⃣ Vision Clarity — 10 Marks
        Ambition.
        What we judge:
        - Do they have ANY goal?
        - "I want to be a developer" is a CLEAR vision.
        - Details are NOT required.
        
        Marking Guide:
        - 9–10: Has a stated long-term goal
        - 7–8: General idea of future
        - 5–6: Vague idea
        - 3–4: Very unsure
        - 0–2: No data

        8️⃣ Aim Clarity — 10 Marks
        Next steps.
        What we judge:
        - Do they know the next step?
        - "I will study" is a clear aim.
        
        Marking Guide:
        - 9–10: Has a next step/goal
        - 7–8: General idea of next steps
        - 5–6: Vague steps
        - 3–4: No idea
        - 0–2: No data

        9️⃣ Hesitation — Penalty (0 to -10)
        Disruption penalty.
        What we judge:
        - ONLY penalize if silence is awkward or completely stops communication.
        - "Um", "Uh" are natural thinking noises. IGNORE them unless excessive (every 2 words).
        
        Penalty Guide:
        - 0: Normal flow (includes some ums/uhs)
        - -2: Frequent ums/uhs but keeps going
        - -5: Very disruptive/stops meanting
        - -8: Painful to listen to
        - -10: Communication failed

        🧮 Final Score Logic
        Total Score = Fluency + Pronunciation + Grammar + Vocal Confidence + Textual Confidence + Storytelling + Vision Clarity + Aim Clarity + Hesitation (negative)
        Max: 100
        
        Output MUST be a valid JSON object with detailed reasoning for each score:
        {
            "fluency": { "score": int, "reasoning": "..." },
            "pronunciation": { "score": int, "reasoning": "..." },
            "grammar": { "score": int, "reasoning": "..." },
            "vocal_confidence": { "score": int, "reasoning": "..." },
            "textual_confidence": { "score": int, "reasoning": "..." },
            "hesitation": { "score": int, "reasoning": "..." },
            "storytelling": { "score": int, "reasoning": "..." },
            "vision_clarity": { "score": int, "reasoning": "..." },
            "aim_clarity": { "score": int, "reasoning": "..." },
            "overall_review": "Comprehensive summary of performance (3-4 sentences).",
            "strengths": ["...", "..."],
            "weaknesses": ["...", "..."],
            "recommendations": ["...", "..."]
        }
        """
        
        user_content = f"""
        Analyze this full assessment transcript and conversation history:
        
        Full Transcript: "{full_transcript}"
        
        Conversation Structure (Q&A):
        {json.dumps(conversation_history[-10:], indent=2)} 
        (Showing last 10 turns for context if transcript is long)
        """
        
        try:
            ai_logger.info("🧠 Starting Holistic Assessment Analysis (GPT-4o)...")
            async with openai_full_semaphore:
                response = await self.client.chat.completions.create(
                    model=self.deployment_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.7
                )
            
            result_json = json.loads(response.choices[0].message.content)
            
            # Helper to safely extract score
            def get_score(cat):
                val = result_json.get(cat, {}).get("score", 0)
                # Handle possible string/int mismatch or malformed structure
                if isinstance(val, (int, float)):
                    return val
                return 0

            # Calculate total
            total = (
                get_score("fluency") + 
                get_score("pronunciation") + 
                get_score("grammar") + 
                get_score("vocal_confidence") + 
                get_score("textual_confidence") +
                get_score("hesitation") + # Negative
                get_score("storytelling") + 
                get_score("vision_clarity") +
                get_score("aim_clarity")
            )
            total = max(0, min(100, total))
            
            # Create a Scores structure (mapped to our Pydantic model roughly)
            scores = AssessmentStepScore(
                fluency=get_score("fluency"),
                pronunciation=get_score("pronunciation"),
                grammar=get_score("grammar"),
                confidence=get_score("vocal_confidence"), # map vocal_confidence to legacy confidence field
                vocal_confidence=get_score("vocal_confidence"),
                textual_confidence=get_score("textual_confidence"),
                hesitation=get_score("hesitation"),
                storytelling=get_score("storytelling"),
                vision_clarity=get_score("vision_clarity"),
                aim_clarity=get_score("aim_clarity"),
                total_step_score=total,
                feedback=result_json.get("overall_review", ""),
                improvement_tips=result_json.get("recommendations", [])
            )
            
            return AIAnalysisResult(
                transcript=full_transcript,
                scores=scores,
                ai_response_text=result_json.get("overall_review", ""),
                raw_json=result_json # We can attach this to save full details
            )

        except Exception as e:
            error_logger.error(f"Holistic Analysis Failed: {e}")
            # Return zeroed struct on failure
            return AIAnalysisResult(
                 transcript=full_transcript,
                 scores=AssessmentStepScore(
                    fluency=0, pronunciation=0, grammar=0, confidence=0,
                    hesitation=0, storytelling=0, vision_clarity=0,
                    total_step_score=0, feedback="Analysis failed.", improvement_tips=[]
                 ),
                 ai_response_text="Analysis unavailable."
            )

# Singleton
scoring_engine = ScoringEngine()
