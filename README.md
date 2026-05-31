# Mission-Centered Agentic OS

This repository is the smallest inspectable bootstrap for a mission-centered self-building system.

It is intentionally file-first:

- mission state lives in `mission/`
- agent role guides live in `agents/`
- automation lives in `scripts/`
- git is the history and memory layer

## What It Can Do Now

- store the mission
- store the constitution
- store a current plan
- track tasks with done conditions
- select exactly one next task
- start exactly one safe task at a time
- stop for human review on gated tasks
- run a basic bootstrap eval
- run a bounded improvement episode loop
- log decisions, risks, and eval results
- propose the next improvement
- stop for human review on high-risk work

## Core Files

- `mission/mission.md`
- `mission/constitution.md`
- `mission/resources.md`
- `mission/plan.md`
- `mission/tasks.json`
- `mission/decision-log.md`
- `mission/risk-log.md`
- `mission/evals.md`
- `agents/planner.md`
- `agents/builder.md`
- `agents/guardian.md`

## Scripts

- `./scripts/next-task`: prints the next pending task that is not blocked by human review or unresolved task dependencies
- `./scripts/execute-task`: starts one safe task or stops for human review
- `./scripts/episode`: runs a bounded Ralph-style improvement episode and closes the active task after a passing eval and explicit `COMPLETION_SUMMARY`
- `./scripts/afk`: runs `episode` with timestamped logging for unattended sessions
- `./scripts/supervisor`: relaunches bounded AFK episodes, sleeps while work is cleanly idle-blocked, resumes when executable work appears, and records a structured summary for each AFK cycle
- `./scripts/status`: summarizes whether the system is active, planned, blocked, or cleanly idle-blocked, shows current work, planned work, human blockers, dependency-waiting work, and flags stale work
- `./scripts/block-task`: mark a task blocked with a human reason
- `./scripts/unblock-task`: clear a blocker with a human resolution note
- `./scripts/plan-next`: generate the next 1-3 safe tasks when the executable queue is empty
- `./scripts/eval`: runs the minimum bootstrap checks

## Working Rules

1. Change one small thing at a time.
2. Keep every decision inspectable.
3. Do not weaken the constitution.
4. Ask for human review before high-risk actions.
5. Do not mark work complete until checks pass.

## Current Bootstrap Status

Run:

```bash
./scripts/next-task
./scripts/execute-task --dry-run
./scripts/eval
```

For an unattended bounded run:

```bash
./scripts/afk 20
```

It writes a timestamped log under `logs/` and returns a non-zero exit code only for real failures.
Inside `episode`, the system now follows a fuller loop: if no executable safe task exists, it runs `./scripts/plan-next`, then continues with act/review/update. Planner-created tasks now carry a `planning_reason` in both `mission/tasks.json` and the `planned_next_tasks` execution-log event so humans can inspect why the backlog changed. The planner also tags each candidate with a lightweight `theme`, records `depends_on_task_ids` plus matching `dependency_titles` when a new task depends on already-finished work, and limits itself to one open task per theme at a time, which keeps the generated backlog varied instead of stacking several planner, status, or supervisor follow-ups at once. The agent must emit either `COMPLETION_SUMMARY: ...` for completed work or `BLOCKED_BY_HUMAN: ...` when human input is needed. Each supervisor relaunch also appends a `supervisor_cycle_summary` event to `mission/execution-log.ndjson` and prints a matching `SUPERVISOR_CYCLE_SUMMARY` line so humans can inspect whether a cycle ended in `progress`, `clean_idle`, or `failure`.

To see where human action is needed:

```bash
./scripts/status
```

The place to look for blockers is `mission/tasks.json`, and the quickest human-readable view is `./scripts/status`. That command now reports a single overall `STATE`, whether the repo is in `CLEAN_IDLE_BLOCKED` mode, the current executable task, the planned safe backlog, the latest planner event with its rationale, the blocked queue, dependency-waiting tasks, and stale-work counters. `./scripts/next-task` skips any pending task whose `depends_on_task_ids` still point at unfinished work, while `./scripts/status` surfaces those items under `DEPENDENCY_WAITING` together with their human-readable `dependency_titles`. `STALE_IN_PROGRESS` highlights work that has been in progress for more than a day, while `LONG_BLOCKED` highlights tasks that have been blocked by humans for more than three days. `STATE blocked` means blockers exist but the repo is not in the clean idle-blocked state because some other pending work still exists, usually a review-gated risk task.

To block one task and keep the loop working on others:

```bash
./scripts/block-task NEXT-4 --reason "Waiting for human decision on scope"
```

To resolve that blocker and let the loop pick it again:

```bash
./scripts/unblock-task NEXT-4 --resolution "Human approved the narrow slice"
```

If eval passes, the bootstrap system is ready for the next safe iteration.
