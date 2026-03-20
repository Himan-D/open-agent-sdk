"""Text-to-Speech (TTS) engine for voice output."""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import structlog
import base64
import io

logger = structlog.get_logger(__name__)


class TTSEngine(str, Enum):
    """Available TTS engines."""
    GOOGLE = "google"
    AWS_POLLY = "aws_polly"
    AZURE = "azure"
    COQUI = "coqui"
    ESPEAKE = "espeak"  # Offline fallback


@dataclass
class VoiceConfig:
    """Voice configuration."""
    engine: TTSEngine = TTSEngine.ESPEAKE
    voice_id: str = "default"
    language: str = "en-US"
    rate: float = 1.0  # Speech rate multiplier
    pitch: float = 1.0  # Pitch multiplier
    volume: float = 1.0  # Volume (0-1)
    output_format: str = "mp3"  # mp3, wav, ogg


@dataclass
class SpeechResult:
    """Result of TTS generation."""
    audio_data: bytes
    duration_seconds: float
    engine: str
    format: str


class TextToSpeech:
    """Text-to-Speech engine for converting text to audio.
    
    Similar to OpenClaw's voice system for generating
    spoken responses from the agent.
    
    Example:
        >>> tts = TextToSpeech(engine=TTSEngine.ESPEAKE)
        >>> result = await tts.speak("Hello, how can I help you?")
        >>> print(f"Audio duration: {result.duration_seconds}s")
    """

    def __init__(self, config: Optional[VoiceConfig] = None):
        self.config = config or VoiceConfig()
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the TTS engine."""
        if self._initialized:
            return
        
        logger.info("tts_initialized", engine=self.config.engine)
        self._initialized = True

    async def speak(self, text: str) -> SpeechResult:
        """Convert text to speech.
        
        Args:
            text: Text to convert to speech
            
        Returns:
            SpeechResult with audio data
        """
        if not self._initialized:
            self.initialize()
        
        logger.debug("tts_speaking", text_length=len(text), engine=self.config.engine)
        
        if self.config.engine == TTSEngine.ESPEAKE:
            return await self._espeak_tts(text)
        elif self.config.engine == TTSEngine.GOOGLE:
            return await self._google_tts(text)
        elif self.config.engine == TTSEngine.AWS_POLLY:
            return await self._aws_polly_tts(text)
        else:
            return await self._espeak_tts(text)

    async def _espeak_tts(self, text: str) -> SpeechResult:
        """Use espeak for TTS (offline)."""
        try:
            import subprocess
            
            cmd = [
                "espeak",
                "-w", "/tmp/tts_output.wav",
                "-s", str(int(self.config.rate * 100)),
                text
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            if result.returncode == 0:
                with open("/tmp/tts_output.wav", "rb") as f:
                    audio_data = f.read()
                
                return SpeechResult(
                    audio_data=audio_data,
                    duration_seconds=len(audio_data) / 16000,
                    engine="espeak",
                    format="wav",
                )
        except FileNotFoundError:
            logger.warning("espeak_not_installed")
        except Exception as e:
            logger.error("espeak_error", error=str(e))
        
        return SpeechResult(
            audio_data=b"",
            duration_seconds=0.0,
            engine="espeak",
            format="wav",
        )

    async def _google_tts(self, text: str) -> SpeechResult:
        """Use Google Cloud TTS."""
        try:
            from google.cloud import texttospeech
            
            client = texttospeech.TextToSpeechClient()
            
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            voice = texttospeech.VoiceSelectionParams(
                language_code=self.config.language,
                name=self.config.voice_id,
            )
            
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=self.config.rate,
                pitch=self.config.pitch - 1.0,  # Google uses -20 to +20
            )
            
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config,
            )
            
            return SpeechResult(
                audio_data=response.audio_content,
                duration_seconds=len(response.audio_content) / 16000,
                engine="google",
                format="mp3",
            )
        except ImportError:
            logger.warning("google_cloud_not_installed")
        except Exception as e:
            logger.error("google_tts_error", error=str(e))
        
        return await self._espeak_tts(text)

    async def _aws_polly_tts(self, text: str) -> SpeechResult:
        """Use AWS Polly TTS."""
        try:
            import boto3
            
            polly = boto3.client("polly")
            
            response = polly.synthesize_speech(
                Text=text,
                OutputFormat=self.config.output_format.upper(),
                VoiceId=self.config.voice_id,
                Engine="neural" if "neural" in self.config.voice_id else "standard",
            )
            
            audio_stream = response["AudioStream"].read()
            
            return SpeechResult(
                audio_data=audio_stream,
                duration_seconds=len(audio_stream) / 16000,
                engine="aws_polly",
                format=self.config.output_format,
            )
        except ImportError:
            logger.warning("boto3_not_installed")
        except Exception as e:
            logger.error("aws_polly_error", error=str(e))
        
        return await self._espeak_tts(text)

    def get_available_voices(self) -> List[Dict[str, str]]:
        """Get list of available voices for the current engine."""
        default_voices = [
            {"id": "default", "name": "Default", "language": "en-US"},
            {"id": "female", "name": "Female", "language": "en-US"},
            {"id": "male", "name": "Male", "language": "en-US"},
        ]
        
        if self.config.engine == TTSEngine.GOOGLE:
            return [
                {"id": "en-US-Neural2-F", "name": "Neural2 Female", "language": "en-US"},
                {"id": "en-US-Neural2-J", "name": "Neural2 Male", "language": "en-US"},
            ]
        elif self.config.engine == TTSEngine.AWS_POLLY:
            return [
                {"id": "Joanna", "name": "Joanna (Female)", "language": "en-US"},
                {"id": "Matthew", "name": "Matthew (Male)", "language": "en-US"},
            ]
        
        return default_voices


def create_tts_engine(
    engine: str = "espeak",
    voice_id: str = "default",
    language: str = "en-US",
) -> TextToSpeech:
    """Create a TTS engine.
    
    Example:
        >>> tts = create_tts_engine(engine="espeak")
    """
    return TextToSpeech(
        config=VoiceConfig(
            engine=TTSEngine(engine),
            voice_id=voice_id,
            language=language,
        )
    )
