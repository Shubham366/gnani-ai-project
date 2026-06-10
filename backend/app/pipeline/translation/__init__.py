from ...config import settings
from .base import TranslationProvider


def create_translator() -> TranslationProvider:
    provider = settings.translation_provider
    if provider in ("gemini", "openai", "grok"):
        from .llm import LLMTranslator

        return LLMTranslator(provider)
    if provider == "google_free":
        from .google_free import GoogleFreeTranslator

        return GoogleFreeTranslator()
    raise ValueError(f"Unknown translation provider: {provider}")
