#!/usr/bin/env python3

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TASKS_PATH = ROOT / "mission" / "tasks.json"
EXECUTION_LOG_PATH = ROOT / "mission" / "execution-log.ndjson"
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_tasks() -> dict:
    return json.loads(TASKS_PATH.read_text())


def save_tasks(data: dict) -> None:
    data["updated_at"] = utc_now()
    TASKS_PATH.write_text(json.dumps(data, indent=2) + "\n")


def current_in_progress_task(data: dict) -> dict | None:
    in_progress = [task for task in data.get("tasks", []) if task.get("status") == "in_progress"]
    if not in_progress:
        return None
    in_progress.sort(key=lambda task: task.get("started_at", ""))
    return in_progress[0]


def next_safe_task(data: dict) -> dict | None:
    current = current_in_progress_task(data)
    if current and not current.get("requires_human_review", False) and current.get("safe", False):
        return current

    tasks = data.get("tasks", [])
    pending = [
        task
        for task in tasks
        if task.get("status") == "pending"
        and not task.get("requires_human_review", False)
        and not task.get("blocked_by_human", False)
    ]
    if not pending:
        return None
    pending.sort(key=lambda task: (PRIORITY_RANK.get(task.get("priority"), 99), task.get("id", "")))
    return pending[0]


def find_task(data: dict, task_id: str) -> dict | None:
    for task in data.get("tasks", []):
        if task.get("id") == task_id:
            return task
    return None


def complete_task(task: dict, *, timestamp: str, summary: str) -> None:
    task["status"] = "done"
    task["completed_at"] = timestamp
    task["completion_summary"] = summary


def blocked_tasks(data: dict) -> list[dict]:
    return [task for task in data.get("tasks", []) if task.get("blocked_by_human", False)]


def append_execution_event(event: dict) -> None:
    EXECUTION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with EXECUTION_LOG_PATH.open("a") as handle:
        handle.write(json.dumps(event) + "\n")
