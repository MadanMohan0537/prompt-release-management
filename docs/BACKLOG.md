# Feature backlog

Status reflects this repository, not the wider product vision.

| Priority | Feature | User problem | Behavior | Dependencies | Success test | Risks / tradeoffs | Status |
|---|---|---|---|---|---|---|---|
| P0 | Versioned release workflow | Teams cannot reconstruct what changed | Register bundles, rationale, evidence, approval and diff | Python stdlib | Unapproved or stale release is rejected | Process can feel heavy for experiments | Shipped |
| P1 | Configuration bundle promotion | Prompt-only versions miss behavioral dependencies | Digest prompt, model, retrieval and tools with explicit scope | Canonical JSON + SHA-256 | 4/4 scoped mutations invalidate evidence | Broad scope slows safe tiny edits; narrow scope can hide coupling | Shipped |
| P1 | Sequential canary statistics | Small cohorts trigger noisy rollbacks | Require per-cohort sample floors, one-sided confidence evidence, family-error spending, and a maximum-look hold | Python statistics primitives | Noisy point drop stays live; severe regression rolls back; 200 null trials stay within 5% budget | Normal approximation can miscalibrate bounded/dependent data; conservative budget slows detection | **Shipped** |
| P1 | Segment guardrails | Aggregate quality hides harm to a locale or plan | Compare candidate by declared protected/operational slices | Segment labels, minimum counts | Seeded subgroup regression rolls back | Privacy and sparse-data risks | Planned |
| P2 | Rollback compatibility preview | Old prompt may not match new tools or retrieval schema | Dry-run rollback bundle against current contracts before promotion | Schema compatibility engine | Breaking tool change is blocked with actionable diff | Static checks cannot catch all runtime behavior | Planned |
| P2 | Tamper-evident audit chain | Mutable logs weaken compliance evidence | Hash-chain events and sign release attestations | Key management | Modified historical event fails verification | Operational burden and key rotation | Explored |
| P2 | Approval policy as code | One reviewer is insufficient for high-risk surfaces | Match risk tier to reviewer roles and quorum | Identity provider, policy file | High-risk release cannot bypass required specialties | Role sprawl can slow releases | Explored |
| P3 | Cost and latency budgets | Quality-only promotion can raise serving cost | Evaluate multi-objective thresholds during canary | Token, latency telemetry | Candidate exceeding budget cannot graduate | Optimizing metrics may reduce quality | Explored |
| P3 | Evidence expiry | Old evidence may predate distribution shifts | Expire by time or monitored drift signal | Clock, drift detector | Expired evidence blocks promotion | Re-evaluation cost and alert fatigue | Explored |
| P3 | Emergency release mode | Incidents sometimes require rapid edits | Time-bound override with two-person approval and mandatory retrospective | Identity and incident system | Override expires and creates follow-up record | Can become routine bypass if poorly governed | Explored |

## Newly evaluated extensions

| Priority | Feature | User problem | Behavior | Dependencies | Success test | Risks / tradeoffs | Status |
|---|---|---|---|---|---|---|---|
| P1 | Paired replay canary | Aggregate scores can move because traffic mix changes | Replay matched request keys through stable and candidate bundles and analyze paired deltas | Privacy-reviewed replay corpus, deterministic runner | Seeded cohort-mix shift no longer causes a false rollback | Replays can be stale and retain sensitive content | Planned |
| P2 | Metric freshness contract | A statistically sound decision can still use delayed or partial telemetry | Require metric timestamp, completeness, and cohort coverage before every look | Telemetry metadata | Stale or partial metric fixture produces an evidence hold | Extra holds can slow incident response | Planned |
| P2 | Harm-weighted guardrail | Mean quality can hide a few severe failures | Combine predeclared severity weights with a hard critical-event ceiling | Reviewed severity rubric | One seeded critical regression blocks despite a stable mean | Weights invite gaming and require governance | Planned |

Next slice: segment guardrails, because aggregate confidence can still hide a concentrated regression. After that, implement the rigorous rollback compatibility preview with stored tool-schema replay.

