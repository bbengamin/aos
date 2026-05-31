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
