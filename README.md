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
- `./scripts/afk-log-index`: lists recent `logs/afk-*.log` files with parsed timestamps, last-task context, and best-effort outcomes
- `./scripts/supervisor`: relaunches bounded AFK episodes, sleeps while work is cleanly idle-blocked, resumes when executable work appears, and records a structured summary for each AFK cycle
- `./scripts/status`: summarizes whether the system is active, planned, blocked, or cleanly idle-blocked, explains that top-level state with `STATE_REASON`, adds a compact `STATUS_POSTURE` signal for mixed active-vs-waiting conditions, shows top-level `WORK_INVENTORY`, `QUEUE_HEALTH`, and `HUMAN_INPUT_QUEUE` summaries, an `ATTENTION_REQUIRED` signal, a concrete `NEXT_ACTION`, a combined `NEXT_STEP` action-plus-target hint, a top-level `WAITING_ON` cause, the specific `ATTENTION_TASK`, current work, planned work, human blockers, review-gated work, dependency-waiting work, and flags stale work
- `./scripts/block-task`: mark a task blocked with a human reason
- `./scripts/unblock-task`: clear a blocker with a human resolution note
- `./scripts/plan-next`: generate the next 1-3 safe tasks when the executable queue is empty
- `./scripts/planner-candidates`: audit the planner catalog and explain which candidates are already covered, eligible now, or blocked
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
Inside `episode`, the system now follows a fuller loop: if no executable safe task exists, it runs `./scripts/plan-next`, then continues with act/review/update. Planner-created tasks now carry a `planning_reason` in both `mission/tasks.json` and the `planned_next_tasks` execution-log event so humans can inspect why the backlog changed. The planner also tags each candidate with a lightweight `theme`, records `depends_on_task_ids` plus matching `dependency_titles` when a new task depends on already-finished work, and limits itself to one open task per theme at a time, which keeps the generated backlog varied instead of stacking several planner, status, or supervisor follow-ups at once. The agent must emit either `COMPLETION_SUMMARY: ...` for completed work or `BLOCKED_BY_HUMAN: ...` when human input is needed. Each supervisor relaunch also appends a `supervisor_cycle_summary` event to `mission/execution-log.ndjson` and prints a matching `SUPERVISOR_CYCLE_SUMMARY` line so humans can inspect whether a cycle ended in `progress`, `clean_idle`, or `failure`. That summary now also records the post-cycle `repo_state` plus matching `repo_state_reason`, the shared `queue_health` backlog-shape signal from `./scripts/status`, the shared `human_input_queue` review-vs-blocked count, the current `attention_required` signal, a `suggested_action` that mirrors the operator action model from `./scripts/status`, a compact `next_step` hint that combines that action with the concrete target task when one exists, the current `waiting_on` cause from `./scripts/status`, the concrete `suggested_action_task_id` and `suggested_action_task_title` when that action points at a specific task, which task ids and task titles were completed during the cycle directly in the console summary, both `remaining_safe_tasks` and `executable_safe_tasks` so humans can distinguish total safe backlog from immediately runnable safe work, and when a cycle ends in `progress` with more safe work remaining it previews the next executable task id and title.

Supervisor cycle summaries also carry the shared `status_posture` signal from `./scripts/status`, so unattended cycle logs expose whether the repo ended that cycle in a mixed condition like `ready_safe_backlog`, `blocked_waiting_for_human`, or `active_with_review_and_blocked` without forcing humans to reconstruct that posture from lower-level fields.

To quickly inspect recent unattended run logs:

```bash
./scripts/afk-log-index 5
```

That command reads `logs/afk-*.log`, sorts them newest-first, and prints the parsed timestamp, a best-effort outcome, and the last task context for each log.

To see where human action is needed:

```bash
./scripts/status
```

The place to look for blockers is `mission/tasks.json`, and the quickest human-readable view is `./scripts/status`. That command now reports a single overall `STATE`, a top-level `STATE_REASON` explaining why that state applies, a top-level `WORK_INVENTORY` summary for active/planned/review/blocked/dependency-waiting/stale counts, a top-level `ATTENTION_REQUIRED` summary, a concrete `NEXT_ACTION`, the matching `ATTENTION_TASK`, a top-level `NEXT_ACTION_TASK`, whether the repo is in `CLEAN_IDLE_BLOCKED` mode, the current executable task, the planned safe backlog, the latest planner event with its rationale, the blocked queue, the separate `REVIEW_WAITING` queue for tasks that still require a human review gate, dependency-waiting tasks, and stale-work counters. `STATE_REASON` distinguishes cases like `ready_safe_backlog` versus `dependency_waiting`, which would otherwise both appear as `STATE planned`, and also makes review-only or human-blocked states more obvious at a glance. `ATTENTION_REQUIRED review` means a human review gate is the most immediate next action, `ATTENTION_REQUIRED unblock` means a human-blocked task needs input, and `ATTENTION_REQUIRED stale` highlights neglected active or blocked work before it silently ages further; `ATTENTION_TASK` points at the concrete task driving that signal. `NEXT_ACTION` turns that status into an operator hint such as `continue_current`, `execute_next_safe_task`, `request_human_review`, `unblock_human_task`, `investigate_stale_work`, or `wait_on_dependencies`, while `NEXT_ACTION_TASK` points at the first concrete task that action should target. `./scripts/next-task` skips any pending task whose `depends_on_task_ids` still point at unfinished work, while `./scripts/status` surfaces those items under `DEPENDENCY_WAITING` together with their human-readable `dependency_titles`. `STALE_IN_PROGRESS` highlights work that has been in progress for more than a day, while `LONG_BLOCKED` highlights tasks that have been blocked by humans for more than three days. `STATE blocked` means blockers exist but the repo is not in the clean idle-blocked state because some other pending work still exists, often visible under `REVIEW_WAITING`.

