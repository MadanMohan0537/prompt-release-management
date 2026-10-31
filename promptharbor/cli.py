"""Reproducible synthetic release simulation."""
import argparse, csv, json
from pathlib import Path
from .core import Bundle, Evidence, Registry, ReleaseManager, Sample

def demo() -> tuple[dict, Registry]:
    registry = Registry()
    base = Bundle("Answer with cited facts.", {"name":"local-demo","temperature":0}, {"top_k":3}, [{"name":"search","schema":{"q":"string"}}])
    bad = Bundle("Guess a short answer.", {"name":"local-demo","temperature":1}, {"top_k":1}, [{"name":"search","schema":{}}])
    registry.register("1.0.0", base, "pm", "Initial verified release")
    registry.register("1.1.0", bad, "pm", "Test a shorter response style")
    registry.attach_evidence("1.1.0", Evidence(bad.digest, "synthetic-grounding-v1", .86, 40))
    registry.approve("1.1.0", "risk-reviewer")
    manager = ReleaseManager(registry); manager.stable = "1.0.0"; manager.promote("1.1.0", 10)
    samples = [Sample(str(i), manager.route(str(i)), .55 if manager.route(str(i)) == "1.1.0" else .92) for i in range(1000)]
    decision = manager.observe_report(samples)
    rolled_back = decision["decision"] == "rollback"
    canary_count = sum(s.version == "1.1.0" for s in samples)
    return {"product":"PromptHarbor","stable":"1.0.0","candidate":"1.1.0","requests":len(samples),"canary_requests":canary_count,"rolled_back":rolled_back,"canary_decision":decision,"diff":registry.diff("1.0.0","1.1.0")}, registry

def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("--json", type=Path); p.add_argument("--csv", type=Path); args=p.parse_args()
    report, registry = demo()
    if args.json: args.json.write_text(json.dumps(report, indent=2)+"\n")
    if args.csv:
        with args.csv.open("w", newline="") as f:
            w=csv.DictWriter(f, fieldnames=["at","event","version","actor","digest","score","percent","quality_drop","lower_bound","stable_samples","candidate_samples","look"], extrasaction="ignore"); w.writeheader(); w.writerows(registry.audit)
    print(json.dumps(report, indent=2))
if __name__ == "__main__": main()

