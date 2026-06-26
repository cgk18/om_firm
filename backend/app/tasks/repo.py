"""In-memory task store for the demo. Created at startup, lives for the session,
resets clean on restart — no external DB.

Behind this small interface so a real persistence layer (a fresh Postgres at
pilot time, our schema) can drop in without touching the pipeline.
"""

from __future__ import annotations

from app.contracts import Task


class TasksRepo:
    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}

    def add(self, task: Task) -> Task:
        self._tasks[task.id] = task
        return task

    def add_all(self, tasks: list[Task]) -> list[Task]:
        for t in tasks:
            self.add(t)
        return tasks

    def get(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    def list(self) -> list[Task]:
        """All tasks, newest first."""
        return sorted(self._tasks.values(), key=lambda t: t.created_at, reverse=True)
