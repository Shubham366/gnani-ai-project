import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


def _env_int(key: str, default: int) -> int:
    raw = _env(key)
    return int(raw) if raw else default


@dataclass(frozen=True)
class Settings:
    asr_provider: str = field(default_factory=lambda: _env("ASR_PROVIDER", "whisper_local"))
    translation_provider: str = field(default_factory=lambda: _env("TRANSLATION_PROVIDER", "google_free"))
    tts_provider: str = field(default_factory=lambda: _env("TTS_PROVIDER", "edge"))

    whisper_model: str = field(default_factory=lambda: _env("WHISPER_MODEL", "base.en"))

    openai_api_key: str = field(default_factory=lambda: _env("OPENAI_API_KEY"))
    gemini_api_key: str = field(default_factory=lambda: _env("GEMINI_API_KEY"))
    grok_api_key: str = field(default_factory=lambda: _env("GROK_API_KEY"))
    grok_base_url: str = field(default_factory=lambda: _env("GROK_BASE_URL", "https://api.x.ai/v1"))

    translation_model: str = field(default_factory=lambda: _env("TRANSLATION_MODEL"))
    gemini_model: str = field(default_factory=lambda: _env("GEMINI_MODEL", "gemini-2.0-flash"))
    grok_model: str = field(default_factory=lambda: _env("GROK_MODEL", "grok-3-mini"))

    tts_voice: str = field(default_factory=lambda: _env("TTS_VOICE", "hi-IN-SwaraNeural"))
    default_tone: str = field(default_factory=lambda: _env("DEFAULT_TONE", "formal"))

    sample_rate: int = field(default_factory=lambda: _env_int("SAMPLE_RATE", 16000))
    silence_ms: int = field(default_factory=lambda: _env_int("SILENCE_MS", 700))
    min_speech_ms: int = field(default_factory=lambda: _env_int("MIN_SPEECH_MS", 300))
    max_utterance_ms: int = field(default_factory=lambda: _env_int("MAX_UTTERANCE_MS", 15000))


settings = Settings()
