import io

from openai import AsyncOpenAI

from ...audio import pcm16_to_wav
from ...config import settings
from ..glossary import ASR_HINT
from .base import ASRProvider


class GrokASR(ASRProvider):
    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.grok_api_key, base_url=settings.grok_base_url)

    async def transcribe(self, pcm16: bytes, sample_rate: int) -> str:
        wav = io.BytesIO(pcm16_to_wav(pcm16, sample_rate))
        wav.name = "utterance.wav"
        result = await self.client.audio.transcriptions.create(
            model="whisper-1",
            file=wav,
            language="en",
            prompt=f"Glossary: {ASR_HINT}.",
        )
        return result.text.strip()
