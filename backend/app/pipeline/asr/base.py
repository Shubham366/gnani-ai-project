from abc import ABC, abstractmethod


class ASRProvider(ABC):
    @abstractmethod
    async def transcribe(self, pcm16: bytes, sample_rate: int) -> str: ...
