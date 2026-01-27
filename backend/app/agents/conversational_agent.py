"""
Conversational Agent for AI Assessment.
Manages conversation flow, determines transitions, and generates contextual responses.
"""
from openai import AzureOpenAI
from app.config import settings
from .prompts import SECTION_PROMPTS
import json
import httpx
from app.core.logging import ai_logger, error_logger
from typing import Dict, List, Optional, Any


class ConversationalAgent:
    """
    AI agent that conducts conversational assessments.
    Uses GPT-4o to manage dialogue, ask follow-ups, and determine section transitions.
    """
    
    def __init__(self):
        # Create HTTP client with timeout
        self.http_client = httpx.Client(timeout=90.0)
        
        # Initialize Azure OpenAI client
        self.client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            http_client=self.http_client
        )
        self.deployment_name = settings.AZURE_OPENAI_DEPLOYMENT_NAME
    
    def get_response(
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
            # Call GPT-4o with JSON mode
            ai_logger.info(f"Calling Azure OpenAI for conversational response...")
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.8,  # Slightly higher for conversational variety
                max_tokens=500
            )
            
            # Parse JSON response
            result = json.loads(response.choices[0].message.content)
            
            # Extract fields with defaults
            agent_message = result.get("agent_message", "I see. Could you tell me more?")
            completeness_score = result.get("completeness_score", 5)
            should_transition_raw = result.get("should_transition", False)
            next_section = result.get("next_section")
            
            # Apply transition logic
            # Minimum turn requirement: at least 2 exchanges before allowing transition
            can_transition = turn_count >= 2
            
            should_transition = bool(should_transition_raw) and can_transition and completeness_score >= 6
            
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
            "reading": "Great! Now let's move to the reading section. I'll give you a short passage to read aloud.",
            "listening": "Excellent! Next is the listening section. I'll tell you a story, and you'll answer questions about it.",
            "storytelling": "Perfect! Now let's test your storytelling. I'll give you a prompt to respond to.",
            "opinion": "Wonderful! For this section, I'd like to hear your opinion on a topic.",
            "aim": "Thank you! For our final section, let's discuss your goals and aspirations."
        }
        return intros.get(section_name, f"Let's move to the {section_name} section.")


# Singleton instance
conversational_agent = ConversationalAgent()
