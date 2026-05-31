# Decision Log

## 2026-05-31 - Bootstrap with files and simple scripts

Decision:
Use markdown, JSON, and tiny local scripts as the initial operating system.

Why:
This keeps the system inspectable, diffable, and safe while still allowing immediate progress.

Consequences:

- bootstrap remains easy to review
- git history can serve as memory
- no hidden state is required

## 2026-05-31 - Defer executor complexity

Decision:
Do not build a general execution engine yet.

Why:
The first milestone only needs task storage, task selection, evals, and logs.

Consequences:

- less architecture upfront
- safer first iteration
- clear next improvement remains available

## 2026-05-31 - Use Python stdlib scripts for bootstrap automation

Decision:
Implement `scripts/next-task` and `scripts/eval` as tiny Python scripts using only the standard library.

Why:
Python is available locally and lets the bootstrap stay readable without adding dependencies.

Consequences:

- no package setup is needed
- behavior remains inspectable in one file per script
- the next iteration can build on the same approach

## 2026-05-31 - Follow a bounded Ralph-style episode loop

Decision:
Adopt the Ralph pattern of bounded repeated runs, but keep this repo's loop minimal and mission-file-based.

Why:
The useful part of Ralph is not recursion itself. It is the discipline of one small slice per run, bounded iterations, and early stop conditions.

Consequences:

- `scripts/episode` uses `MAX_ITERATIONS` instead of an unbounded loop
- the system stops on human-review-required tasks instead of pushing through them
- repeated improvement remains possible without surrendering control

## 2026-05-31 - Preserve exactly one active task at a time

Decision:
If a safe task is already `in_progress`, the selector should keep returning it instead of opening a second one.

Why:
The mission requires one safe task at a time, and Ralph-style loops work best when each run keeps advancing the current slice until it is complete.

Consequences:

- `scripts/next-task` and `scripts/execute-task` both honor the current in-progress task
- the system avoids silently widening scope
- the next missing capability is completion, not selection

## 2026-05-31 - Record completion evidence in task state and execution log

Decision:
Add a dedicated `scripts/complete-task` command instead of folding completion into `scripts/execute-task`.

Why:
Starting work and closing work are different actions. A separate command keeps each script small and lets eval require explicit completion evidence.

Consequences:

- task closure stays inspectable and intentional
- `mission/tasks.json` now carries a `completion_summary` for completed work
- the next missing capability is wiring completion into the bounded episode loop
