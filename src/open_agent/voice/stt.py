"""Speech-to-Text (STT) engine for voice input."""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


class STTEngine(str, Enum):
    """Available STT engines."""
    GOOGLE = "google"
    WHISPER = "whisper"
    AWS_TRANSCRIBE = "aws_transcribe"
    AZURE = "azure"
    DEEPGRAM = "deepgram"
    SPHINX = "sphinx"  # Offline fallback (CMU)


@dataclass
class STTConfig:
    """Speech-to-Text configuration."""
    engine: STTEngine = STTEngine.SPHINX
    language: str = "en-US"
    model: str = "base"  # For whisper: tiny, base, small, medium, large
    sample_rate: int = 16000
    enable_punctuation: bool = True
    enable_profanity_filter: bool = False


@dataclass  
class TranscriptionResult:
    """Result of speech transcription."""
    text: str
    confidence: float
    language: str
    engine: str
    duration_seconds: float
    words: List[Dict[str, Any]]  # Word-level timestamps


class SpeechToText:
    """Speech-to-Text engine for converting audio to text.
    
    Similar to OpenClaw's voice system for processing
    voice input from users.
    
    Example:
        >>> stt = SpeechToText(engine=STTEngine.SPHINX)
        >>> result = await stt.listen(audio_data)
        >>> print(f"You said: {result.text}")
    """

    def __init__(self, config: Optional[STTConfig] = None):
        self.config = config or STTConfig()
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the STT engine."""
        if self._initialized:
            return
        
        logger.info("stt_initialized", engine=self.config.engine)
        self._initialized = True

    async def listen(self, audio_data: bytes) -> TranscriptionResult:
        """Transcribe audio data to text.
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            TranscriptionResult with transcribed text
        """
        if not self._initialized:
            self.initialize()
        
        logger.debug("stt_listening", audio_size=len(audio_data), engine=self.config.engine)
        
        if self.config.engine == STTEngine.SPHINX:
            return await self._sphinx_stt(audio_data)
        elif self.config.engine == STTEngine.WHISPER:
            return await self._whisper_stt(audio_data)
        elif self.config.engine == STTEngine.GOOGLE:
            return await self._google_stt(audio_data)
        elif self.config.engine == STTEngine.DEEPGRAM:
            return await self._deepgram_stt(audio_data)
        else:
            return await self._sphinx_stt(audio_data)

    async def _sphinx_stt(self, audio_data: bytes) -> TranscriptionResult:
        """Use CMU Sphinx for offline STT."""
        try:
            import speech_recognition
            
            recognizer = speech_recognition.Recognizer()
            
            import io
            import wave
            
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(self.config.sample_rate)
                wav_file.writeframes(audio_data)
            
            wav_buffer.seek(0)
            
            with speech_recognition.AudioFile(wav_buffer) as source:
                audio = recognizer.record(source)
            
            text = recognizer.recognize_sphinx(audio)
            
            return TranscriptionResult(
                text=text,
                confidence=0.8,
                language=self.config.language,
                engine="sphinx",
                duration_seconds=len(audio_data) / self.config.sample_rate,
                words=[],
            )
        except ImportError:
            logger.warning("speech_recognition_not_installed")
        except Exception as e:
            logger.error("sphinx_error", error=str(e))
        
        return TranscriptionResult(
            text="",
            confidence=0.0,
            language=self.config.language,
            engine="sphinx",
            duration_seconds=0.0,
            words=[],
        )

    async def _whisper_stt(self, audio_data: bytes) -> TranscriptionResult:
        """Use OpenAI Whisper for STT."""
        try:
            import whisper
            import numpy as np
            import torch
            
            model = whisper.load_model(self.config.model)
            
            import io
            import wave
            import numpy as np
            
            wav_buffer = io.BytesIO(audio_data)
            with wave.open(wav_buffer, 'rb') as wav_file:
                sample_rate = wav_file.getframerate()
                frames = wav_file.readframes(-1)
                audio_np = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
            
            result = model.transcribe(
                audio_np,
                language=self.config.language.split("-")[0],
                fp16=torch.cuda.is_available(),
            )
            
            words = []
            if "words" in result:
                words = [
                    {"word": w["word"], "start": w["start"], "end": w["end"]}
                    for w in result["words"]
                ]
            
            return TranscriptionResult(
                text=result["text"],
                confidence=result.get("probability", 0.9),
                language=self.config.language,
                engine="whisper",
                duration_seconds=result.get("duration", 0.0),
                words=words,
            )
        except ImportError:
            logger.warning("openai_whisper_not_installed")
        except Exception as e:
            logger.error("whisper_error", error=str(e))
        
        return await self._sphinx_stt(audio_data)

    async def _google_stt(self, audio_data: bytes) -> TranscriptionResult:
        """Use Google Cloud Speech-to-Text."""
        try:
            from google.cloud import speech
            
            client = speech.SpeechClient()
            
            audio = speech.RecognitionAudio(content=audio_data)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=self.config.sample_rate,
                language_code=self.config.language,
                enable_automatic_punctuation=self.config.enable_punctuation,
            )
            
            response = client.recognize(config=config, audio=audio)
            
            if response.results:
                result = response.results[0]
                alternatives = result.alternatives
                
                if alternatives:
                    best = alternatives[0]
                    return TranscriptionResult(
                        text=best.transcript,
                        confidence=best.confidence,
                        language=self.config.language,
                        engine="google",
                        duration_seconds=0.0,
                        words=[],
                    )
            
            return TranscriptionResult(
                text="",
                confidence=0.0,
                language=self.config.language,
                engine="google",
                duration_seconds=0.0,
                words=[],
            )
        except ImportError:
            logger.warning("google_cloud_not_installed")
        except Exception as e:
            logger.error("google_stt_error", error=str(e))
        
        return await self._sphinx_stt(audio_data)

    async def _deepgram_stt(self, audio_data: bytes) -> TranscriptionResult:
        """Use Deepgram for STT."""
        try:
            import os
            import httpx
            
            api_key = os.environ.get("DEEPGRAM_API_KEY")
            if not api_key:
                logger.warning("DEEPGRAM_API_KEY_not_set")
                return await self._sphinx_stt(audio_data)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.deepgram.com/v1/listen",
                    headers={"Authorization": f"Token {api_key}"},
                    params={
                        "language": self.config.language.split("-")[0],
                        "punctuate": self.config.enable_punctuation,
                    },
                    content=audio_data,
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    result = data["results"]["channels"][0]["alternatives"][0]
                    
                    return TranscriptionResult(
                        text=result["transcript"],
                        confidence=0.9,
                        language=self.config.language,
                        engine="deepgram",
                        duration_seconds=0.0,
                        words=[],
                    )
        except ImportError:
            logger.warning("httpx_not_installed")
        except Exception as e:
            logger.error("deepgram_error", error=str(e))
        
        return await self._sphinx_stt(audio_data)

    def get_available_engines(self) -> List[Dict[str, str]]:
        """Get list of available STT engines."""
        return [
            {"id": "sphinx", "name": "CMU Sphinx", "offline": "true"},
            {"id": "whisper", "name": "OpenAI Whisper", "offline": "true"},
            {"id": "google", "name": "Google Cloud", "offline": "false"},
            {"id": "deepgram", "name": "Deepgram", "offline": "false"},
        ]


def create_stt_engine(
    engine: str = "sphinx",
    language: str = "en-US",
) -> SpeechToText:
    """Create an STT engine.
    
    Example:
        >>> stt = create_stt_engine(engine="sphinx")
    """
    return SpeechToText(
        config=STTConfig(
            engine=STTEngine(engine),
            language=language,
        )
    )
