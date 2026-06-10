from abc import ABC, abstractmethod


class TranslationProvider(ABC):
    @abstractmethod
    async def translate(self, text: str, tone: str) -> str: ...
