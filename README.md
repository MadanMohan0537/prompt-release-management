# PromptHarbor

[![CI](https://github.com/MadanMohan0537/prompt-release-management/actions/workflows/ci.yml/badge.svg)](https://github.com/MadanMohan0537/prompt-release-management/actions/workflows/ci.yml)

PromptHarbor is a dependency-free reference implementation for releasing prompt systems with the controls normally expected of software: semantic versions, configuration diffs, independent approval, evaluation evidence, deterministic canaries, monitoring, and automatic rollback.

> **Project Lab traceability:** Idea 12 — Prompt Change Management. PromptHarbor is the product name; the original title is retained only to prevent duplicate builds.

## Why this exists

A prompt edit is rarely just text. Model parameters, retrieval settings, and tool schemas can change behavior just as much. Reviewing only the prompt creates stale evidence and unsafe releases. PromptHarbor versions these dependencies as one manifest and binds evaluation evidence to its cryptographic digest.

## Shipped MVP

- Semantic-version registry with rationale and unified manifest diffs
- Bundled prompt, model, retrieval, and tool-schema configuration
- Explicit dependency scope, defaulting to all four behavior-changing inputs
- Evaluation evidence bound to an exact SHA-256 manifest digest
- Independent reviewer approval for customer-facing releases
- Deterministic percentage canaries with stable user routing
- Quality-drop monitor with automatic rollback and audit events
- Confidence-aware sequential canary decisions with cohort sample floors, one-sided lower bounds, and a bounded look budget
- Explicit insufficient-data gaps and manual-review state after the sequential budget is exhausted
- JSON release report and CSV audit export
- Reproducible synthetic 10% canary; no API keys or paid services
- 23 tests and a Python 3.11–3.13 CI matrix

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
python -m promptharbor.cli --json report.json --csv audit.csv
```

The demo registers a stable and candidate bundle, attaches synthetic evaluation evidence, records independent approval, sends 10% of 1,000 deterministic request keys to the candidate, and rolls it back only after the observed quality drop has enough samples and its one-sided confidence bound exceeds the allowed drop.

## Core workflow

1. Register a semantic version and release rationale.
2. Evaluate the exact configuration manifest and attach its digest.
3. Collect approval from someone other than the author.
4. Promote to a bounded canary.
5. Compare candidate and stable quality; roll back only when the confidence-bounded drop exceeds the permitted threshold.
6. Export the audit trail for review.

## Configuration-bundle experiment

The test suite takes valid evidence and independently changes the prompt, model settings, retrieval configuration, and tool schema. All **4/4** scoped changes invalidate the evidence. A control test shows that an intentionally unscoped dependency does not invalidate it. This is useful for narrow edits, but the scope is itself visible and defaults to the safer full manifest.

## Sequential-canary experiment

The predeclared policy requires at least 30 samples in each cohort, limits a canary to 20 statistical looks, and divides a 5% family error budget across those looks. A deterministic 200-trial equal-quality simulation remains within the declared false-rollback budget. A noisy fixture whose point estimate exceeds the 5% drop threshold continues because its confidence bound is inconclusive; the seeded 37-point regression rolls back with 894 stable and 106 candidate samples.

## Design boundaries

This is a portfolio-scale policy engine, not a production control plane. Metrics are supplied by callers; the demo uses synthetic quality scores. Storage is in memory, authentication is represented by actor strings, approval policy is single-reviewer, and semantic versions are validated but not ordered. The normal approximation and Bonferroni look budget are transparent controls, not a substitute for a production experiment design. See [Method and limitations](docs/METHOD.md), [feature backlog](docs/BACKLOG.md), and [rotation progress](docs/PROGRESS.md).

## Repository map

```text
promptharbor/core.py   Registry, evidence, routing, rollback
promptharbor/cli.py    Reproducible end-to-end simulation
tests/                 Policy and behavior tests
docs/                  Method, limitations, prioritized backlog
```

## License

MIT

