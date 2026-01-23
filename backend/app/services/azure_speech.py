"""
Azure Speech Service integration for Speech-to-Text and Text-to-Speech.
"""
import os
import tempfile
from typing import Optional, Dict, Any, Tuple
import azure.cognitiveservices.speech as speechsdk
from app.config import settings


class AzureSpeechService:
    """Service for Azure Speech operations (STT, TTS, Pronunciation Assessment)."""
    
    def __init__(self):
        """Initialize Azure Speech SDK."""
        self.speech_key = settings.AZURE_SPEECH_KEY
        self.speech_region = settings.AZURE_SPEECH_REGION
        self.speech_language = settings.AZURE_SPEECH_LANGUAGE
        self.tts_voice = settings.AZURE_TTS_VOICE_NAME
        
        # Create speech config
        self.speech_config = speechsdk.SpeechConfig(
            subscription=self.speech_key,
            region=self.speech_region
        )
        self.speech_config.speech_recognition_language = self.speech_language
        self.speech_config.speech_synthesis_voice_name = self.tts_voice
    
    async def speech_to_text(
        self, 
        audio_file_path: str,
        enable_pronunciation_assessment: bool = True,
        reference_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Convert speech to text with optional pronunciation assessment.
        
        Args:
            audio_file_path: Path to audio file
            enable_pronunciation_assessment: Whether to assess pronunciation
            reference_text: Expected text (for pronunciation assessment)
        
        Returns:
            Dictionary with transcript, confidence, and pronunciation scores
        """
        try:
            # Create audio config from file
            audio_config = speechsdk.AudioConfig(filename=audio_file_path)
            
            # Create speech recognizer
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )
            
            # Enable pronunciation assessment if requested
            if enable_pronunciation_assessment and reference_text:
                pronunciation_config = speechsdk.PronunciationAssessmentConfig(
                    reference_text=reference_text,
                    grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
                    granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
                    enable_miscue=True
                )
                pronunciation_config.apply_to(speech_recognizer)
            
            # Perform recognition
            result = speech_recognizer.recognize_once()
            
            # Process result
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                response = {
                    "success": True,
                    "transcript": result.text,
                    "confidence": 0.0,
                    "pronunciation_assessment": None
                }
                
                # Extract pronunciation assessment if available
                if enable_pronunciation_assessment and reference_text:
                    pronunciation_result = speechsdk.PronunciationAssessmentResult(result)
                    response["pronunciation_assessment"] = {
                        "accuracy_score": pronunciation_result.accuracy_score,
                        "fluency_score": pronunciation_result.fluency_score,
                        "completeness_score": pronunciation_result.completeness_score,
                        "pronunciation_score": pronunciation_result.pronunciation_score
                    }
                    response["confidence"] = pronunciation_result.accuracy_score / 100.0
                
                return response
            
            elif result.reason == speechsdk.ResultReason.NoMatch:
                return {
                    "success": False,
                    "error": "No speech could be recognized",
                    "transcript": "",
                    "confidence": 0.0
                }
            
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation = result.cancellation_details
                return {
                    "success": False,
                    "error": f"Speech recognition canceled: {cancellation.reason}",
                    "transcript": "",
                    "confidence": 0.0
                }
            
            else:
                return {
                    "success": False,
                    "error": "Unknown error occurred",
                    "transcript": "",
                    "confidence": 0.0
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "transcript": "",
                "confidence": 0.0
            }
    
    async def text_to_speech(
        self,
        text: str,
        output_file_path: Optional[str] = None,
        voice_name: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Convert text to speech audio.
        
        Args:
            text: Text to synthesize
            output_file_path: Where to save audio (if None, creates temp file)
            voice_name: Voice to use (if None, uses default)
        
        Returns:
            Tuple of (success, audio_file_path, error_message)
        """
        try:
            # Use custom voice if provided
            if voice_name:
                self.speech_config.speech_synthesis_voice_name = voice_name
            
            # Create output file path if not provided
            if not output_file_path:
                temp_dir = tempfile.gettempdir()
                output_file_path = os.path.join(temp_dir, f"tts_{os.urandom(8).hex()}.wav")
            
            # Create audio config
            audio_config = speechsdk.AudioConfig(filename=output_file_path)
            
            # Create synthesizer
            speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )
            
            # Synthesize
            result = speech_synthesizer.speak_text_async(text).get()
            
            # Check result
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                return True, output_file_path, None
            
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation = result.cancellation_details
                error_msg = f"Speech synthesis canceled: {cancellation.reason}"
                if cancellation.error_details:
                    error_msg += f" - {cancellation.error_details}"
                return False, None, error_msg
            
            else:
                return False, None, "Unknown error occurred during synthesis"
        
        except Exception as e:
            return False, None, str(e)
    
    async def synthesize_ssml(
        self,
        ssml: str,
        output_file_path: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Synthesize speech from SSML (for advanced control).
        
        Args:
            ssml: SSML markup text
            output_file_path: Where to save audio
        
        Returns:
            Tuple of (success, audio_file_path, error_message)
        """
        try:
            if not output_file_path:
                temp_dir = tempfile.gettempdir()
                output_file_path = os.path.join(temp_dir, f"tts_ssml_{os.urandom(8).hex()}.wav")
            
            audio_config = speechsdk.AudioConfig(filename=output_file_path)
            speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )
            
            result = speech_synthesizer.speak_ssml_async(ssml).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                return True, output_file_path, None
            else:
                return False, None, "SSML synthesis failed"
        
        except Exception as e:
            return False, None, str(e)
    
    def get_available_voices(self) -> list:
        """
        Get list of available neural voices.
        
        Returns:
            List of voice information
        """
        # Common neural voices for English
        return [
            {"name": "en-US-JennyNeural", "gender": "Female", "locale": "en-US"},
            {"name": "en-US-GuyNeural", "gender": "Male", "locale": "en-US"},
            {"name": "en-US-AriaNeural", "gender": "Female", "locale": "en-US"},
            {"name": "en-US-DavisNeural", "gender": "Male", "locale": "en-US"},
            {"name": "en-GB-SoniaNeural", "gender": "Female", "locale": "en-GB"},
            {"name": "en-GB-RyanNeural", "gender": "Male", "locale": "en-GB"},
            {"name": "en-IN-NeerjaNeural", "gender": "Female", "locale": "en-IN"},
            {"name": "en-IN-PrabhatNeural", "gender": "Male", "locale": "en-IN"},
        ]


# Create singleton instance
azure_speech_service = AzureSpeechService()


def get_azure_speech_service() -> AzureSpeechService:
    """Dependency for accessing Azure Speech service."""
    return azure_speech_service
