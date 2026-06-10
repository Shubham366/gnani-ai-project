from ...config import settings
from .base import TTSProvider


def create_tts() -> TTSProvider:
    provider = settings.tts_provider
    if provider == "edge":
        from .edge import EdgeTTS

        return EdgeTTS()
    if provider == "gtts":
        from .google import GoogleTTS

        return GoogleTTS()
    raise ValueError(f"Unknown TTS provider: {provider}")