`WAITING_ON` is the compact wait-cause signal on that same status view. It reports `human_review`, `human_unblock`, `dependencies`, or `none` so humans can quickly see what kind of external wait is shaping the queue, even when active work is already in progress.

`NEXT_STEP` is the compact action-and-target signal on that same status view. It combines the top-level `NEXT_ACTION` with the concrete task from `NEXT_ACTION_TASK`, so humans can scan one line and immediately see both the recommended move and the task it applies to.

`QUEUE_HEALTH` is the compact backlog-shape signal on that status view. It reports labels like `ready_backlog`, `mixed_ready_and_dependencies`, `review_waiting`, `blocked_only`, `stale_active`, or `dependency_waiting_only` so humans can tell whether the queue is mostly actionable, mostly waiting, or already drifting stale without scanning the full detailed sections first.

`HUMAN_INPUT_QUEUE` is the matching human-wait summary. It reports `review=<n> blocked=<n> total=<n>` so humans can quickly see how much pending work is paused on review gates versus unblock decisions.

`EXECUTABLE_SAFE_TASKS` is the matching readiness count. It reports how many safe tasks are runnable right now, so humans can distinguish between a large total backlog and the smaller subset the loop can actually act on immediately.

`STATUS_POSTURE` is the compact mixed-condition summary on that same status view. It reports whether the repo is simply `active_only` or in a more nuanced posture like `active_with_review_and_blocked`, `blocked_with_ready_work`, `ready_and_waiting_on_dependencies`, `stale_active`, or `clean_idle_blocked`, which helps humans interpret queue shape without reading every detailed section first.

To inspect the full planner catalog and see why each candidate would be chosen or skipped:

```bash
./scripts/planner-candidates
```

That audit uses the same eligibility logic as `./scripts/plan-next`, including the top-level gate that blocks all new planning while executable safe work already exists, so its covered, eligible, and blocked reasons match the planner's actual behavior. Candidates with satisfied prerequisites now also show the resolved prerequisite `dependency_ids`, which makes it easier to trace a planner slice back to the concrete completed tasks it depends on. Generated follow-up candidates also show their `generator_key` and `follow_up_batch`, so humans can tell which recurring planner family produced the slice and which batch number it belongs to. Covered candidates also show which existing task id and status already cover that planner slice, which makes duplicate-avoidance decisions easier to inspect. When a candidate is blocked by the planner gate itself, the audit now also shows the current executable safe task ids, titles, and `planner_gate_task_states`, which makes it clearer whether the planner is correctly waiting for already-actionable work to be executed first and what state those blocking tasks are in. When a candidate is blocked by unfinished prerequisite titles, the audit now also shows any matching non-done task ids and statuses already sitting in the queue, so humans can see whether the slice is waiting on a pending task, an in-progress task, or a missing prerequisite entirely. When a candidate is blocked by the per-theme breadth limit, the audit also shows which open task ids and titles are already occupying that theme so humans can see exactly why that planner slice is waiting. When a candidate is blocked because the planner batch is already full, the audit now also shows which eligible task titles, ids, and themes already consumed the current batch slots, using `PLANNED:<title>` placeholders for candidates that would be created in the current planning pass. When a candidate is blocked because the global AUTO-task budget is exhausted, the audit also shows the configured budget limit, the current AUTO-task count, and the AUTO task ids already consuming that capacity.

When that AUTO-task budget gate applies, `auto_task_refs` lists the concrete AUTO task ids and titles currently consuming the budget.

When the top-level planner gate is blocked by executable safe work, the command now also prints `planner_gate_task_refs` so humans can see the exact blocking task ids, titles, and statuses before reading the per-candidate details.

To block one task and keep the loop working on others:

```bash
./scripts/block-task NEXT-4 --reason "Waiting for human decision on scope"
```

To resolve that blocker and let the loop pick it again:

```bash
./scripts/unblock-task NEXT-4 --resolution "Human approved the narrow slice"
```

If eval passes, the bootstrap system is ready for the next safe iteration.
