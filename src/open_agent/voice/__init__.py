"""Voice module - Text-to-Speech and Speech-to-Text capabilities.

This module provides voice functionality similar to OpenClaw:
- Text-to-Speech (TTS) for agent responses
- Speech-to-Text (STT) for voice input
- Voice configuration and settings
"""

from open_agent.voice.tts import (
    TextToSpeech, TTSEngine, VoiceConfig, SpeechResult, create_tts_engine
)
from open_agent.voice.stt import (
    SpeechToText, STTEngine, STTConfig, TranscriptionResult, create_stt_engine
)

__all__ = [
    "TextToSpeech",
    "TTSEngine",
    "VoiceConfig",
    "SpeechResult",
    "create_tts_engine",
    "SpeechToText",
    "STTEngine",
    "STTConfig",
    "TranscriptionResult",
    "create_stt_engine",
]
