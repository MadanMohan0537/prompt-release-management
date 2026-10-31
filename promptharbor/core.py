"""Dependency-free prompt release primitives."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from difflib import unified_diff
import hashlib
import json
import math
from statistics import NormalDist, mean, variance
from typing import Any

ALL_DEPENDENCIES = ("prompt", "model", "retrieval", "tools")

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

@dataclass(frozen=True)
class Bundle:
    prompt: str
    model: dict[str, Any]
    retrieval: dict[str, Any]
    tools: list[dict[str, Any]]
    dependency_scope: tuple[str, ...] = ALL_DEPENDENCIES

    def __post_init__(self) -> None:
        bad = set(self.dependency_scope) - set(ALL_DEPENDENCIES)
        if bad or not self.dependency_scope:
            raise ValueError(f"invalid dependency scope: {sorted(bad)}")

    def manifest(self) -> dict[str, Any]:
        return {name: getattr(self, name) for name in self.dependency_scope}

    @property
    def digest(self) -> str:
        raw = json.dumps(self.manifest(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode()).hexdigest()

@dataclass(frozen=True)
class Evidence:
    bundle_digest: str
    suite: str
    score: float
    cases: int

    def validates(self, bundle: Bundle, minimum: float) -> bool:
        return self.bundle_digest == bundle.digest and self.cases > 0 and self.score >= minimum

@dataclass(frozen=True)
class Sample:
    route_key: str
    version: str
    quality: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.quality) or not 0 <= self.quality <= 1:
            raise ValueError("quality must be finite and between 0 and 1")

@dataclass
class Version:
    number: str
    bundle: Bundle
    author: str
    rationale: str
    evidence: Evidence | None = None
    approvals: set[str] = field(default_factory=set)

class Registry:
    def __init__(self) -> None:
        self.versions: dict[str, Version] = {}
        self.audit: list[dict[str, Any]] = []

    def register(self, number: str, bundle: Bundle, author: str, rationale: str) -> Version:
        if number in self.versions or not rationale.strip():
            raise ValueError("version must be unique and rationale non-empty")
        parts = number.split(".")
        if len(parts) != 3 or not all(x.isdigit() for x in parts):
            raise ValueError("version must use numeric semantic versioning")
        item = Version(number, bundle, author, rationale)
        self.versions[number] = item
        self._log("registered", number, author, digest=bundle.digest)
        return item

    def attach_evidence(self, number: str, evidence: Evidence) -> None:
        self.versions[number].evidence = evidence
        self._log("evidence_attached", number, "system", score=evidence.score)

    def approve(self, number: str, reviewer: str) -> None:
        item = self.versions[number]
        if reviewer == item.author:
            raise ValueError("author cannot approve a customer-facing release")
        item.approvals.add(reviewer)
        self._log("approved", number, reviewer)

    def diff(self, old: str, new: str) -> str:
        a = json.dumps(asdict(self.versions[old].bundle), indent=2, sort_keys=True).splitlines()
        b = json.dumps(asdict(self.versions[new].bundle), indent=2, sort_keys=True).splitlines()
        return "\n".join(unified_diff(a, b, fromfile=old, tofile=new, lineterm=""))

    def _log(self, event: str, version: str, actor: str, **details: Any) -> None:
        self.audit.append({"at": _now(), "event": event, "version": version, "actor": actor, **details})

class ReleaseManager:
    def __init__(
        self,
        registry: Registry,
        minimum_score: float = .8,
        minimum_samples: int = 30,
        family_error_rate: float = .05,
        maximum_looks: int = 20,
    ) -> None:
        if minimum_samples < 2:
            raise ValueError("minimum_samples must be at least 2")
        if not 0 < family_error_rate < 1:
            raise ValueError("family_error_rate must be between 0 and 1")
        if maximum_looks < 1:
            raise ValueError("maximum_looks must be positive")
        self.registry = registry
        self.minimum_score = minimum_score
        self.minimum_samples = minimum_samples
        self.family_error_rate = family_error_rate
        self.maximum_looks = maximum_looks
        self.stable: str | None = None
        self.candidate: str | None = None
        self.percent = 0
        self.observation_looks = 0
        self.last_observation: dict[str, Any] | None = None

    def promote(self, version: str, percent: int = 10) -> None:
        item = self.registry.versions[version]
        if not item.approvals:
            raise ValueError("reviewer approval required")
        if item.evidence is None or not item.evidence.validates(item.bundle, self.minimum_score):
            raise ValueError("current passing evaluation evidence required")
        if not 1 <= percent <= 100:
            raise ValueError("canary percent must be 1..100")
        self.candidate, self.percent = version, percent
        self.observation_looks = 0
        self.last_observation = None
        self.registry._log("canary_started", version, "system", percent=percent)

    def route(self, key: str) -> str:
        if not self.stable:
            raise ValueError("stable version is not configured")
        bucket = int(hashlib.sha256(key.encode()).hexdigest()[:8], 16) % 100
        return self.candidate if self.candidate and bucket < self.percent else self.stable

    def observe_report(self, samples: list[Sample], max_drop: float = .05) -> dict[str, Any]:
        if not 0 <= max_drop <= 1:
            raise ValueError("max_drop must be between 0 and 1")
        if not self.candidate or not self.stable:
            report = {"decision": "inactive", "reason": "stable and candidate versions are required"}
            self.last_observation = report
            return report
        candidate = [s.quality for s in samples if s.version == self.candidate]
        stable = [s.quality for s in samples if s.version == self.stable]
        base = {
            "stable_samples": len(stable),
            "candidate_samples": len(candidate),
            "minimum_samples": self.minimum_samples,
            "max_drop": max_drop,
        }
        if len(candidate) < self.minimum_samples or len(stable) < self.minimum_samples:
            report = {
                **base,
                "decision": "insufficient_data",
                "additional_stable_needed": max(0, self.minimum_samples - len(stable)),
                "additional_candidate_needed": max(0, self.minimum_samples - len(candidate)),
            }
            self.last_observation = report
            return report
        if self.observation_looks >= self.maximum_looks:
            report = {**base, "decision": "manual_review", "reason": "maximum sequential looks exhausted"}
            self.last_observation = report
            return report

        self.observation_looks += 1
        drop = mean(stable) - mean(candidate)
        standard_error = math.sqrt(variance(stable) / len(stable) + variance(candidate) / len(candidate))
        alpha_per_look = self.family_error_rate / self.maximum_looks
        critical_value = NormalDist().inv_cdf(1 - alpha_per_look)
        lower_bound = drop - critical_value * standard_error
        report = {
            **base,
            "decision": "rollback" if lower_bound > max_drop else "continue",
            "look": self.observation_looks,
            "maximum_looks": self.maximum_looks,
            "family_error_rate": self.family_error_rate,
            "alpha_per_look": round(alpha_per_look, 6),
            "observed_drop": round(drop, 6),
            "standard_error": round(standard_error, 6),
            "one_sided_lower_bound": round(lower_bound, 6),
        }
        if report["decision"] == "rollback":
            failed = self.candidate
            self.candidate, self.percent = None, 0
            self.registry._log(
                "auto_rollback",
                failed,
                "monitor",
                quality_drop=round(drop, 4),
                lower_bound=round(lower_bound, 4),
                stable_samples=len(stable),
                candidate_samples=len(candidate),
                look=self.observation_looks,
            )
        self.last_observation = report
        return report

    def observe(self, samples: list[Sample], max_drop: float = .05) -> bool:
        """Backward-compatible boolean wrapper around the evidence report."""
        return self.observe_report(samples, max_drop)["decision"] == "rollback"

