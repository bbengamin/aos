#!/usr/bin/env python3

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TASKS_PATH = ROOT / "mission" / "tasks.json"
EXECUTION_LOG_PATH = ROOT / "mission" / "execution-log.ndjson"
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}
AUTO_TASK_PREFIX = "AUTO"
STALE_IN_PROGRESS_SECONDS = 24 * 60 * 60
LONG_BLOCKED_SECONDS = 72 * 60 * 60


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_utc_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def age_seconds(value: str | None, *, now: datetime | None = None) -> int | None:
    timestamp = parse_utc_timestamp(value)
    if timestamp is None:
        return None
    reference = now or datetime.now(timezone.utc)
    return max(0, int((reference - timestamp).total_seconds()))


def format_age(seconds: int | None) -> str | None:
    if seconds is None:
        return None
    hours = seconds // 3600
    if hours < 48:
        return f"{hours}h"
    return f"{hours // 24}d"


def load_tasks() -> dict:
    return json.loads(TASKS_PATH.read_text())


def load_execution_events() -> list[dict]:
    if not EXECUTION_LOG_PATH.exists():
        return []
    return [json.loads(line) for line in EXECUTION_LOG_PATH.read_text().splitlines() if line.strip()]


def save_tasks(data: dict) -> None:
    data["updated_at"] = utc_now()
    TASKS_PATH.write_text(json.dumps(data, indent=2) + "\n")


def current_in_progress_task(data: dict) -> dict | None:
    in_progress = [task for task in data.get("tasks", []) if task.get("status") == "in_progress"]
    if not in_progress:
        return None
    in_progress.sort(key=lambda task: task.get("started_at", ""))
    return in_progress[0]


def task_is_done(task: dict) -> bool:
    return task.get("status") == "done"


def dependency_titles(task: dict) -> list[str]:
    return [title for title in task.get("dependency_titles", []) if title]


def dependency_task_ids(task: dict) -> list[str]:
    return [task_id for task_id in task.get("depends_on_task_ids", []) if task_id]


def unresolved_dependency_ids(task: dict, data: dict) -> list[str]:
    unresolved = []
    for dependency_id in dependency_task_ids(task):
        dependency = find_task(data, dependency_id)
        if dependency is None or not task_is_done(dependency):
            unresolved.append(dependency_id)
    return unresolved


def task_is_dependency_blocked(task: dict, data: dict) -> bool:
    return bool(unresolved_dependency_ids(task, data))


def next_safe_task(data: dict) -> dict | None:
    current = current_in_progress_task(data)
    if (
        current
        and not current.get("requires_human_review", False)
        and current.get("safe", False)
        and not current.get("blocked_by_human", False)
        and not task_is_dependency_blocked(current, data)
    ):
        return current

    tasks = data.get("tasks", [])
    pending = [
        task
        for task in tasks
        if task.get("status") == "pending"
        and not task.get("requires_human_review", False)
        and not task.get("blocked_by_human", False)
        and not task_is_dependency_blocked(task, data)
    ]
    if not pending:
        return None
    pending.sort(key=lambda task: (PRIORITY_RANK.get(task.get("priority"), 99), task.get("id", "")))
    return pending[0]


def has_executable_safe_task(data: dict) -> bool:
    return next_safe_task(data) is not None


def executable_safe_task_count(data: dict) -> int:
    current = current_in_progress_task(data)
    count = 0
    if current and not current.get("requires_human_review", False) and current.get("safe", False):
        count += 1
    count += len(pending_safe_tasks(data))
    return count


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


def review_waiting_tasks(data: dict) -> list[dict]:
    return [
        task
        for task in data.get("tasks", [])
        if task.get("status") == "pending" and task.get("requires_human_review", False)
    ]


def is_stale_in_progress_task(task: dict, *, now: datetime | None = None) -> bool:
    if task.get("status") != "in_progress":
        return False
    age = age_seconds(task.get("started_at"), now=now)
    return age is not None and age >= STALE_IN_PROGRESS_SECONDS


def is_long_blocked_task(task: dict, *, now: datetime | None = None) -> bool:
    if not task.get("blocked_by_human", False):
        return False
    age = age_seconds(task.get("blocked_at"), now=now)
    return age is not None and age >= LONG_BLOCKED_SECONDS


def pending_unblocked_tasks(data: dict) -> list[dict]:
    return [
        task
        for task in data.get("tasks", [])
        if task.get("status") == "pending"
        and not task.get("blocked_by_human", False)
        and not task_is_dependency_blocked(task, data)
    ]


def dependency_waiting_tasks(data: dict) -> list[dict]:
    return [
        task
        for task in data.get("tasks", [])
        if task.get("status") == "pending"
        and not task.get("blocked_by_human", False)
        and task_is_dependency_blocked(task, data)
    ]


def is_clean_idle_blocked(data: dict) -> bool:
    return (
        current_in_progress_task(data) is None
        and not has_executable_safe_task(data)
        and bool(blocked_tasks(data))
        and not pending_unblocked_tasks(data)
    )


def overall_state(
    *,
    current: dict | None,
    planned: list[dict],
    blockers: list[dict],
    dependency_waiting: list[dict],
    clean_idle: bool,
) -> str:
    if current:
        return "active"
    if clean_idle:
        return "clean_idle_blocked"
    if planned or dependency_waiting:
        return "planned"
    if blockers:
        return "blocked"
    return "idle"


