"""Builders that join a Task to its transcript + patient card for the API."""

from __future__ import annotations

from app.contracts import Patient, Task
from app.seed import REFERENCE_NOW

from .schemas import ApptView, MedView, PatientCard, TaskView


def patient_card(patient: Patient, store) -> PatientCard:
    meds = [
        MedView(medication_name=rx.medication_name, dosage=rx.dosage, instructions=rx.instructions)
        for rx in store.active_prescriptions_for(patient.id)
    ]
    appts = []
    for a in store.future_appointments(patient.id, now=REFERENCE_NOW):
        prov = store.provider(a.provider_id)
        appts.append(ApptView(start_time=a.start_time, provider_name=prov.name if prov else None, status=a.status))
    primary = store.provider(patient.primary_provider_id) if patient.primary_provider_id else None
    return PatientCard(
        id=patient.id,
        full_name=patient.full_name,
        date_of_birth=patient.date_of_birth,
        phone=patient.phone,
        insurance_plan=patient.insurance_plan,
        last_visit=patient.last_visit,
        status=patient.status,
        primary_provider=primary.name if primary else None,
        active_medications=meds,
        upcoming_appointments=appts,
    )


def task_view(task: Task, state) -> TaskView:
    msg = state.messages.get(task.message_id)
    transcript = (msg.transcript or msg.raw_body) if msg else None
    patient = state.store.patient(task.patient_id) if task.patient_id else None
    card = patient_card(patient, state.store) if patient else None
    return TaskView(task=task, transcript=transcript, patient=card)
