from abc import ABC, abstractmethod


class TTSProvider(ABC):
    @abstractmethod
    async def synthesize(self, hindi_text: str) -> bytes: ...
