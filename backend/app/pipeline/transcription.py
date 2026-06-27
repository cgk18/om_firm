"""Transcription stage — Deepgram STT: audio bytes -> transcript text.

The hero-path entry point: a recorded voicemail comes in, this turns it into the
transcript the rest of the pipeline already runs on (intake -> orchestrator -> …).

Uses the `nova-3-medical` model — medical-tuned, so it gets drug names right
(Lisinopril, Atorvastatin) and smart-formats dates/numbers. `client` is injectable
for tests.
"""

from __future__ import annotations

import os
from typing import Any

DEEPGRAM_MODEL = "nova-3-medical"


def _default_client() -> Any:
    from deepgram import DeepgramClient

    key = os.getenv("DEEPGRAM_API_KEY")
    if not key:
        raise RuntimeError("DEEPGRAM_API_KEY is not set")
    return DeepgramClient(api_key=key)


def transcribe_audio(audio: bytes, *, client: Any | None = None, model: str = DEEPGRAM_MODEL) -> str:
    """Transcribe raw audio bytes (wav/mp3/m4a/flac …) to text."""
    if client is None:
        client = _default_client()
    resp = client.listen.v1.media.transcribe_file(
        request=audio, model=model, smart_format=True, punctuate=True
    )
    return resp.results.channels[0].alternatives[0].transcript.strip()
