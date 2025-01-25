from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import play
from app.core.logging import LoggerMixin
import os
import io

load_dotenv()

class TTSService(LoggerMixin):
    def __init__(self):
        self.api_key = os.getenv("ELEVEN_LABS_API_KEY")
        if not self.api_key:
            self.logger.error("ELEVEN_LABS_API_KEY not found in environment variables")
            raise ValueError("ELEVEN_LABS_API_KEY is required")
            
        self.client = ElevenLabs(api_key=self.api_key)

    def convert_text_to_speech(self, text: str) -> bytes:
        """Convert text to speech using ElevenLabs"""
        audio_stream = self.client.text_to_speech.convert(
            text=text,
            voice_id="JBFqnCBsd6RMkjVDRZzb",
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
        )
        
        # Convert the generator to bytes
        buffer = io.BytesIO()
        for chunk in audio_stream:
            buffer.write(chunk)
        return buffer.getvalue()
