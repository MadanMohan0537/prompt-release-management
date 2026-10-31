import unittest
import random
from dataclasses import replace
from promptharbor.core import Bundle, Evidence, Registry, ReleaseManager, Sample

def bundle(): return Bundle("Be accurate", {"name":"demo","temperature":0}, {"top_k":3}, [{"name":"search","schema":{"q":"str"}}])

class TestPromptHarbor(unittest.TestCase):
    def test_digest_deterministic(self): self.assertEqual(bundle().digest, bundle().digest)
    def test_each_dependency_invalidates_evidence(self):
        b=bundle(); e=Evidence(b.digest,"suite",.9,10)
        changes=[replace(b,prompt="Changed"),replace(b,model={"name":"other"}),replace(b,retrieval={"top_k":9}),replace(b,tools=[])]
        self.assertTrue(e.validates(b,.8)); self.assertTrue(all(not e.validates(x,.8) for x in changes))
    def test_explicit_scope_ignores_unscoped_change(self):
        b=replace(bundle(), dependency_scope=("prompt",)); e=Evidence(b.digest,"suite",.9,10)
        self.assertTrue(e.validates(replace(b,model={"name":"new"}),.8))
    def test_bad_scope(self):
        with self.assertRaises(ValueError): replace(bundle(), dependency_scope=("unknown",))
    def test_semver_required(self):
        with self.assertRaises(ValueError): Registry().register("v1",bundle(),"a","why")
    def test_rationale_required(self):
        with self.assertRaises(ValueError): Registry().register("1.0.0",bundle(),"a","")
    def test_duplicate_rejected(self):
        r=Registry(); r.register("1.0.0",bundle(),"a","why")
        with self.assertRaises(ValueError): r.register("1.0.0",bundle(),"a","why")
    def test_author_cannot_approve(self):
        r=Registry(); r.register("1.0.0",bundle(),"a","why")
        with self.assertRaises(ValueError): r.approve("1.0.0","a")
    def test_promotion_requires_approval(self):
        r=Registry(); b=bundle(); r.register("1.0.0",b,"a","why"); r.attach_evidence("1.0.0",Evidence(b.digest,"s",.9,1))
        with self.assertRaises(ValueError): ReleaseManager(r).promote("1.0.0")
    def test_promotion_rejects_stale_evidence(self):
        r=Registry(); b=bundle(); r.register("1.0.0",b,"a","why"); r.attach_evidence("1.0.0",Evidence("stale","s",.9,1)); r.approve("1.0.0","b")
        with self.assertRaises(ValueError): ReleaseManager(r).promote("1.0.0")
    def test_promotion_rejects_low_score(self):
        r=Registry(); b=bundle(); r.register("1.0.0",b,"a","why"); r.attach_evidence("1.0.0",Evidence(b.digest,"s",.2,1)); r.approve("1.0.0","b")
        with self.assertRaises(ValueError): ReleaseManager(r).promote("1.0.0")
    def test_route_is_deterministic(self):
        r=Registry(); b=bundle(); r.register("1.0.0",b,"a","why"); r.attach_evidence("1.0.0",Evidence(b.digest,"s",.9,1)); r.approve("1.0.0","b"); m=ReleaseManager(r); m.stable="0.9.0"; m.promote("1.0.0")
        self.assertEqual(m.route("user-1"),m.route("user-1"))
    def test_rollback_on_drop(self):
        r=Registry(); b=bundle(); r.register("1.0.0",b,"a","why"); r.attach_evidence("1.0.0",Evidence(b.digest,"s",.9,1)); r.approve("1.0.0","b"); m=ReleaseManager(r); m.stable="0.9.0"; m.promote("1.0.0")
        samples=[Sample(f"s{i}","0.9.0",.9) for i in range(30)]+[Sample(f"c{i}","1.0.0",.5) for i in range(30)]
        self.assertTrue(m.observe(samples)); self.assertIsNone(m.candidate)
    def test_no_rollback_without_both_cohorts(self):
        r=Registry(); m=ReleaseManager(r); m.stable="a"; m.candidate="b"; self.assertFalse(m.observe([Sample("1","a",.9)]))
    def test_diff_names_versions(self):
        r=Registry(); r.register("1.0.0",bundle(),"a","why"); r.register("1.1.0",replace(bundle(),prompt="new"),"a","why")
        self.assertIn("--- 1.0.0",r.diff("1.0.0","1.1.0"))
    def test_audit_records_actions(self):
        r=Registry(); r.register("1.0.0",bundle(),"a","why"); self.assertEqual("registered",r.audit[0]["event"])

    def test_sample_quality_must_be_bounded_and_finite(self):
        for value in (-.1, 1.1, float("nan"), float("inf")):
            with self.assertRaises(ValueError): Sample("x", "v", value)

    def test_sample_floor_reports_exact_gaps(self):
        m=ReleaseManager(Registry(), minimum_samples=30); m.stable="stable"; m.candidate="candidate"
        report=m.observe_report([Sample(f"s{i}","stable",.9) for i in range(28)]+[Sample(f"c{i}","candidate",.8) for i in range(7)])
        self.assertEqual("insufficient_data",report["decision"])
        self.assertEqual(2,report["additional_stable_needed"])
        self.assertEqual(23,report["additional_candidate_needed"])
        self.assertEqual(0,m.observation_looks)

    def test_uncertain_point_drop_does_not_rollback(self):
        m=ReleaseManager(Registry()); m.stable="stable"; m.candidate="candidate"
        stable=[Sample(f"s{i}","stable",.8 if i%2 else 1.0) for i in range(30)]
        candidate=[Sample(f"c{i}","candidate",.74 if i%2 else .94) for i in range(30)]
        report=m.observe_report(stable+candidate)
        self.assertGreater(report["observed_drop"],.05)
        self.assertLessEqual(report["one_sided_lower_bound"],.05)
        self.assertEqual("continue",report["decision"])

    def test_null_simulation_stays_within_declared_false_rollback_budget(self):
        rng=random.Random(17); false_rollbacks=0; trials=200
        for trial in range(trials):
            m=ReleaseManager(Registry()); m.stable="stable"; m.candidate="candidate"
            stable=[Sample(f"{trial}-s{i}","stable",min(1,max(0,rng.gauss(.85,.08)))) for i in range(60)]
            candidate=[Sample(f"{trial}-c{i}","candidate",min(1,max(0,rng.gauss(.85,.08)))) for i in range(60)]
            false_rollbacks += m.observe(stable+candidate)
        self.assertLessEqual(false_rollbacks/trials,.05)

    def test_sequential_look_budget_requires_manual_review(self):
        m=ReleaseManager(Registry(),maximum_looks=1); m.stable="stable"; m.candidate="candidate"
        samples=[Sample(f"s{i}","stable",.9) for i in range(30)]+[Sample(f"c{i}","candidate",.88) for i in range(30)]
        self.assertEqual("continue",m.observe_report(samples)["decision"])
        self.assertEqual("manual_review",m.observe_report(samples)["decision"])

    def test_rollback_audit_records_evidence_denominators(self):
        r=Registry(); m=ReleaseManager(r); m.stable="stable"; m.candidate="candidate"
        samples=[Sample(f"s{i}","stable",.9) for i in range(30)]+[Sample(f"c{i}","candidate",.5) for i in range(30)]
        self.assertTrue(m.observe(samples))
        event=r.audit[-1]
        self.assertEqual(30,event["stable_samples"])
        self.assertEqual(30,event["candidate_samples"])
        self.assertIn("lower_bound",event)

    def test_canary_statistics_parameters_are_validated(self):
        with self.assertRaises(ValueError): ReleaseManager(Registry(),minimum_samples=1)
        with self.assertRaises(ValueError): ReleaseManager(Registry(),family_error_rate=1)
        with self.assertRaises(ValueError): ReleaseManager(Registry(),maximum_looks=0)

if __name__ == "__main__": unittest.main()

