from __future__ import annotations

import base64
from typing import Optional

from app.config import settings
from app.services.speech.language_selector import (
    detect_user_language,
    get_voice_for_language,
)

from elevenlabs.client import ElevenLabs



class TTSService:
    def __init__(self) -> None:
        self.enabled = bool(settings.TTS_API_KEY)
        
        if self.enabled:
            self.client = ElevenLabs(api_key=settings.TTS_API_KEY)
        else:
            self.client = None

    def is_enabled(self) -> bool:
        return self.enabled

    def text_to_speech_base64(self, text: str) -> Optional[str]:
        if not self.enabled or not self.client:
            return None
        
        lang = detect_user_language(text)
        voice_id = get_voice_for_language(lang)

        audio_stream = self.client.text_to_speech.convert(
            # voice_id=settings.TTS_VOICE_ID,
            voice_id=voice_id,
            model_id=settings.TTS_VOICE_MODEL_ID,
            text=text,
        )
        audio_bytes = b"".join(audio_stream)
        return base64.b64encode(audio_bytes).decode("utf-8")