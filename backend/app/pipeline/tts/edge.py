import edge_tts

from ...config import settings
from .base import TTSProvider


class EdgeTTS(TTSProvider):
    async def synthesize(self, hindi_text: str) -> bytes:
        communicate = edge_tts.Communicate(hindi_text, settings.tts_voice)
        audio = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio.extend(chunk["data"])
        return bytes(audio)
