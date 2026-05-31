#!/usr/bin/env python3

from __future__ import annotations

import os

from tasklib import pending_safe_tasks


SAFE_TASK_TEMPLATES = [
    {
        "title": "Add supervisor daemon for repeated AFK episodes",
        "theme": "supervisor",
        "priority": "high",
        "kind": "improvement",
        "done_condition": "A local daemon script can launch bounded AFK episodes repeatedly, sleep in clean idle-blocked state, and resume when executable work appears.",
        "notes": "This turns episodic AFK runs into a persistent local operating loop without adding secrets or private integrations.",
        "planning_reason": "The loop can already plan and execute bounded episodes, but it still needs a persistent local operator that keeps relaunching those episodes while preserving review gates.",
    },
    {
        "title": "Add planner-generated task reporting",
        "theme": "planner",
        "priority": "medium",
        "kind": "improvement",
        "done_condition": "The system records when and why new tasks were generated so humans can review planning decisions after AFK runs.",
        "notes": "Makes the new planning step inspectable and easier to trust.",
        "planning_reason": "The planner currently creates new work with only titles and done conditions, so humans need explicit rationale to audit why each new task entered the queue.",
    },
    {
        "title": "Add idle-state status summary command",
        "theme": "status",
        "priority": "medium",
        "kind": "improvement",
        "done_condition": "A status summary can distinguish active work, planned work, blocked work, and clean idle-blocked state in one command.",
        "notes": "Helps humans quickly understand whether the system is waiting or working.",
        "planning_reason": "Once planning and supervision exist, humans need a single status view that explains whether the system is actively working, waiting on a blocker, or cleanly idle.",
    },
    {
        "title": "Add supervisor cycle outcome summaries",
        "theme": "supervisor",
        "priority": "medium",
        "kind": "improvement",
        "done_condition": "The supervisor records a short structured outcome for each AFK cycle so humans can inspect whether each relaunch ended in progress, clean idle, or failure.",
        "notes": "Makes unattended relaunch behavior easier to audit after longer runs.",
        "planning_reason": "Now that a supervisor exists, humans need a durable summary of what each AFK cycle actually did instead of only the raw log stream.",
        "requires_done_titles": ["Add supervisor daemon for repeated AFK episodes"],
    },
    {
        "title": "Add planner backlog breadth limits",
        "theme": "planner",
        "priority": "medium",
        "kind": "improvement",
        "done_condition": "The planner can rotate through multiple safe improvement themes without re-adding covered work or flooding the queue with one theme.",
        "notes": "Keeps self-generated backlog growth controlled and easier to review.",
        "planning_reason": "Once the planner can keep generating work, it needs a simple breadth control so the queue stays varied and inspectable instead of repetitive.",
        "requires_done_titles": ["Add planner-generated task reporting"],
    },
    {
        "title": "Add stale-work status indicators",
        "theme": "status",
        "priority": "medium",
        "kind": "improvement",
        "done_condition": "Status output highlights stale in-progress or long-blocked tasks so humans can spot neglected work quickly.",
        "notes": "Improves human supervision once the backlog and history get larger.",
        "planning_reason": "After richer status reporting exists, the next safe improvement is to surface neglected work so humans can intervene earlier.",
        "requires_done_titles": ["Add idle-state status summary command"],
    },
    {
        "title": "Add task dependency metadata for planned work",
        "theme": "planner",
        "priority": "medium",
        "kind": "improvement",
        "done_condition": "Planned tasks can carry lightweight dependency hints so the selector and humans can see why some work should wait.",
        "notes": "Adds more structure to a growing self-generated backlog without introducing a heavy workflow engine.",
        "planning_reason": "As the planner generates more follow-up work, lightweight dependency hints keep the backlog understandable and reduce accidental out-of-order execution.",
        "requires_done_titles": ["Add planner backlog breadth limits"],
    },
    {
        "title": "Add AFK log index command",
        "theme": "logs",
        "priority": "low",
        "kind": "improvement",
        "done_condition": "A command can list recent AFK log files with timestamps and outcomes so humans can inspect unattended runs quickly.",
        "notes": "Improves inspectability of longer unattended sessions.",
        "planning_reason": "Once unattended runs accumulate, humans need a fast index over AFK logs instead of opening individual files manually.",
        "requires_done_titles": ["Add supervisor cycle outcome summaries"],
    },
    {
        "title": "Add planner candidate audit command",
        "theme": "planner",
        "priority": "low",
        "kind": "improvement",
        "done_condition": "A command can show which planner candidates are covered, eligible, or blocked so humans can understand why the planner chose or skipped work.",
        "notes": "Makes planner behavior more explainable without adding external dependencies.",
        "planning_reason": "As the planner catalog becomes broader, humans need a direct way to inspect why candidate tasks are eligible, skipped, or already covered.",
        "requires_done_titles": ["Add planner backlog breadth limits", "Add stale-work status indicators"],
    },
]

