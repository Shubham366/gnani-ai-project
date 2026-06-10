from ..audio import frame_rms
from ..config import settings

FRAME_MS = 30
SPEECH_RMS_THRESHOLD = 0.012


class StreamSegmenter:
    def __init__(self) -> None:
        self.frame_bytes = settings.sample_rate * 2 * FRAME_MS // 1000
        self.silence_frames_needed = settings.silence_ms // FRAME_MS
        self.min_speech_frames = settings.min_speech_ms // FRAME_MS
        self.max_frames = settings.max_utterance_ms // FRAME_MS
        self._pending = bytearray()
        self._utterance = bytearray()
        self._speech_frames = 0
        self._silence_frames = 0
        self._frames_in_utterance = 0
        self._in_speech = False

    def feed(self, chunk: bytes) -> list[bytes]:
        self._pending.extend(chunk)
        finalized: list[bytes] = []
        while len(self._pending) >= self.frame_bytes:
            frame = bytes(self._pending[: self.frame_bytes])
            del self._pending[: self.frame_bytes]
            result = self._feed_frame(frame)
            if result:
                finalized.append(result)
        return finalized

    def flush(self) -> bytes | None:
        return self._finalize()

    def _feed_frame(self, frame: bytes) -> bytes | None:
        is_speech = frame_rms(frame) >= SPEECH_RMS_THRESHOLD
        if is_speech:
            self._in_speech = True
            self._speech_frames += 1
            self._silence_frames = 0
        elif self._in_speech:
            self._silence_frames += 1
        if self._in_speech:
            self._utterance.extend(frame)
            self._frames_in_utterance += 1
        if self._in_speech and (
            self._silence_frames >= self.silence_frames_needed
            or self._frames_in_utterance >= self.max_frames
        ):
            return self._finalize()
        return None

    def _finalize(self) -> bytes | None:
        utterance = bytes(self._utterance)
        had_enough_speech = self._speech_frames >= self.min_speech_frames
        self._utterance.clear()
        self._speech_frames = 0
        self._silence_frames = 0
        self._frames_in_utterance = 0
        self._in_speech = False
        if had_enough_speech and utterance:
            return utterance
        return None
