# Plan

## Current Phase

Bootstrap the minimum mission OS.

## Steps

1. Create durable mission and governance files.
2. Create a task list with explicit done conditions.
3. Add a simple selector for one next safe task.
4. Add a basic eval script for bootstrap capabilities.
5. Log decisions, risks, and eval outcomes.
6. Use git commits as iteration memory.

## Out Of Scope For Bootstrap

- autonomous multi-step execution without review gates
- external API calls
- deployment
- secret management
- production mutation

## Proposed Next Mission

Implement a tiny single-task executor that records before/after state and refuses high-risk tasks without human review.
