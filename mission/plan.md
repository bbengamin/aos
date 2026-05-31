# Plan

## Current Phase

Bootstrap the minimum mission OS and add a bounded safe execution loop.

## Steps

1. Create durable mission and governance files.
2. Create a task list with explicit done conditions.
3. Add a simple selector for one next safe task.
4. Add a single-task execution helper with review gates.
5. Add a bounded episode runner for repeated iterations.
6. Log decisions, execution events, risks, and eval outcomes.
7. Use git commits as iteration memory.

## Out Of Scope For Bootstrap

- autonomous multi-step execution without review gates
- external API calls
- deployment
- secret management
- production mutation

## Proposed Next Mission

Teach the bounded episode runner to use the completion helper so one safe task can be closed and committed in a single bounded iteration, while blocked tasks remain visible but do not stop unrelated safe work.