FOLLOW_UP_TEMPLATE_SPECS = [
    {
        "generator_key": "supervisor_follow_up",
        "title_stem": "Refine supervisor cycle outcome summaries",
        "theme": "supervisor",
        "priority": "medium",
        "kind": "improvement",
        "done_condition_template": "Batch {batch} extends supervisor cycle summaries with one more actionable operator signal while preserving bounded local execution.",
        "notes_template": "Follow-up batch {batch} keeps the supervisor observable without expanding into risky automation.",
        "planning_reason_template": "Supervisor summary coverage exists, so batch {batch} should tighten what each AFK cycle reports back to humans.",
        "requires_done_titles": ["Add supervisor cycle outcome summaries"],
    },
    {
        "generator_key": "planner_follow_up",
        "title_stem": "Refine planner backlog generation heuristics",
        "theme": "planner",
        "priority": "medium",
        "kind": "improvement",
        "done_condition_template": "Batch {batch} improves planner candidate selection or explanation quality without introducing unsafe autonomous scope.",
        "notes_template": "Follow-up batch {batch} keeps self-generated work varied and inspectable.",
        "planning_reason_template": "Planner backlog controls now exist, so batch {batch} should improve how the planner derives or explains fresh safe work.",
        "requires_done_titles": ["Add planner candidate audit command"],
    },
    {
        "generator_key": "status_follow_up",
        "title_stem": "Refine operator status summaries",
        "theme": "status",
        "priority": "medium",
        "kind": "improvement",
        "done_condition_template": "Batch {batch} adds one more useful status signal that helps a human distinguish active, waiting, stale, and blocked work at a glance.",
        "notes_template": "Follow-up batch {batch} keeps the operator view concise but more informative.",
        "planning_reason_template": "Status reporting already covers the main states, so batch {batch} should sharpen the operator summary instead of widening system scope.",
        "requires_done_titles": ["Add stale-work status indicators"],
    },
    {
        "generator_key": "logs_follow_up",
        "title_stem": "Refine AFK log indexing and summaries",
        "theme": "logs",
        "priority": "low",
        "kind": "improvement",
        "done_condition_template": "Batch {batch} improves AFK log indexing or summary extraction so unattended runs remain easy to audit.",
        "notes_template": "Follow-up batch {batch} keeps unattended log review practical as more runs accumulate.",
        "planning_reason_template": "AFK log indexing exists, so batch {batch} should improve how unattended run history is summarized for humans.",
        "requires_done_titles": ["Add AFK log index command"],
    },
    {
        "generator_key": "eval_follow_up",
        "title_stem": "Harden eval coverage for planner and supervisor loops",
        "theme": "eval",
        "priority": "medium",
        "kind": "improvement",
        "done_condition_template": "Batch {batch} adds or tightens one more deterministic eval around planner or supervisor behavior.",
        "notes_template": "Follow-up batch {batch} keeps the loop trustworthy as more self-generated behavior appears.",
        "planning_reason_template": "The system now plans and supervises more work, so batch {batch} should keep expanding deterministic eval coverage around those loops.",
        "requires_done_titles": ["Add supervisor cycle outcome summaries", "Add planner candidate audit command"],
    },
]

