"""
Voice module - placeholder for server-side TTS/STT integration.
Currently unused per BUILD_SPEC U-05 decision (no server voice).
This module is kept for future use if U-05 is approved.
"""

from typing import Dict, Any, Optional


class VoiceProvider:
    """
    Abstract voice provider interface.
    Would be implemented with ElevenLabs or similar if U-05 is approved.
    """

    def text_to_speech(self, text: str, lang: str = "en") -> bytes:
        """Convert text to speech audio bytes."""
        raise NotImplementedError("Server-side TTS not enabled (U-05)")

    def speech_to_text(self, audio: bytes, lang: str = "en") -> str:
        """Convert speech audio to text."""
        raise NotImplementedError("Server-side STT not enabled (U-05)")
