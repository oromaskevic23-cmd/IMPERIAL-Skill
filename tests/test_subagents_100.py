"""Fail-closed tests for an offline fleet of 100 symbolic NCA plans."""
import copy
import hashlib
import unittest
from imperial_skill.subagents_100 import (
    FleetSkillError, plan_subagents_100, plan_batches, review_synthetic_receipts,
)

def mission(**changes):
    data = {
        "schema": "imperial.skill.subagents-100.mission.v1",
        "tenant_id": "imperial-internal", "orchestrator_id": "engineering-orch",
        "runtime_domain": "CODE_ENGINEERING", "mission_id": "TASK-100",
        "source_sha256": "a"*64, "agent_count": 100, "max_parallel": 10,
        "owner_kill_switch_engaged": True, "external_effects": False, "spending_usd": 0,
    }
    return {**data, **changes}

class Subagents100Tests(unittest.TestCase):
    def test_exactly_100_unique_identities_ten_squads(self):
        p = plan_subagents_100(mission())
        self.assertEqual(len(p["roster"]), 100)
        self.assertEqual(len({a["agent_id"] for a in p["roster"]}), 100)
        self.assertEqual(p["roster"][0]["agent_id"], "NCA-SUB-001")
        self.assertEqual(p["roster"][-1]["agent_id"], "NCA-SUB-100")
        self.assertEqual(len({a["squad"] for a in p["roster"]}), 10)
        self.assertTrue(all(sum(a["squad"] == s for a in p["roster"]) == 10
                            for s in {a["squad"] for a in p["roster"]}))

    def test_determinism(self):
        self.assertEqual(plan_subagents_100(mission()), plan_subagents_100(mission()))

    def test_no_runtime_privileges(self):
        p = plan_subagents_100(mission())
        for key in ("owner_approval_verified", "ai_passport_verified",
                    "guardian_admission_verified", "independent_qa_verified",
                    "model_called", "worker_started", "execution_authorized",
                    "production_authorized", "external_effects"):
            self.assertIs(p[key], False)
        self.assertIs(p["owner_kill_switch_engaged"], True)
        self.assertEqual(p["spending_usd"], 0)
        self.assertTrue(all(a["state"] == "PLANNED_ONLY" for a in p["roster"]))

    def test_batch_cap(self):
        for cap in (1, 3, 10):
            b = plan_batches(plan_subagents_100(mission(max_parallel=cap)))
            self.assertEqual(sum(map(len,b["batches"])), 100)
            self.assertTrue(all(1 <= len(x) <= cap for x in b["batches"]))
            self.assertEqual(b["jobs_dispatched"], 0)

    def test_agent_count_and_concurrency_denial(self):
        for changes in ({"agent_count":99},{"agent_count":101},
                        {"agent_count":True},{"max_parallel":0},
                        {"max_parallel":11},{"max_parallel":True}):
            with self.subTest(changes=changes),self.assertRaises(FleetSkillError):
                plan_subagents_100(mission(**changes))

    def test_kill_switch_budget_and_external_effects_denial(self):
        for changes in ({"owner_kill_switch_engaged":False},
                        {"external_effects":True},{"spending_usd":1},
                        {"spending_usd":False}):
            with self.subTest(changes=changes),self.assertRaises(FleetSkillError):
                plan_subagents_100(mission(**changes))

    def test_federation_schema_and_scope_denial(self):
        for changes in ({"tenant_id":"x"},{"orchestrator_id":""},
                        {"runtime_domain":"CRYPTO_IMPERIAL"},
                        {"mission_id":"bad/.."},{"source_sha256":"short"},
                        {"unknown":True},{"schema":"unknown"}):
            with self.subTest(changes=changes),self.assertRaises(FleetSkillError):
                plan_subagents_100(mission(**changes))

    def test_separate_missions_have_separate_task_hashes(self):
        p = plan_subagents_100(mission())
        q = plan_subagents_100(mission(mission_id="TASK-101"))
        self.assertNotEqual(p["roster"][0]["task_sha256"],q["roster"][0]["task_sha256"])

    def test_plan_tampering_denied(self):
        p = plan_subagents_100(mission())
        for key, value in (("execution_authorized",True),
                           ("owner_kill_switch_engaged",False),
                           ("agent_count",101),("plan_sha256","0"*64)):
            altered = copy.deepcopy(p)
            altered[key] = value
            with self.subTest(key=key),self.assertRaises(FleetSkillError):
                plan_batches(altered)
        altered = copy.deepcopy(p)
        altered["roster"][0]["state"] = "RUNNING"
        with self.assertRaises(FleetSkillError):
            review_synthetic_receipts(altered,[])

    def test_complete_synthetic_receipts_not_independent_qa(self):
        p = plan_subagents_100(mission())
        receipts = [
            {"agent_id":a["agent_id"],"task_sha256":a["task_sha256"],
             "artifact_sha256":hashlib.sha256(a["agent_id"].encode()).hexdigest(),
             "status":"SYNTHETIC_ONLY"} for a in p["roster"]
        ]
        r = review_synthetic_receipts(p, receipts)
        self.assertEqual(r["synthetic_receipts_received"],100)
        self.assertEqual(r["receipts_missing"],0)
        self.assertTrue(r["all_synthetic_receipts_present"])
        self.assertFalse(r["independent_qa_verified"])
        self.assertFalse(r["execution_authorized"])

    def test_missing_receipts_visible(self):
        r = review_synthetic_receipts(plan_subagents_100(mission()),[])
        self.assertEqual(r["receipts_missing"],100)
        self.assertFalse(r["all_synthetic_receipts_present"])

    def test_duplicate_receipt_and_wrong_task_denied(self):
        p = plan_subagents_100(mission())
        receipt = {"agent_id":"NCA-SUB-001",
                   "task_sha256":p["roster"][0]["task_sha256"],
                   "artifact_sha256":"f"*64,"status":"SYNTHETIC_ONLY"}
        with self.assertRaises(FleetSkillError):
            review_synthetic_receipts(p,[receipt,receipt])
        with self.assertRaises(FleetSkillError):
            review_synthetic_receipts(p,[{**receipt,"task_sha256":"0"*64}])

    def test_fake_evidence_and_extra_data_denied(self):
        p=plan_subagents_100(mission())
        receipt={"agent_id":"NCA-SUB-001",
                 "task_sha256":p["roster"][0]["task_sha256"],
                 "artifact_sha256":"f"*64,"status":"SYNTHETIC_ONLY"}
        for bad in ({**receipt,"status":"QA_PASS"},
                    {**receipt,"owner_approved":True},
                    {**receipt,"artifact_sha256":"x"},
                    {**receipt,"agent_id":"NCA-SUB-101"}):
            with self.subTest(bad=bad),self.assertRaises(FleetSkillError):
                review_synthetic_receipts(p,[bad])
        with self.assertRaises(FleetSkillError):
            review_synthetic_receipts(p,[receipt]*101)

if __name__ == "__main__":
    unittest.main()