PLANNER_BATCH_SIZE = 3
PLANNER_THEME_OPEN_LIMIT = 1


def planner_max_auto_tasks() -> int | None:
    raw_limit = os.environ.get("AOS_MAX_AUTO_TASKS")
    if raw_limit and raw_limit.isdigit():
        return int(raw_limit)
    return None


def next_follow_up_batch(data: dict, generator_key: str) -> int:
    max_batch = 0
    for task in data.get("tasks", []):
        if task.get("generator_key") != generator_key:
            continue
        batch = task.get("follow_up_batch")
        if isinstance(batch, int):
            max_batch = max(max_batch, batch)
    return max_batch + 1


def generated_follow_up_templates(data: dict) -> list[dict]:
    templates = []
    for spec in FOLLOW_UP_TEMPLATE_SPECS:
        batch = next_follow_up_batch(data, spec["generator_key"])
        templates.append(
            {
                "title": f"{spec['title_stem']} batch {batch}",
                "theme": spec["theme"],
                "priority": spec["priority"],
                "kind": spec["kind"],
                "done_condition": spec["done_condition_template"].format(batch=batch),
                "notes": spec["notes_template"].format(batch=batch),
                "planning_reason": spec["planning_reason_template"].format(batch=batch),
                "requires_done_titles": spec.get("requires_done_titles", []),
                "generator_key": spec["generator_key"],
                "follow_up_batch": batch,
            }
        )
    return templates


def all_planner_templates(data: dict) -> list[dict]:
    return SAFE_TASK_TEMPLATES + generated_follow_up_templates(data)


def template_already_covered(data: dict, template: dict) -> bool:
    return covering_task(data, template) is not None


def covering_task(data: dict, template: dict) -> dict | None:
    for task in data.get("tasks", []):
        if task.get("title") != template["title"]:
            continue
        if task.get("done_condition") != template["done_condition"]:
            continue
        if task.get("status") in {"pending", "in_progress", "done"}:
            return task
    return None


def title_is_done(data: dict, title: str) -> bool:
    for task in data.get("tasks", []):
        if task.get("title") == title and task.get("status") == "done":
            return True
    return False


def task_id_for_done_title(data: dict, title: str) -> str | None:
    for task in data.get("tasks", []):
        if task.get("title") == title and task.get("status") == "done":
            return task.get("id")
    return None


def missing_required_titles(data: dict, template: dict) -> list[str]:
    return [title for title in template.get("requires_done_titles", []) if not title_is_done(data, title)]


def template_is_eligible(data: dict, template: dict) -> bool:
    return not missing_required_titles(data, template)


def resolved_dependency_ids(data: dict, template: dict) -> list[str]:
    dependency_ids = []
    for required_title in template.get("requires_done_titles", []):
        dependency_id = task_id_for_done_title(data, required_title)
        if dependency_id:
            dependency_ids.append(dependency_id)
    return dependency_ids


def open_theme_tasks(data: dict) -> dict[str, list[dict]]:
    tasks_by_theme: dict[str, list[dict]] = {}
    for task in data.get("tasks", []):
        if task.get("status") not in {"pending", "in_progress"}:
            continue
        theme = task.get("theme")
        if not theme:
            continue
        tasks_by_theme.setdefault(theme, []).append(task)
    return tasks_by_theme


def open_theme_counts(data: dict) -> dict[str, int]:
    return {theme: len(tasks) for theme, tasks in open_theme_tasks(data).items()}


