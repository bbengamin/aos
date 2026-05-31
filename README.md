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

- `./scripts/next-task`: prints the next pending task that is not blocked by human review
- `./scripts/execute-task`: starts one safe task or stops for human review
- `./scripts/episode`: runs a bounded Ralph-style improvement episode and closes the active task after a passing eval and explicit `COMPLETION_SUMMARY`
- `./scripts/afk`: runs `episode` with timestamped logging for unattended sessions
- `./scripts/status`: shows the current task, next task, and human blockers
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

It writes a timestamped log under `logs/` and returns a non-zero exit code if the episode stops for review or fails.
Inside `episode`, the agent must emit `COMPLETION_SUMMARY: ...` after `./scripts/eval` passes. The runner then records task completion and creates the commit.

To see where human action is needed:

```bash
./scripts/status
```

The place to look for blockers is `mission/tasks.json`, and the quickest human-readable view is `./scripts/status`.

If eval passes, the bootstrap system is ready for the next safe iteration.
