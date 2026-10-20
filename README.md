# Prompt Release Management

[![CI](https://github.com/MadanMohan0537/prompt-release-management/actions/workflows/ci.yml/badge.svg)](https://github.com/MadanMohan0537/prompt-release-management/actions/workflows/ci.yml)

A local Python engine for changing prompts with a numeric version, a review by someone other than the author, evaluation evidence tied to a digest, a deterministic canary, and rollback when observed mean quality drops.

The runtime uses only the Python standard library. The installable package, the import package, and the CLI are still named `promptharbor`. The demo report's `product` field is still `PromptHarbor`.

## Problem and who it's for

A prompt change is rarely just text. Model parameters, retrieval settings, and tool schemas change behavior just as much. If reviewers look only at the prompt, evaluation evidence goes stale and unsafe releases get through. This is for teams running LLM features in production, and for the AI PMs and release owners who approve those changes.

## Approach

- Register one bundle of the prompt, model settings, retrieval configuration, and tool schemas, with a numeric `major.minor.patch` label and a non-empty rationale. `diff` prints a unified diff of two stored bundles. That diff is the full bundle, including dependency scope, not only the scoped document that is hashed.
- Store evaluation evidence against the SHA-256 digest of the scoped manifest (canonical JSON). Changing a scoped field changes the digest, so later promotion rejects that evidence.
- Reject approval by the author. Promotion requires at least one other approval, evidence whose digest still matches, a score at or above the minimum (default 0.8), and at least one case.
- Send a percentage of SHA-256 hash buckets to the candidate. The same request key stays on the same version. When the caller passes samples to `observe`, a drop in mean quality greater than the allowed amount (default 0.05), with both cohorts present, clears the candidate and records `auto_rollback`.
- The CLI can write a JSON release report and a CSV audit trail.

## What exists today

- A registry of numeric `major.minor.patch` labels. Empty rationales and duplicate labels are rejected. Labels are not ordered, and pre-release tags are rejected.
- Evidence checked against the manifest digest. One test changes the prompt, model settings, retrieval settings, and tool schema; all four changes fail validation. A second test keeps the evidence valid when a field outside a narrower scope changes. The scope is a field on the bundle and defaults to all four inputs.
- The author cannot approve their own release. Promotion is refused with no approval, a digest that does not match, or a score below the minimum.
- The CLI demo registers `1.0.0` and `1.1.0`, attaches synthetic evidence and a non-author approval to `1.1.0` only, and sets `1.0.0` as stable by assignment. It routes 1,000 deterministic keys (`"0"` through `"999"`) with a 10% canary target. 106 of those keys go to the candidate. Candidate samples score 0.55 and stable samples score 0.92, so the recorded drop is 0.37 and the candidate is rolled back.
- 16 unit tests in `tests/test_core.py`. [`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs those tests and the CLI on Python 3.11, 3.12, and 3.13.

## How success would be measured

This repository does not contain measured production outcomes. The tests and the synthetic demo above exercise the engine locally. They are not measurements of the following.

| Measure | Status |
|---|---|
| Behavior-changing edits that invalidate stale evidence | Not yet measured |
| Regressions caught at canary stage instead of full rollout | Not yet measured |
| Time from a quality drop to rollback | Not yet measured |
| Releases shipped without independent approval | Not yet measured |

## Limitations

- A small in-memory policy engine, not a production control plane.
- Quality metrics are supplied by the caller. The demo uses synthetic scores. Rollback compares cohort means and does not apply a sample floor or a confidence interval.
- Storage is in memory, actors are strings, and one reviewer other than the author is enough to promote.
- Version labels are checked for three numeric parts, then stored as strings. They are not ordered.
- Hash routing keeps a key on one version. It is not a feature-flag service, and nothing here promotes a canary to stable.
- Calling `observe` is what triggers rollback. There is no running monitor.

See [docs/METHOD.md](docs/METHOD.md) and [docs/BACKLOG.md](docs/BACKLOG.md). Items marked planned or explored in the backlog are not in this tree.

## Quick start

Requires Python 3.11 or newer. No API keys or paid services. On a machine where `python` is not on `PATH`, `python3` is the interpreter, including for the virtualenv step below. After activation, `python` in the virtualenv is that same interpreter. The workflow calls `python`.

```bash
git clone https://github.com/MadanMohan0537/prompt-release-management.git
cd prompt-release-management
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
python -m promptharbor.cli --json report.json --csv audit.csv
```

The last command prints the JSON report. `--json` and `--csv` also write `report.json` and `audit.csv`, which are listed in `.gitignore`. The installed console script has the same name: `promptharbor`.

## Deployment

Cloudflare Workers is the planned target. It is not configured in this repository, and this project is not deployed.

There is no `wrangler.toml` and no Worker entry point. What is needed before a deploy:

- `wrangler.toml`
- a Worker entry point
- Python Workers, or a JavaScript/TypeScript port

When that configuration exists, the deploy command is:

```bash
npx wrangler deploy
```

## Repository map

```text
promptharbor/core.py   registry, evidence, routing, rollback
promptharbor/cli.py    reproducible end-to-end simulation
tests/                 policy and behavior tests
docs/                  method, limitations, backlog
```

## License

MIT. See [LICENSE](LICENSE).
