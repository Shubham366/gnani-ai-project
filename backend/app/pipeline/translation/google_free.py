import asyncio

from .. import glossary
from ..text_cleanup import ABBREVIATIONS, localize_times
from .base import TranslationProvider


class GoogleFreeTranslator(TranslationProvider):
    def __init__(self) -> None:
        from deep_translator import GoogleTranslator

        self.engine = GoogleTranslator(source="en", target="hi")

    async def translate(self, text: str, tone: str) -> str:
        protected, placeholders = glossary.protect(text)
        translated = await asyncio.get_running_loop().run_in_executor(
            None, self.engine.translate, protected
        )
        translated = glossary.restore(translated or "", placeholders)
        translated = localize_times(translated)
        for abbr, hindi in ABBREVIATIONS.items():
            translated = translated.replace(abbr, hindi)
        return translated.strip()
