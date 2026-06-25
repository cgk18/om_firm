from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from .enums import Channel


class Message(BaseModel):
    """A raw inbound patient message — the pipeline's entry point.

    For voicemail, `raw_ref` points at the audio and `transcript` is filled by
    the transcription stage. For email, `raw_body` holds the text and is copied
    into `transcript` so every downstream stage reads one field.
    """

    id: str = Field(default_factory=lambda: uuid4().hex)
    channel: Channel
    received_at: datetime
    raw_ref: str | None = None
    raw_body: str | None = None
    transcript: str | None = None
    stt_meta: dict[str, Any] = Field(default_factory=dict)
