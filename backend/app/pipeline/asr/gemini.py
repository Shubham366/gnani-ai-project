from google import genai
from google.genai import types

from ...audio import pcm16_to_wav
from ...config import settings
from ..glossary import ASR_HINT
from .base import ASRProvider

PROMPT = (
    "Transcribe this English audio exactly as spoken. "
    f"These terms may appear and must be spelled exactly: {ASR_HINT}. "
    "Return only the transcript text, nothing else."
)


class GeminiASR(ASRProvider):
    def __init__(self) -> None:
        self.client = genai.Client(api_key=settings.gemini_api_key)

    async def transcribe(self, pcm16: bytes, sample_rate: int) -> str:
        wav = pcm16_to_wav(pcm16, sample_rate)
        response = await self.client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=[
                PROMPT,
                types.Part.from_bytes(data=wav, mime_type="audio/wav"),
            ],
        )
        return (response.text or "").strip()
