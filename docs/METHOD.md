# Method and limitations

## Evaluation method

The CLI uses 1,000 deterministic routing keys and an intentionally degraded candidate. Stable samples score 0.92 and candidate samples 0.55. A rollback is expected when the observed candidate drop exceeds 0.05. These values test control behavior; they are not evidence of model quality.

Evidence integrity is tested separately: a passing record is bound to a canonical, sorted JSON manifest digest. Mutating each of the four default dependencies must invalidate the record. An explicit narrow scope is tested as a control.

## Sequential canary rule

The canary decision is predeclared: each stable and candidate cohort needs 30 samples; the observed stable-minus-candidate mean quality drop is compared with a 0.05 tolerance; and rollback occurs only when the one-sided lower confidence bound exceeds that tolerance. Sample variance supplies the standard error. A 5% family error budget is Bonferroni-divided across at most 20 looks; after that, the system requests manual review instead of repeatedly testing.

Acceptance evidence includes three frozen checks: a noisy point drop above 0.05 remains live when its lower bound is inconclusive, a 0.37 seeded regression rolls back, and 200 seeded equal-quality trials remain within the declared 5% false-rollback budget. These tests validate implementation behavior, not universal statistical calibration.

## Assumptions

- The caller supplies trustworthy, comparable metric samples.
- Route keys are stable and non-sensitive before hashing.
- One independent approval is sufficient for this demo.
- Bundle dictionaries contain JSON-serializable data.

## Limitations and risks

- In-memory state disappears at process exit; production use needs transactional durable storage.
- Actor names are not authenticated identities and audit events are not tamper-evident.
- Normal-approximation bounds can be inaccurate for bounded, highly skewed, dependent, or nonstationary quality scores.
- Bonferroni control is conservative and assumes a predeclared maximum number of looks; adaptive traffic and overlapping samples need a stronger sequential design.
- The sample floor is a workflow guard, not a power calculation. Production thresholds must reflect minimum detectable harm and segment prevalence.
- A single aggregate metric can hide subgroup regressions.
- Narrow dependency scopes reduce retesting but can legitimize stale evidence when chosen incorrectly.
- Rollback compatibility is not checked; restoring an older prompt against a changed tool contract may fail.

## Success criteria for this MVP

- Every promoted version has current passing evidence and independent approval.
- 4/4 scoped configuration mutations invalidate existing evidence.
- A synthetic harmful candidate receives a bounded cohort and is automatically removed.
- Inconclusive or undersized canaries do not roll back, and repeated looks cannot exceed the declared budget.
- The full decision trail exports without external services.

