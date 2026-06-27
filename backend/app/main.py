"""Demo API — a thin FastAPI layer over the in-memory pipeline.

Run:  cd backend && .venv/bin/uvicorn app.main:app --reload

On startup the queue is pre-seeded from the demo voicemails using the CANNED
extractor (offline, free, instant). `POST /ingest` runs the REAL Claude intake on
a pasted transcript — the "watch the AI work" moment. `POST /reset` rebuilds the
queue (handy between filming takes).

All pipeline time math uses REFERENCE_NOW (the demo's "today") so seeded and
live-ingested tasks stay coherent. Demo only: in-memory, single user, CORS open.
"""

from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware

try:
    from dotenv import find_dotenv, load_dotenv

    load_dotenv(find_dotenv(usecwd=True))  # so /ingest finds ANTHROPIC_API_KEY
except ImportError:
    pass

from app.api.schemas import DecisionRequest, IngestRequest, PatientCard, TaskView
from app.api.views import patient_card, task_view
from app.contracts import Channel, Message, default_policy
from app.eval.golden import canned_extract
from app.pipeline.intake import extract_intent
from app.pipeline.transcription import transcribe_audio
from app.scheduling import HoldStore
from app.seed import REFERENCE_NOW, SeedStore, load_messages
from app.tasks import TasksRepo, apply_decision, intake_to_tasks


class AppState:
    """In-memory demo state. Messages are kept so the API can join transcripts."""

    def __init__(self) -> None:
        self.store = SeedStore()
        self.policy = default_policy()
        self.repo = TasksRepo()
        self.holds = HoldStore()
        self.messages: dict[str, Message] = {}
        self.audio: dict[str, tuple[bytes, str]] = {}  # message_id -> (bytes, content_type)

    def ingest(self, message: Message, *, extract):
        self.messages[message.id] = message
        return intake_to_tasks(
            message, repo=self.repo, store=self.store, policy=self.policy,
            now=REFERENCE_NOW, holds=self.holds, extract=extract,
        )

    def seed(self) -> None:
        for m in load_messages():
            self.ingest(m, extract=canned_extract)


state = AppState()
state.seed()

app = FastAPI(title="om_firm demo API")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


@app.get("/tasks", response_model=list[TaskView])
def list_tasks(status: str | None = None, type: str | None = None):
    tasks = state.repo.list()
    if status:
        tasks = [t for t in tasks if t.status.value == status]
    if type:
        tasks = [t for t in tasks if t.type.value == type]
    return [task_view(t, state) for t in tasks]


@app.get("/tasks/{task_id}", response_model=TaskView)
def get_task(task_id: str):
    t = state.repo.get(task_id)
    if t is None:
        raise HTTPException(404, "task not found")
    return task_view(t, state)


@app.post("/tasks/{task_id}/decision", response_model=TaskView)
def decide(task_id: str, body: DecisionRequest):
    try:
        t = apply_decision(
            state.repo, task_id, body.decision,
            note=body.note, reviewer=body.reviewer, edited_text=body.edited_text,
            holds=state.holds,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    if t is None:
        raise HTTPException(404, "task not found")
    return task_view(t, state)


@app.get("/patients/{patient_id}", response_model=PatientCard)
def get_patient(patient_id: str):
    p = state.store.patient(patient_id)
    if p is None:
        raise HTTPException(404, "patient not found")
    return patient_card(p, state.store)


@app.post("/ingest", response_model=list[TaskView])
def ingest(body: IngestRequest):
    """Live: run the REAL Claude intake on a pasted transcript -> new task(s)."""
    msg = Message(
        channel=Channel(body.channel),
        received_at=REFERENCE_NOW,
        transcript=body.transcript,
        raw_body=body.transcript if body.channel == "email" else None,
    )
    try:
        tasks = state.ingest(msg, extract=extract_intent)
    except Exception as e:  # noqa: BLE001 - surface intake/LLM failures cleanly
        raise HTTPException(502, f"intake failed: {e}")
    return [task_view(t, state) for t in tasks]


@app.post("/ingest/audio", response_model=list[TaskView])
def ingest_audio(file: UploadFile = File(...)):
    """Live voicemail: upload audio -> Deepgram transcribe -> real Claude intake ->
    new task(s), with the audio kept for playback. The full hero moment."""
    audio = file.file.read()
    try:
        transcript = transcribe_audio(audio)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, f"transcription failed: {e}")
    msg = Message(channel=Channel.voicemail, received_at=REFERENCE_NOW, transcript=transcript)
    msg.raw_ref = f"/audio/{msg.id}"
    state.audio[msg.id] = (audio, file.content_type or "audio/wav")
    try:
        tasks = state.ingest(msg, extract=extract_intent)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, f"intake failed: {e}")
    return [task_view(t, state) for t in tasks]


@app.get("/audio/{message_id}")
def get_audio(message_id: str):
    item = state.audio.get(message_id)
    if item is None:
        raise HTTPException(404, "audio not found")
    data, content_type = item
    return Response(content=data, media_type=content_type)


@app.post("/reset")
def reset():
    """Rebuild the demo queue from scratch (handy between filming takes)."""
    global state
    state = AppState()
    state.seed()
    return {"tasks": len(state.repo.list())}