def queue_health(
    *,
    current: dict | None,
    planned: list[dict],
    blockers: list[dict],
    review_waiting: list[dict],
    dependency_waiting: list[dict],
) -> str:
    if current and is_stale_in_progress_task(current):
        return "stale_active"
    if current:
        return "active_only"
    if review_waiting:
        return "review_waiting"
    if any(is_long_blocked_task(task) for task in blockers):
        return "stale_blocked"
    if blockers and (planned or dependency_waiting):
        return "mixed_blocked_and_ready"
    if blockers:
        return "blocked_only"
    if planned and dependency_waiting:
        return "mixed_ready_and_dependencies"
    if planned:
        return "ready_backlog"
    if dependency_waiting:
        return "dependency_waiting_only"
    return "empty"


def attention_required(data: dict) -> str:
    current = current_in_progress_task(data)
    blockers = blocked_tasks(data)
    if review_waiting_tasks(data):
        return "review"
    if current and is_stale_in_progress_task(current):
        return "stale"
    if any(is_long_blocked_task(task) for task in blockers):
        return "stale"
    if blockers:
        return "unblock"
    return "none"


def attention_task(*, attention: str, current: dict | None, review_waiting: list[dict], blockers: list[dict]) -> dict | None:
    if attention == "review":
        return review_waiting[0] if review_waiting else None
    if attention == "stale":
        if current and is_stale_in_progress_task(current):
            return current
        for task in blockers:
            if is_long_blocked_task(task):
                return task
        return None
    if attention == "unblock":
        return blockers[0] if blockers else None
    return None


def next_action(*, attention: str, current: dict | None, next_task: dict | None, dependency_waiting: list[dict]) -> str:
    if attention == "review":
        return "request_human_review"
    if attention == "stale":
        return "investigate_stale_work"
    if attention == "unblock":
        return "unblock_human_task"
    if current:
        return "continue_current"
    if next_task:
        return "execute_next_safe_task"
    if dependency_waiting:
        return "wait_on_dependencies"
    return "idle"


def next_action_task(
    *,
    attention: str,
    current: dict | None,
    next_task: dict | None,
    dependency_waiting: list[dict],
    review_waiting: list[dict],
    blockers: list[dict],
) -> dict | None:
    task = attention_task(
        attention=attention,
        current=current,
        review_waiting=review_waiting,
        blockers=blockers,
    )
    if task:
        return task
    if current:
        return current
    if next_task:
        return next_task
    if dependency_waiting:
        return dependency_waiting[0]
    return None


def next_step_summary(action: str, task: dict | None) -> str:
    if not task:
        return action
    return f"{action} {task['id']}: {task['title']}"


def waiting_on(*, review_waiting: list[dict], blockers: list[dict], dependency_waiting: list[dict]) -> str:
    if review_waiting:
        return "human_review"
    if blockers:
        return "human_unblock"
    if dependency_waiting:
        return "dependencies"
    return "none"


def human_input_queue(*, review_waiting: list[dict], blockers: list[dict]) -> str:
    review_count = len(review_waiting)
    blocked_count = len(blockers)
    total = review_count + blocked_count
    return f"review={review_count} blocked={blocked_count} total={total}"


def state_reason(
    *,
    current: dict | None,
    next_task: dict | None,
    blockers: list[dict],
    review_waiting: list[dict],
    dependency_waiting: list[dict],
    clean_idle: bool,
    attention: str,
) -> str:
    if current:
        return "stale_in_progress" if attention == "stale" and is_stale_in_progress_task(current) else "current_in_progress"
    if clean_idle:
        return "human_blocked_only"
    if review_waiting:
        return "review_waiting"
    if blockers:
        return "stale_blocked_task" if attention == "stale" else "human_blocked_pending"
    if next_task:
        return "ready_safe_backlog"
    if dependency_waiting:
        return "dependency_waiting"
    return "no_pending_work"


def pending_safe_tasks(data: dict) -> list[dict]:
    return [
        task
        for task in data.get("tasks", [])
        if task.get("status") == "pending"
        and task.get("safe", False)
        and not task.get("requires_human_review", False)
        and not task.get("blocked_by_human", False)
        and not task_is_dependency_blocked(task, data)
    ]


def latest_planning_event() -> dict | None:
    for event in reversed(load_execution_events()):
        if event.get("event") == "planned_next_tasks":
            return event
    return None


def next_auto_task_id(data: dict) -> str:
    max_number = 0
    for task in data.get("tasks", []):
        task_id = task.get("id", "")
        if not task_id.startswith(f"{AUTO_TASK_PREFIX}-"):
            continue
        suffix = task_id.removeprefix(f"{AUTO_TASK_PREFIX}-")
        if suffix.isdigit():
            max_number = max(max_number, int(suffix))
    return f"{AUTO_TASK_PREFIX}-{max_number + 1}"


def add_task(data: dict, task: dict) -> None:
    data.setdefault("tasks", []).append(task)


def block_task(task: dict, *, reason: str, timestamp: str) -> None:
    task["blocked_by_human"] = True
    task["blocker_reason"] = reason
    task["blocked_at"] = timestamp
    if task.get("status") == "in_progress":
        task["status"] = "pending"


def unblock_task(task: dict, *, resolution: str, timestamp: str) -> None:
    task["blocked_by_human"] = False
    task["unblocked_at"] = timestamp
    task["unblock_resolution"] = resolution


def append_execution_event(event: dict) -> None:
    EXECUTION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with EXECUTION_LOG_PATH.open("a") as handle:
        handle.write(json.dumps(event) + "\n")
