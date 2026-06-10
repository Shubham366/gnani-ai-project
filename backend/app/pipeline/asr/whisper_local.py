import asyncio

from ...audio import pcm16_to_float32
from ...config import settings
from ..glossary import ASR_HINT
from .base import ASRProvider


class LocalWhisperASR(ASRProvider):
    def __init__(self) -> None:
        from faster_whisper import WhisperModel

        self.model = WhisperModel(settings.whisper_model, device="cpu", compute_type="int8")

    async def transcribe(self, pcm16: bytes, sample_rate: int) -> str:
        return await asyncio.get_running_loop().run_in_executor(None, self._run, pcm16)

    def _run(self, pcm16: bytes) -> str:
        audio = pcm16_to_float32(pcm16)
        segments, _ = self.model.transcribe(
            audio,
            language="en",
            beam_size=5,
            vad_filter=True,
            condition_on_previous_text=False,
            initial_prompt=f"Glossary: {ASR_HINT}.",
        )
        return " ".join(segment.text.strip() for segment in segments).strip()
