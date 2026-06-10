from ...config import settings
from .base import TranslationProvider
from .prompts import system_prompt


class LLMTranslator(TranslationProvider):
    def __init__(self, provider: str) -> None:
        self.provider = provider
        if provider == "gemini":
            from google import genai

            self.client = genai.Client(api_key=settings.gemini_api_key)
            self.model = settings.translation_model or settings.gemini_model
        else:
            from openai import AsyncOpenAI

            if provider == "grok":
                self.client = AsyncOpenAI(
                    api_key=settings.grok_api_key, base_url=settings.grok_base_url
                )
                self.model = settings.translation_model or settings.grok_model
            else:
                self.client = AsyncOpenAI(api_key=settings.openai_api_key)
                self.model = settings.translation_model or "gpt-4o-mini"

    async def translate(self, text: str, tone: str) -> str:
        if self.provider == "gemini":
            return await self._translate_gemini(text, tone)
        return await self._translate_openai_compatible(text, tone)

    async def _translate_gemini(self, text: str, tone: str) -> str:
        from google.genai import types

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=text,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt(tone),
                temperature=0.2,
            ),
        )
        return (response.text or "").strip()

    async def _translate_openai_compatible(self, text: str, tone: str) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt(tone)},
                {"role": "user", "content": text},
            ],
        )
        return (response.choices[0].message.content or "").strip()
