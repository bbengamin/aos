# Risk Log

## Current Risk Posture

Bootstrap risk is low because the system only writes local repository files and runs local checks.

## Known Risks

### 2026-05-31 - False sense of capability

Risk:
The repository could look complete before execution and review gates are mature.

Mitigation:

- keep scope explicitly limited in `mission/plan.md`
- require eval pass before claiming progress
- keep next improvement focused on safe single-task execution

### 2026-05-31 - Unsafe future autonomy

Risk:
Later iterations could add risky actions without a review stop.

Mitigation:

- high-risk actions are listed in the constitution
- guardian role explicitly blocks them pending human review
- future executor work should check for review requirements first

### 2026-05-31 - Unbounded self-improvement loops

Risk:
An infinite loop can consume budget and create noisy commits without meaningful progress.

Mitigation:

- `scripts/episode` is bounded by `MAX_ITERATIONS`
- the loop exits on eval failure instead of silently churning
- the loop exits on human-review-required tasks

### 2026-05-31 - Safe public networking vs higher-risk integrations

Risk:
Allowing all network activity would blur the line between safe public notifications and higher-risk authenticated integrations.

Mitigation:

- public outbound network calls are approved only in the narrow open/no-secrets scope
- any authenticated, secret-bearing, write-capable, or private-system integration remains human-review-gated
- a dedicated sentinel task (`RISK-2`) preserves that review boundary
