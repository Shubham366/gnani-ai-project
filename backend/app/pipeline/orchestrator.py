import asyncio
import base64
import logging
import time
from collections.abc import Awaitable, Callable

from ..config import settings
from .asr import create_asr
from .text_cleanup import is_meaningful, remove_fillers
from .translation import create_translator
from .tts import create_tts

logger = logging.getLogger(__name__)

Emit = Callable[[dict], Awaitable[None]]


class TranslationSession:
    def __init__(self, emit: Emit) -> None:
        self.emit = emit
        self.asr = create_asr()
        self.translator = create_translator()
        self.tts = create_tts()
        self.tone = settings.default_tone
        self.generation = 0
        self._tasks: set[asyncio.Task] = set()

    def set_tone(self, tone: str) -> None:
        if tone in ("formal", "casual"):
            self.tone = tone

    def barge_in(self) -> None:
        self.generation += 1
        for task in self._tasks:
            task.cancel()

    def submit_utterance(self, pcm16: bytes) -> None:
        task = asyncio.create_task(self._process(pcm16, self.generation))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    def close(self) -> None:
        for task in self._tasks:
            task.cancel()

    async def _process(self, pcm16: bytes, generation: int) -> None:
        try:
            await self._run_pipeline(pcm16, generation)
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.exception("pipeline error")
            await self.emit({"type": "error", "message": str(exc)})

    async def _run_pipeline(self, pcm16: bytes, generation: int) -> None:
        started = time.perf_counter()

        transcript = await self.asr.transcribe(pcm16, settings.sample_rate)
        asr_ms = self._elapsed_ms(started)
        if self._stale(generation):
            return

        cleaned = remove_fillers(transcript)
        if not is_meaningful(cleaned):
            return
        await self.emit({"type": "transcript", "text": cleaned, "raw": transcript})

        translate_started = time.perf_counter()
        hindi = await self.translator.translate(cleaned, self.tone)
        translate_ms = self._elapsed_ms(translate_started)
        if self._stale(generation) or not hindi:
            return
        await self.emit({"type": "translation", "text": hindi})

        tts_started = time.perf_counter()
        audio = await self.tts.synthesize(hindi)
        tts_ms = self._elapsed_ms(tts_started)
        if self._stale(generation):
            return

        await self.emit(
            {
                "type": "audio",
                "format": "mp3",
                "data": base64.b64encode(audio).decode("ascii"),
                "latency_ms": {
                    "asr": asr_ms,
                    "translation": translate_ms,
                    "tts": tts_ms,
                    "total": self._elapsed_ms(started),
                },
            }
        )

    def _stale(self, generation: int) -> bool:
        return generation != self.generation

    @staticmethod
    def _elapsed_ms(since: float) -> int:
        return int((time.perf_counter() - since) * 1000)
