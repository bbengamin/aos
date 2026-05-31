# Eval Log

## 2026-05-31 - Bootstrap eval

Command:

```bash
./scripts/next-task
./scripts/eval
```

Result:

- `scripts/next-task` selected `BOOT-2`
- `scripts/eval` returned `EVAL_PASS`

Validated:

- required bootstrap files exist
- the system can list current tasks
- the system can select exactly one next safe task
- the system can run a basic eval
- the plan proposes the next improvement

Outcome:

Bootstrap capabilities are present and verified.

## 2026-05-31 - Safe execution loop eval

Command:

```bash
./scripts/next-task
./scripts/execute-task --dry-run
./scripts/eval
```

Checks expected:

- `next-task` returns exactly one current executable task
- `execute-task --dry-run` reports readiness without mutating state
- eval confirms a human-review-gated task exists
- eval confirms the execution log exists and is parseable
- eval confirms the bounded episode runner is present

Result:

- `next-task` selected `NEXT-1`
- `execute-task --dry-run` reported `READY_TO_EXECUTE`
- `execute-task` started `NEXT-1`
- `execute-task RISK-1` reported `HUMAN_REVIEW_REQUIRED`
- `scripts/eval` returned `EVAL_PASS`

Outcome:

The system can now hold one active task, stop on review-gated work, and run a bounded Ralph-style episode loop.

## 2026-05-31 - Task completion helper eval

Command:

```bash
./scripts/complete-task --summary "Added scripts/complete-task, shared tasklib completion helper, and eval coverage for completion evidence."
./scripts/eval
```

Checks expected:

- `complete-task` can close the current in-progress task
- the completed task records a `completion_summary` in `mission/tasks.json`
- the execution log records a `completed` event with the same summary
- eval still returns `EVAL_PASS` after a new safe pending task is available

Result:

- `complete-task` reported `TASK_COMPLETED` for `NEXT-1`
- `mission/tasks.json` records `completed_at` and `completion_summary` for `NEXT-1`
- `mission/execution-log.ndjson` contains a `completed` event for `NEXT-1`
- `scripts/eval` returned `EVAL_PASS`

Outcome:

The repository can now explicitly close one in-progress safe task with durable evidence of what changed.

## 2026-05-31 - AFK wrapper eval

Command:

```bash
./scripts/afk 1
./scripts/eval
```

Checks expected:

- `scripts/afk` accepts an iteration count as a positional argument
- it writes a timestamped log file under `logs/`
- it returns the same exit status as `scripts/episode`
- eval still returns `EVAL_PASS`

## 2026-05-31 - Blocker visibility eval

Command:

```bash
./scripts/status
./scripts/next-task
./scripts/eval
```

Checks expected:

- tasks with `blocked_by_human: true` remain visible to humans
- blocked tasks are not selected as the next safe task
- `scripts/status` shows current work, next work, and blockers in one place
- eval confirms blocker visibility support is present

## 2026-05-31 - Episode completion loop eval

Command:

```bash
./scripts/eval
```

Checks expected:

- `scripts/episode` requires an explicit `COMPLETION_SUMMARY:` line from the inner agent
- `scripts/episode` supports an explicit `BLOCKED_BY_HUMAN:` line from the inner agent
- `scripts/episode` calls `scripts/complete-task` after a passing eval
- `mission/bootstrap-prompt.txt` tells the inner agent not to complete or commit directly during an episode
- eval still returns `EVAL_PASS`

Result:

- `scripts/episode` now parses `COMPLETION_SUMMARY:` from agent output
- `scripts/episode` now also parses `BLOCKED_BY_HUMAN:` from agent output
- `scripts/episode` runs `scripts/complete-task --summary ...` before commit
- `mission/bootstrap-prompt.txt` documents the runner-owned completion flow
- `scripts/eval` returned `EVAL_PASS`

Outcome:

The bounded episode loop can now close a completed safe task explicitly before committing the iteration.

## 2026-05-31 - Continue past blocked tasks eval

Command:

```bash
./scripts/status
./scripts/eval
```

Checks expected:

- blocked tasks remain visible in status output
- the runner can treat blocked tasks as non-fatal and continue with later safe work
- prompt and runner both support `BLOCKED_BY_HUMAN:` as a structured blocker signal

## 2026-05-31 - Narrow network approval recorded

Checks expected:

- `RISK-1` is resolved as a documented narrow approval
- a replacement sentinel keeps higher-risk network integrations blocked
- the documented approval excludes secrets, auth, private systems, spending, deployment, and external write actions

Result:

- `RISK-1` is resolved as a narrow public-network approval
- `RISK-2` remains blocked for authenticated, secret-bearing, or write-capable integrations
- `./scripts/eval` returns `EVAL_PASS` with `NEXT none` and `BLOCKERS 1`

Outcome:

The repository now treats "only blocked work remains" as a valid idle state instead of a failure.

## 2026-05-31 - Human blocker workflow eval

Command:

```bash
./scripts/block-task NEXT-4 --reason "Waiting for human decision on scope"
./scripts/unblock-task NEXT-4 --resolution "Human approved the narrow slice"
./scripts/eval
```

Checks expected:

- humans can explicitly block a task without editing JSON directly
- humans can explicitly unblock a task with a resolution note
- execution-log captures both block and unblock events
- eval confirms the commands are present

## 2026-05-31 - Local planning loop eval

Checks expected:

- `scripts/plan-next` generates safe `AUTO-*` tasks when no executable safe work exists
- `scripts/plan-next` logs a `planned_next_tasks` event
- `scripts/episode` invokes the planner when the executable queue is empty
- eval confirms the plan stage is wired into the loop
