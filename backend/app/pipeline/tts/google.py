import asyncio
import io

from gtts import gTTS

from .base import TTSProvider


class GoogleTTS(TTSProvider):
    async def synthesize(self, hindi_text: str) -> bytes:
        return await asyncio.get_running_loop().run_in_executor(None, self._run, hindi_text)

    def _run(self, hindi_text: str) -> bytes:
        buf = io.BytesIO()
        gTTS(text=hindi_text, lang="hi").write_to_fp(buf)
        return buf.getvalue()
