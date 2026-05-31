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

## 2026-05-31 - Add a thin AFK entrypoint instead of expanding the episode runner

Decision:
Provide unattended execution through `scripts/afk` as a small shell wrapper around `scripts/episode`.

Why:
The user needs a one-command entrypoint. A thin wrapper keeps the execution logic in one place while adding timestamps and logs for AFK runs.

Consequences:

- `scripts/episode` remains the core loop
- `scripts/afk` handles log file creation and clearer exit messaging
- unattended runs stay easy to inspect after the fact

## 2026-05-31 - Separate blocked tasks from executable tasks

Decision:
Tasks blocked on human input should stay visible in task state, but they should not stop unrelated safe work from being selected.

Why:
The system should keep making safe progress when one path is waiting on a human. Stopping the whole loop for every blocked task would waste unattended episodes.

Consequences:

- tasks can now carry `blocked_by_human` and `blocker_reason`
- `scripts/next-task` skips blocked tasks
- `scripts/status` provides the human review inbox

## 2026-05-31 - Let the bounded runner own task closure

Decision:
Require the agent inside `scripts/episode` to emit an explicit `COMPLETION_SUMMARY`, then let the runner call `scripts/complete-task` and create the commit.

Why:
The bounded loop should be able to finish one safe slice end to end without depending on the inner agent to mutate task state and git state separately.

Consequences:

- `scripts/episode` now fails closed if the agent does not provide a completion summary
- task completion remains explicit and durable through `scripts/complete-task`
- unattended runs keep one source of truth for when a task is actually closed and committed

## 2026-05-31 - Make blocker resolution an explicit command

Decision:
Humans should block and unblock work through explicit commands instead of editing JSON directly during normal operation.

Why:
Direct JSON edits are still a fallback, but dedicated commands create a cleaner human/AI handoff and preserve an event trail.

Consequences:

- `scripts/block-task` records why a task paused
- `scripts/unblock-task` records how the blocker was resolved
- paused work can resume later with the context preserved in both task state and execution log

## 2026-05-31 - Continue AFK runs past blocked tasks

Decision:
Blocked tasks should consume only their own iteration, not terminate the whole AFK run.

Why:
If one task needs a human, the remaining iteration budget should still be used on other safe tasks. Otherwise AFK runs waste capacity and stop too early.

Consequences:

- the runner treats `BLOCKED_BY_HUMAN:` as a structured non-fatal outcome
- blocked work is recorded and skipped in later selections
- AFK runs end only when the executable queue is exhausted repeatedly or a real failure occurs

## 2026-05-31 - Approve narrow public outbound network calls

Decision:
Approve outbound network calls for public/open-source use, as long as they do not require secrets, authenticated access, private data, spending, deployment, or external write actions.

Why:
The system needs a safe path toward notification and public status/reporting features, and the human explicitly approved that narrow scope.

Consequences:

- public outbound calls are no longer blocked in principle
- higher-risk integrations remain review-gated under a new risk sentinel
- the constitution still blocks secrets, private systems, spending, deployment, and production mutation

## 2026-05-31 - Add a local planning step when the queue is empty

Decision:
When no executable safe task exists, the system should generate a small set of next safe tasks locally instead of idling immediately.

Why:
The loop is incomplete without `plan`. AFK can only consume a finite queue unless the system can replenish its own safe backlog.

Consequences:

- `scripts/plan-next` becomes the minimal local planner
- `scripts/episode` now performs `plan -> act -> review -> learn -> update` more completely
- the next gap after planning is a long-running supervisor/daemon

## 2026-05-31 - Let iteration finalization decide commit and push automatically

Decision:
Keep commit and push decisions inside the bounded iteration finalizer so humans do not need to manage them manually, but only create a commit when the iteration produced relevant tracked changes and always derive the message from the task summary instead of a generic iteration counter.

Why:
Humans should not have to care about whether AFK needs to commit or push. The system should make that decision automatically, but low-signal `agentic-os iteration N` commits and large piles of unpushed local history are both poor outcomes.

Consequences:

- `scripts/episode` now decides whether a completed iteration warrants a commit
- commit messages are summary-based and task-aware instead of generic iteration numbers
- `scripts/episode` attempts a push only when an upstream exists and a new local commit was actually created