def audit_planner_candidates(data: dict, *, max_auto_tasks: int | None = None) -> list[dict]:
    existing_auto = [task for task in data.get("tasks", []) if task.get("id", "").startswith("AUTO-")]
    theme_tasks = open_theme_tasks(data)
    theme_counts = {theme: len(tasks) for theme, tasks in theme_tasks.items()}
    planned_count = 0
    budget_exhausted = max_auto_tasks is not None and len(existing_auto) >= max_auto_tasks
    planner_gate_blocked = bool(pending_safe_tasks(data))
    candidates = []

    for template in all_planner_templates(data):
        candidate = {
            "title": template["title"],
            "theme": template["theme"],
            "priority": template["priority"],
            "kind": template["kind"],
            "notes": template["notes"],
            "done_condition": template["done_condition"],
            "planning_reason": template["planning_reason"],
            "dependency_titles": template.get("requires_done_titles", []),
            "dependency_ids": resolved_dependency_ids(data, template),
            "generator_key": template.get("generator_key"),
            "follow_up_batch": template.get("follow_up_batch"),
        }

        if template_already_covered(data, template):
            matching_task = covering_task(data, template)
            candidate["status"] = "covered"
            candidate["reason"] = "matching_task_already_exists"
            candidate["covering_task_id"] = matching_task.get("id")
            candidate["covering_task_status"] = matching_task.get("status")
        else:
            missing_titles = missing_required_titles(data, template)
            if budget_exhausted:
                candidate["status"] = "blocked"
                candidate["reason"] = "auto_task_budget_exhausted"
            elif missing_titles:
                candidate["status"] = "blocked"
                candidate["reason"] = "waiting_on_done_titles"
                candidate["missing_required_titles"] = missing_titles
            elif theme_counts.get(template["theme"], 0) >= PLANNER_THEME_OPEN_LIMIT:
                open_tasks = theme_tasks.get(template["theme"], [])
                candidate["status"] = "blocked"
                candidate["reason"] = "theme_open_limit_reached"
                candidate["theme_open_tasks"] = theme_counts.get(template["theme"], 0)
                candidate["theme_open_task_ids"] = [task.get("id") for task in open_tasks if task.get("id")]
                candidate["theme_open_task_titles"] = [task.get("title") for task in open_tasks if task.get("title")]
            elif planned_count >= PLANNER_BATCH_SIZE:
                candidate["status"] = "blocked"
                candidate["reason"] = "planner_batch_full"
            elif planner_gate_blocked:
                candidate["status"] = "blocked"
                candidate["reason"] = "planner_gate_has_executable_safe_tasks"
            else:
                candidate["status"] = "eligible"
                candidate["reason"] = "would_be_planned_now"
                planned_count += 1
                theme_counts[template["theme"]] = theme_counts.get(template["theme"], 0) + 1
                theme_tasks.setdefault(template["theme"], []).append({"id": None, "title": template["title"]})

        candidates.append(candidate)

    return candidates


def planner_batch_consumers(candidates: list[dict]) -> list[dict]:
    return [candidate for candidate in candidates if candidate.get("status") == "eligible"][:PLANNER_BATCH_SIZE]


def planner_batch_consumer_ids(data: dict, batch_consumers: list[dict]) -> list[str]:
    consumer_ids = []
    title_to_ids: dict[tuple[str, str | None, str | None], list[str]] = {}

    for task in data.get("tasks", []):
        key = (task.get("title"), task.get("done_condition"), task.get("generator_key"))
        task_id = task.get("id")
        if not task_id:
            continue
        title_to_ids.setdefault(key, []).append(task_id)

    for candidate in batch_consumers:
        key = (
            candidate.get("title"),
            candidate.get("done_condition"),
            candidate.get("generator_key"),
        )
        existing_ids = title_to_ids.get(key, [])
        if existing_ids:
            consumer_ids.append(existing_ids[0])
            continue

        consumer_ids.append(f"PLANNED:{candidate['title']}")

    return consumer_ids
