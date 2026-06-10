from ...config import settings
from .base import ASRProvider


def create_asr() -> ASRProvider:
    provider = settings.asr_provider
    if provider == "whisper_local":
        from .whisper_local import LocalWhisperASR

        return LocalWhisperASR()
    if provider == "whisper_api":
        from .whisper_api import WhisperAPIASR

        return WhisperAPIASR()
    if provider == "gemini":
        from .gemini import GeminiASR

        return GeminiASR()
    if provider == "grok":
        from .grok import GrokASR

        return GrokASR()
    raise ValueError(f"Unknown ASR provider: {provider}")
