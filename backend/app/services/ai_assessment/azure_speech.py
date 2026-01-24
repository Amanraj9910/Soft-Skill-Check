"""
Azure Speech Service.
Handles Speech-to-Text (STT) and Text-to-Speech (TTS).
"""
import azure.cognitiveservices.speech as speechsdk
from app.config import settings
from .azure_storage import storage_service
import os
import uuid
import tempfile
import asyncio

# Import logging
from app.core.logging import ai_logger, error_logger
from app.core import log_messages

class AzureSpeechService:
    def __init__(self):
        self.speech_config = None
        try:
            self.speech_config = speechsdk.SpeechConfig(
                subscription=settings.AZURE_SPEECH_KEY, 
                region=settings.AZURE_SPEECH_REGION
            )
            self.speech_config.speech_recognition_language = settings.AZURE_SPEECH_LANGUAGE
            self.speech_config.speech_synthesis_voice_name = settings.AZURE_TTS_VOICE_NAME
        except Exception as e:
            error_logger.warning(f"Azure Speech Service initialization warning: {str(e)}")

    def _ensure_configured(self):
        if not self.speech_config:
             raise Exception("Azure Speech keys are missing or invalid. Please check configuration.")

    def transcribe_audio(self, audio_content: bytes) -> str:
        """
        Transcribes audio content to text using Azure Speech SDK.
        Uses a temporary file as the SDK expects a file or pull stream.
        """
        self._ensure_configured()
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                temp_audio.write(audio_content)
                temp_audio_path = temp_audio.name

            audio_config = speechsdk.audio.AudioConfig(filename=temp_audio_path)
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config, 
                audio_config=audio_config
            )

            result = speech_recognizer.recognize_once_async().get()
            
            # Cleanup
            try:
                os.remove(temp_audio_path)
            except:
                pass

            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                return result.text
            elif result.reason == speechsdk.ResultReason.NoMatch:
                ai_logger.warning(log_messages.speech_to_text_failed("No speech could be recognized"))
                return ""
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                ai_logger.error(f"Speech recognition canceled: {cancellation_details.reason} - {cancellation_details.error_details}")
                return ""
                
        except Exception as e:
            error_logger.error(log_messages.speech_to_text_failed(str(e)))
            return ""

    def synthesize_speech(self, text: str) -> str:
        """
        Synthesizes text to speech.
        Uploads the result to Azure Blob Storage and returns the SAS URL.
        """
        self._ensure_configured()
        try:
            # Generate unique filename for the output
            filename = f"tts_{uuid.uuid4()}.wav"
            
            # We need to synthesize to a file or in-memory stream. 
            # Since we want to upload to blob, let's use a temporary file first for simplicity with SDK.
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                temp_audio_path = temp_audio.name
            
            audio_config = speechsdk.audio.AudioConfig(filename=temp_audio_path)
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config, 
                audio_config=audio_config
            )

            result = synthesizer.speak_text_async(text).get()

            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                # Read the file back to upload
                with open(temp_audio_path, "rb") as f:
                    audio_data = f.read()
                
                # Upload to Blob
                blob_name = storage_service.upload_file(audio_data, filename, "audio/wav")
                
                # Cleanup
                try:
                    os.remove(temp_audio_path)
                except:
                    pass
                    
                # Return URL
                return storage_service.generate_sas_url(blob_name)
                
            elif result.reason == speechsdk.ResultReason.Canceled:
                 cancellation_details = result.cancellation_details
                 ai_logger.error(log_messages.text_to_speech_failed(str(cancellation_details.reason)))
                 return None

        except Exception as e:
            error_logger.error(log_messages.text_to_speech_failed(str(e)))
            return None

# Singleton
speech_service = AzureSpeechService()
