import azure.cognitiveservices.speech as speechsdk
from azure.cognitiveservices.speech import AudioDataStream, SpeechConfig, SpeechRecognizer, AudioConfig
# Remove direct import of submodules which might not work on all versions, access via speechsdk instead
import json
import logging
from typing import Dict, Any, Optional, List
from app.config import settings

logger = logging.getLogger(__name__)

class AzureSpeechService:
    def __init__(self):
        self.speech_config = speechsdk.SpeechConfig(
            subscription=settings.AZURE_SPEECH_KEY, 
            region=settings.AZURE_SPEECH_REGION
        )
        self.speech_config.speech_recognition_language = settings.AZURE_SPEECH_LANGUAGE
        # Set voice for TTS
        self.speech_config.speech_synthesis_voice_name = getattr(
            settings, 'AZURE_SPEECH_VOICE', 'en-US-JennyNeural'
        )

    def synthesize_speech_bytes(self, text: str) -> Optional[bytes]:
        """
        Synthesize speech from text and return audio bytes (WAV format).
        
        Args:
            text: The text to synthesize
            
        Returns:
            Audio bytes in WAV format, or None if synthesis fails
        """
        try:
            # Use in-memory synthesis (audio_config=None outputs to memory)
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config, 
                audio_config=None
            )
            
            result = synthesizer.speak_text_async(text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                logger.info(f"TTS synthesis completed for text of {len(text)} characters")
                return result.audio_data
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                logger.error(f"Speech synthesis canceled: {cancellation_details.reason}")
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    logger.error(f"Error details: {cancellation_details.error_details}")
                return None
            else:
                logger.error(f"Speech synthesis failed with reason: {result.reason}")
                return None
                
        except Exception as e:
            logger.error(f"Speech synthesis error: {e}")
            return None

    async def text_to_speech(self, text: str) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Convert text to speech and save to a temporary file.
        
        Args:
            text: The text to synthesize
            
        Returns:
            Tuple of (success, audio_file_path, error_message)
        """
        import tempfile
        import os
        
        try:
            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, f"tts_{os.urandom(8).hex()}.wav")
            
            audio_config = speechsdk.audio.AudioOutputConfig(filename=temp_file)
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config, 
                audio_config=audio_config
            )
            
            result = synthesizer.speak_text_async(text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                logger.info(f"TTS saved to file: {temp_file}")
                return (True, temp_file, None)
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                error_msg = f"Speech synthesis canceled: {cancellation_details.reason}"
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    error_msg += f" - {cancellation_details.error_details}"
                logger.error(error_msg)
                return (False, None, error_msg)
            else:
                error_msg = f"Speech synthesis failed with reason: {result.reason}"
                logger.error(error_msg)
                return (False, None, error_msg)
                
        except Exception as e:
            logger.error(f"Text-to-speech error: {e}")
            return (False, None, str(e))

    async def speech_to_text(
        self, 
        audio_file_path: str, 
        enable_pronunciation_assessment: bool = False,
        reference_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Convert speech to text with optional pronunciation assessment.
        
        Args:
            audio_file_path: Path to the audio file
            enable_pronunciation_assessment: Whether to enable pronunciation scoring
            reference_text: Reference text for pronunciation assessment
            
        Returns:
            Dictionary with transcript and optional pronunciation scores
        """
        try:
            audio_config = speechsdk.AudioConfig(filename=audio_file_path)
            recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config, 
                audio_config=audio_config
            )
            
            if enable_pronunciation_assessment and reference_text:
                pronunciation_config = speechsdk.PronunciationAssessmentConfig(
                    reference_text=reference_text,
                    grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
                    granularity=speechsdk.PronunciationAssessmentGranularity.Word,
                    enable_miscue=True
                )
                pronunciation_config.apply_to(recognizer)
            
            result = recognizer.recognize_once()
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                response = {
                    "transcript": result.text,
                    "success": True
                }
                
                # Extract pronunciation scores if available
                if enable_pronunciation_assessment:
                    try:
                        pronunciation_result = speechsdk.PronunciationAssessmentResult(result)
                        response["pronunciation_score"] = getattr(pronunciation_result, 'pronunciation_score', 0)
                        response["accuracy_score"] = getattr(pronunciation_result, 'accuracy_score', 0)
                        response["fluency_score"] = getattr(pronunciation_result, 'fluency_score', 0)
                        response["completeness_score"] = getattr(pronunciation_result, 'completeness_score', 0)
                    except Exception as pron_err:
                        logger.warning(f"Could not get pronunciation scores: {pron_err}")
                
                return response
                
            elif result.reason == speechsdk.ResultReason.NoMatch:
                logger.warning("No speech could be recognized")
                return {"transcript": "", "success": False, "error": "No speech recognized"}
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                error_msg = f"Recognition canceled: {cancellation_details.reason}"
                logger.error(error_msg)
                return {"transcript": "", "success": False, "error": error_msg}
                
        except Exception as e:
            logger.error(f"Speech-to-text error: {e}")
            return {"transcript": "", "success": False, "error": str(e)}
        
        return {"transcript": "", "success": False, "error": "Unknown error"}

    def convert_to_wav(self, audio_bytes: bytes) -> Optional[bytes]:
        """
        Convert audio bytes to WAV format.
        
        Args:
            audio_bytes: Raw audio bytes (can be webm, mp3, ogg, etc.)
            
        Returns:
            WAV audio bytes, or None if conversion fails
        """
        import tempfile
        import os
        
        try:
            # Write input to temp file
            with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_in:
                temp_in.write(audio_bytes)
                temp_in_path = temp_in.name
            
            temp_out_path = temp_in_path.replace('.webm', '.wav')
            
            try:
                # Use imageio_ffmpeg to get the ffmpeg executable path
                import imageio_ffmpeg
                import subprocess
                
                ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
                
                # Convert using ffmpeg subprocess directly
                # Command: ffmpeg -i input -y output
                cmd = [ffmpeg_exe, "-v", "quiet", "-i", temp_in_path, "-y", temp_out_path]
                
                subprocess.run(cmd, check=True)
                
                if os.path.exists(temp_out_path):
                    with open(temp_out_path, 'rb') as f:
                        wav_bytes = f.read()
                    return wav_bytes
                else:
                    logger.error("FFmpeg conversion finished but output file missing")
                    return audio_bytes
                
            except ImportError:
                logger.warning("imageio_ffmpeg not available, returning original audio")
                return audio_bytes
            except subprocess.CalledProcessError as e:
                logger.warning(f"FFmpeg conversion failed: {e}, returning original")
                return audio_bytes
            except Exception as conv_err:
                logger.warning(f"Audio conversion failed: {conv_err}, returning original")
                return audio_bytes
            finally:
                # Clean up temp files
                try:
                    os.remove(temp_in_path)
                except:
                    pass
                try:
                    os.remove(temp_out_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Convert to WAV error: {e}")
            return audio_bytes

    def transcribe_audio(self, audio_bytes: bytes) -> str:
        """
        Transcribe audio bytes to text (synchronous version).
        
        Args:
            audio_bytes: Audio bytes (WAV format preferred)
            
        Returns:
            Transcribed text
        """
        import tempfile
        import os
        
        try:
            # Write to temp file for Azure SDK
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_bytes)
                temp_path = temp_file.name
            
            try:
                audio_config = speechsdk.AudioConfig(filename=temp_path)
                recognizer = speechsdk.SpeechRecognizer(
                    speech_config=self.speech_config, 
                    audio_config=audio_config
                )
                
                result = recognizer.recognize_once()
                
                if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                    logger.info(f"Transcription successful: {len(result.text)} chars")
                    return result.text
                elif result.reason == speechsdk.ResultReason.NoMatch:
                    logger.warning("No speech recognized in audio")
                    return ""
                elif result.reason == speechsdk.ResultReason.Canceled:
                    cancellation_details = result.cancellation_details
                    logger.error(f"Transcription canceled: {cancellation_details.reason}")
                    return ""
                    
            finally:
                try:
                    os.remove(temp_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""
        
        return ""

    async def analyze_audio(self, audio_path: str, reference_text: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyzes audio using Azure Speech SDK.
        Returns transcript, timestamps, and pronunciation scores.
        """
        try:
            audio_config = speechsdk.AudioConfig(filename=audio_path)
            
            # Configure Pronunciation Assessment
            # If reference text is provided, use it. 
            # If not (Spontaneous speech), we might need a different approach or just basic recognition + confidence.
            # Azure Pronunciation Assessment supports "content assessment" (scenarios where text is unknown) in some previews,
            # but standard usage requires reference text.
            # For now, we'll try to use the reference text if available.
            
            pronunciation_config = None
            # Enable Pronunciation Assessment
            # If reference_text is provided, use it.
            # If NOT (None or empty), we use empty string to enable "Unscripted" (Content Assessment) mode
            # which is supported in many regions now.
            
            ref_text_for_config = reference_text if reference_text else ""
            
            pronunciation_config = speechsdk.PronunciationAssessmentConfig(
                reference_text=ref_text_for_config,
                grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
                granularity=speechsdk.PronunciationAssessmentGranularity.Word,
                enable_miscue=True
            )
            
            # Create a recognizer
            recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config, 
                audio_config=audio_config
            )
            
            if pronunciation_config:
                pronunciation_config.apply_to(recognizer)

            # Run recognition (Single shot for short clips, or continuous for longer)
            # Assuming short clips per section for now.
            result = recognizer.recognize_once()
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                response = {
                    "transcript": result.text,
                    "confidence": 0.0, # Will fill below
                    "words": [],
                    "pronunciation_result": None
                }
                
                # Extract Pronunciation Result if available
                # Use try/except because SDK attribute names can vary across versions
                try:
                    pronunciation_result = speechsdk.PronunciationAssessmentResult(result)
                    if pronunciation_result:
                        response["pronunciation_result"] = {
                            "accuracy_score": getattr(pronunciation_result, 'accuracy_score', 0),
                            "fluency_score": getattr(pronunciation_result, 'fluency_score', 0),
                            "completeness_score": getattr(pronunciation_result, 'completeness_score', 0),
                            "pronunciation_score": getattr(pronunciation_result, 'pronunciation_score', 0)
                        }
                except Exception as pron_err:
                    logger.warning(f"Could not get PronunciationAssessmentResult: {pron_err}")
                    # Fallback: extract from JSON if available
                    try:
                        json_result_temp = json.loads(result.json)
                        if 'NBest' in json_result_temp and len(json_result_temp['NBest']) > 0:
                            pa = json_result_temp['NBest'][0].get('PronunciationAssessment', {})
                            response["pronunciation_result"] = {
                                "accuracy_score": pa.get('AccuracyScore', 0),
                                "fluency_score": pa.get('FluencyScore', 0),
                                "completeness_score": pa.get('CompletenessScore', 0),
                                "pronunciation_score": pa.get('PronScore', 0)
                            }
                    except:
                        pass
                
                # Extract detailed word-level timings and confidence if possible
                # Note: Python SDK structure for detailed JSON results:
                # We can parse the JSON result for more details
                json_result = json.loads(result.json)
                response["confidence"] = json_result.get("Confidence", 0.0) # NB: This might be 'NBest' list
                
                # To get word timestamps, we usually need to request it in config
                # The Pronunciation assessment usually returns word details in the object structure, 
                # but let's parse raw JSON for safety if needed, or rely on Azure SDK methods.
                
                # Ideally, we iterate "words" from pronunciation result
                if pronunciation_result:
                     # Accessing word level details from `pronunciation_result` is not directly iterable in all SDK versions?
                     # Let's inspect the json_result['NBest'][0]['Words'] for timestamps
                     if 'NBest' in json_result and len(json_result['NBest']) > 0:
                         words_data = json_result['NBest'][0].get('Words', [])
                         response["words"] = [
                             {
                                 "word": w.get("Word"),
                                 "offset": w.get("Offset"), # In ticks (100 nanoseconds)
                                 "duration": w.get("Duration"),
                                 "accuracy_score": w.get("PronunciationAssessment", {}).get("AccuracyScore")
                             }
                             for w in words_data
                         ]

                return response
                
            elif result.reason == speechsdk.ResultReason.NoMatch:
                logger.warning("No speech could be recognized.")
                return {"error": "No speech recognized", "transcript": ""}
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                logger.error(f"Speech Recognition canceled: {cancellation_details.reason}")
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    logger.error(f"Error details: {cancellation_details.error_details}")
                return {"error": "Recognition canceled", "transcript": ""}
                
        except Exception as e:
            logger.error(f"Azure Speech Analysis Failed: {e}")
            return {"error": str(e), "transcript": ""}
            
        return {"error": "Unknown error", "transcript": ""}

# Create a singleton instance
speech_service = AzureSpeechService()

def get_speech_service() -> AzureSpeechService:
    """Dependency provider for AzureSpeechService"""
    return speech_service
