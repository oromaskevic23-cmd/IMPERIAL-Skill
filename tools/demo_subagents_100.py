"""Offline demonstration, not 100 running agents."""
import json
from imperial_skill.subagents_100 import (
    plan_subagents_100, plan_batches, review_synthetic_receipts,
)

def main():
    mission = {
        "schema": "imperial.skill.subagents-100.mission.v1",
        "tenant_id": "imperial-internal", "orchestrator_id": "engineering-orch",
        "runtime_domain": "CODE_ENGINEERING", "mission_id": "DEMO-SUB-100",
        "source_sha256": "a"*64, "agent_count":100, "max_parallel":10,
        "owner_kill_switch_engaged":True,"external_effects":False,"spending_usd":0,
    }
    plan=plan_subagents_100(mission)
    batches=plan_batches(plan)
    review=review_synthetic_receipts(plan,[])
    print(json.dumps({
        "plan_sha256":plan["plan_sha256"],
        "symbolic_subagents":plan["agent_count"],
        "squads":plan["squad_count"],
        "planned_batches":batches["batch_count"],
        "dispatched_workers":batches["jobs_dispatched"],
        "synthetic_receipts_missing":review["receipts_missing"],
        "execution_authorized":False,"production_authorized":False,
    },indent=2))

if __name__ == "__main__":
    main()
