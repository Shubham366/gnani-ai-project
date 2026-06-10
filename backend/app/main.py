import json
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from .config import settings
from .pipeline.orchestrator import TranslationSession
from .pipeline.segmenter import StreamSegmenter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="EN to HI Voice Translation Pipeline")


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "asr": settings.asr_provider,
        "translation": settings.translation_provider,
        "tts": settings.tts_provider,
    }


@app.websocket("/ws")
async def translate_stream(websocket: WebSocket) -> None:
    await websocket.accept()

    async def emit(message: dict) -> None:
        await websocket.send_text(json.dumps(message))

    session = TranslationSession(emit)
    segmenter = StreamSegmenter()
    await emit({"type": "ready", "tone": session.tone})

    try:
        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                break
            if message.get("bytes") is not None:
                for utterance in segmenter.feed(message["bytes"]):
                    session.submit_utterance(utterance)
            elif message.get("text"):
                await handle_control(json.loads(message["text"]), session, segmenter)
    except WebSocketDisconnect:
        pass
    finally:
        session.close()


async def handle_control(
    control: dict, session: TranslationSession, segmenter: StreamSegmenter
) -> None:
    kind = control.get("type")
    if kind == "config":
        session.set_tone(control.get("tone", session.tone))
    elif kind == "barge_in":
        session.barge_in()
    elif kind == "flush":
        utterance = segmenter.flush()
        if utterance:
            session.submit_utterance(utterance)
