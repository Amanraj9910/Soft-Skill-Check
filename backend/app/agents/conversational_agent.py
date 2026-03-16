"""
Conversational Agent for AI Assessment.
Manages conversation flow, determines transitions, and generates contextual responses.
"""
from openai import AsyncAzureOpenAI
from app.config import settings
from .prompts import SECTION_PROMPTS
import json
import httpx
import jsonschema
import pybreaker
from app.core.circuit_breakers import openai_breaker
from app.core.concurrency import openai_mini_semaphore
from app.core.logging import ai_logger, error_logger
from typing import Dict, List, Optional, Any


class ConversationalAgent:
    """
    AI agent that conducts conversational assessments.
    Uses GPT-4o to manage dialogue, ask follow-ups, and determine section transitions.
    """
    
    def __init__(self):
        # Create HTTP client with tuned connection pool
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=5.0, read=60.0, write=10.0, pool=5.0),
            limits=httpx.Limits(
                max_connections=30,
                max_keepalive_connections=10,
                keepalive_expiry=30.0
            )
        )
        
        # Initialize Azure OpenAI client
        self.client = AsyncAzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            http_client=self.http_client
        )
        self.deployment_name = settings.AZURE_OPENAI_DEPLOYMENT_NAME_MINI
    
    async def get_response(
        self,
        user_message: str,
        section: str,
        conversation_history: List[Dict[str, str]],
        turn_count: int = 0
    ) -> Dict[str, Any]:
        """
        Generate AI response and determine if section should transition.
        
        Args:
            user_message: Latest user input (transcript)
            section: Current section ID (e.g., 'introduction', 'reading')
            conversation_history: List of previous exchanges [{user: ..., agent: ...}]
            turn_count: Number of exchanges so far in this section
        
        Returns:
            {
                "agent_message": str,
                "should_transition": bool,
                "next_section": str | None,
                "completeness_score": int (1-10)
            }
        """
        ai_logger.info(f"Generating response for section '{section}', turn {turn_count + 1}")
        
        # Get section-specific prompt
        system_prompt = SECTION_PROMPTS.get(section, SECTION_PROMPTS['introduction'])
        
        # Build conversation messages
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        for exchange in conversation_history:
            messages.append({"role": "user", "content": exchange.get('user', '')})
            messages.append({"role": "assistant", "content": exchange.get('agent', '')})
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        try:
            # Call GPT-4o with JSON mode (protected by circuit breaker)
            ai_logger.info(f"Calling Azure OpenAI for conversational response...")
            # Use the mini semaphore to limit concurrency for this deployment
            try:
                async with openai_mini_semaphore:
                    response = await openai_breaker.call_async(
                        self.client.chat.completions.create,
                        model=self.deployment_name,
                        messages=messages,
                        temperature=0.7,
                        max_tokens=300,
                        top_p=0.9
                    )
            except pybreaker.CircuitBreakerError:
                error_logger.error("OpenAI circuit breaker OPEN. Failing fast.")
                return {
                    "agent_message": "I'm experiencing a temporary issue. Please wait a moment and try again.",
                    "should_transition": False,
                    "next_section": None,
                    "completeness_score": 0
                }
            
            # Parse JSON response
            result = json.loads(response.choices[0].message.content)

            
            # Extract fields with defaults
            agent_message = result.get("agent_message", "I see. Could you tell me more?")
            completeness_score = result.get("completeness_score")
            # Handle None or non-int
            try:
                completeness_score = int(completeness_score)
            except (TypeError, ValueError):
                completeness_score = 5
            should_transition_raw = result.get("should_transition", False)
            next_section = result.get("next_section")
            
            # Apply transition logic
            
            # --- OVERRIDES ---
            
            # 1. Introduction: Strict Max Turn Limit (per user request: 5 steps max)
            if section == 'introduction' and turn_count >= 5:
                should_transition = True
                next_section = 'reading' # Fallback if agent didn't set it
                # OVERWRITE message to prevent "hanging question"
                agent_message = "Thank you for sharing that. Let's move on to the next section." 
                ai_logger.info("Forcing transition in Introduction due to turn limit.")

            # 2. Reading: Always transition after 1 turn (User reads -> Done)
            elif section == 'reading':
                should_transition = True
                completeness_score = 10
                next_section = 'listening' # Shadowing
                agent_message = "Excellent reading. Now, get ready for the shadowing exercise."
                ai_logger.info("Forcing transition in Reading section (One-shot).")

            # 3. Listening/Shadowing: Strict Turn Limit (Intro + 3 parts + buffers = ~7-8 max)
            elif section in ['listening', 'shadowing'] and turn_count >= 7:
                 should_transition = True
                 next_section = 'storytelling'
                 agent_message = "Great effort. Let's move on to the next section."
                 completeness_score = 10
                 ai_logger.info(f"Forcing transition in {section} section due to turn limit.")

            # 4. Storytelling: Limit to 2 turns (Story + Follow-up)
            elif section == 'storytelling' and turn_count >= 2:
                 should_transition = True
                 next_section = 'opinion'
                 agent_message = "That sounds like a wonderful memory! Thank you for sharing it. Let's move on to the next section."
                 completeness_score = 10
                 ai_logger.info("Forcing transition in Storytelling due to turn limit.")

            # 5. Opinion: Limit to 3 turns
            elif section == 'opinion' and turn_count >= 3:
                 should_transition = True
                 next_section = 'aim'
                 agent_message = "Thank you for sharing your perspective. Let's move to the final section."
                 completeness_score = 10
                 ai_logger.info("Forcing transition in Opinion due to turn limit.")

            # 6. Aim: Limit to 3 turns -> FINISH
            elif section == 'aim' and turn_count >= 3:
                 should_transition = True
                 next_section = None # End of assessment
                 agent_message = "Thank you for sharing your goals. This concludes the assessment. You will receive your results shortly."
                 completeness_score = 10
                 ai_logger.info("Forcing transition in Aim due to turn limit (End of Assessment).")

            # 7. Standard Logic for other sections (Introduction, etc.)
            else:
                # Minimum turn requirement: at least 2 exchanges before allowing transition
                can_transition = turn_count >= 2
                
                # Default Logic: Require completeness score
                pass_score = completeness_score >= 6
                
                # EXCEPTION: Shadowing/Listening should depend solely on AI determining end of script,
                # NOT on performance score (which might be low due to accent/errors).
                if section in ['listening', 'shadowing']:
                    pass_score = True
                
                should_transition = bool(should_transition_raw) and can_transition and pass_score
            
            # CRITICAL: If transitioning, ensure message is NOT a question
            if should_transition:
                # Check if it looks like a question
                if "?" in agent_message:
                     ai_logger.info("Transitioning but agent asked a question. Overwriting with closing statement.")
                     if section == 'introduction':
                         agent_message = "Thank you for sharing. Let's move on."
                     elif section == 'storytelling':
                         agent_message = "That was a great story. Let's proceed."
                     elif section == 'opinion':
                         agent_message = "Thank you for your thoughts. Moving to the final section."
                     elif section == 'aim':
                          agent_message = "Thank you for sharing your goals. This concludes the assessment."
                     else:
                         agent_message = "Great. Let's move to the next section."

            ai_logger.info(
                f"Response generated: completeness={completeness_score}/10, "
                f"transition={should_transition}, next={next_section}"
            )
            
            return {
                "agent_message": agent_message,
                "should_transition": should_transition,
                "next_section": next_section if should_transition else None,
                "completeness_score": completeness_score
            }
            
        except Exception as e:
            error_logger.error(f"ConversationalAgent error: {str(e)}")
            # Fallback response
            return {
                "agent_message": "I see. Could you elaborate on that?",
                "should_transition": False,
                "next_section": None,
                "completeness_score": 3
            }
    
    def generate_greeting(self) -> str:
        """
        Generate initial greeting message.
        
        Returns:
            Greeting message as string
        """
        return (
            "Hello! I'm Emma, and I'll be guiding you through today's English speaking assessment. "
            "This assessment has several sections and will take about 15-20 minutes. "
            "Before we begin, may I have your name?"
        )
    
    def generate_section_intro(self, section_name: str) -> str:
        """
        Generate transitional introduction to a new section.
        
        Args:
            section_name: Name of the section to introduce
        
        Returns:
            Intro message
        """
        intros = {
            "reading": "Beginning reading assessment.",
            "listening": "I will say a sentence. Please repeat it exactly. Let's begin. Innovation drives progress.",
            "shadowing": "I will say a sentence. Please repeat it exactly. Let's begin. Innovation drives progress.",
            "storytelling": "Starting storytelling section.",
            "opinion": "Starting opinion section.",
            "aim": "Starting final section."
        }
        return intros.get(section_name, f"Starting {section_name}.")


# Singleton instance
conversational_agent = ConversationalAgent()
