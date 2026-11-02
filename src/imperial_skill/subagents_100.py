"""Original IMPERIAL Core data-only fleet planner.
Copyright (c) 2026 Alexander Nikolaevich Romaskevich.
No processes, model calls, external operations or actual identities are created.
"""
from __future__ import annotations
import hashlib
import re
from .manifest import DOMAINS, IDENT, SHA256, canonical_json

MISSION_FIELDS = frozenset({
    "schema", "tenant_id", "orchestrator_id", "runtime_domain", "mission_id",
    "source_sha256", "agent_count", "max_parallel", "owner_kill_switch_engaged",
    "external_effects", "spending_usd",
})
SQUADS = (
    "requirements", "software-engineering", "independent-review", "defensive-security",
    "integration", "data-quality", "reliability", "documentation", "performance", "research",
)
_ID = re.compile(r"^NCA-SUB-(?:0[0-9]{2}|100)$")


class FleetSkillError(ValueError):
    """Fail-closed fleet plan or synthetic evidence violation."""


def _mission(value: object) -> dict:
    if type(value) is not dict or set(value) != MISSION_FIELDS:
        raise FleetSkillError("MISSION_SCHEMA_DENIED")
    if value["schema"] != "imperial.skill.subagents-100.mission.v1":
        raise FleetSkillError("MISSION_VERSION_DENIED")
    for name in ("tenant_id", "orchestrator_id", "mission_id"):
        if type(value[name]) is not str or not IDENT.fullmatch(value[name]):
            raise FleetSkillError("FEDERATION_IDENTITY_DENIED")
    if type(value["runtime_domain"]) is not str or value["runtime_domain"] not in DOMAINS:
        raise FleetSkillError("RUNTIME_DOMAIN_DENIED")
    if type(value["source_sha256"]) is not str or not SHA256.fullmatch(value["source_sha256"]):
        raise FleetSkillError("SOURCE_INTEGRITY_REQUIRED")
    if type(value["agent_count"]) is not int or value["agent_count"] != 100:
        raise FleetSkillError("EXACTLY_100_SUBAGENTS_REQUIRED")
    if type(value["max_parallel"]) is not int or not 1 <= value["max_parallel"] <= 10:
        raise FleetSkillError("CONCURRENCY_CAP_DENIED")
    if (value["owner_kill_switch_engaged"] is not True or
        value["external_effects"] is not False or
        type(value["spending_usd"]) is not int or value["spending_usd"] != 0):
        raise FleetSkillError("DENY_BY_DEFAULT_REQUIRED")
    canonical_json(value)
    return dict(value)


def plan_subagents_100(mission: object) -> dict:
    """Plan exactly ten ten-member squads; no worker is deployed."""
    m = _mission(mission)
    roster = []
    for index in range(100):
        agent_id = f"NCA-SUB-{index + 1:03d}"
        squad = SQUADS[index // 10]
        slot = index % 10 + 1
        task_sha256 = hashlib.sha256(
            f"{m['mission_id']}:{m['source_sha256']}:{agent_id}:{squad}".encode("ascii")
        ).hexdigest()
        roster.append({"agent_id": agent_id, "squad": squad, "slot": slot,
                       "task_sha256": task_sha256, "state": "PLANNED_ONLY"})
    policy = {
        "schema": "imperial.skill.subagents-100.plan.v1", "mission": m,
        "agent_count": 100, "squad_count": 10, "max_parallel": m["max_parallel"],
        "roster": roster, "stage": "PLAN_ONLY", "owner_kill_switch_engaged": True,
        "owner_approval_verified": False, "ai_passport_verified": False,
        "guardian_admission_verified": False, "independent_qa_verified": False,
        "model_called": False, "worker_started": False,
        "execution_authorized": False, "production_authorized": False,
        "external_effects": False, "spending_usd": 0,
    }
    return {**policy, "plan_sha256": hashlib.sha256(canonical_json(policy)).hexdigest()}


def _verified_plan(plan: object) -> dict:
    if type(plan) is not dict or set(plan) != {
        "schema", "mission", "agent_count", "squad_count", "max_parallel", "roster",
        "stage", "owner_kill_switch_engaged", "owner_approval_verified",
        "ai_passport_verified", "guardian_admission_verified", "independent_qa_verified",
        "model_called", "worker_started", "execution_authorized",
        "production_authorized", "external_effects", "spending_usd", "plan_sha256",
    }:
        raise FleetSkillError("PLAN_SCHEMA_DENIED")
    expected = plan_subagents_100(plan["mission"])
    if canonical_json(plan) != canonical_json(expected):
        raise FleetSkillError("PLAN_TAMPERING_OR_PRIVILEGE_ESCALATION_DENIED")
    return expected


def plan_batches(plan: object) -> dict:
    """Compute bounded batches; does not submit actual jobs."""
    p = _verified_plan(plan)
    cap = p["max_parallel"]
    batches = [[agent["agent_id"] for agent in p["roster"][i:i + cap]]
               for i in range(0, 100, cap)]
    return {"plan_sha256": p["plan_sha256"], "batches": batches,
            "batch_count": len(batches), "max_parallel": cap,
            "jobs_dispatched": 0, "execution_authorized": False}


def review_synthetic_receipts(plan: object, receipts: object) -> dict:
    """Validate untrusted synthetic hashes, never certify independent QA."""
    p = _verified_plan(plan)
    if type(receipts) is not list or len(receipts) > 100:
        raise FleetSkillError("RECEIPT_COUNT_DENIED")
    indexed = {agent["agent_id"]: agent for agent in p["roster"]}
    seen = set()
    redacted = []
    for receipt in receipts:
        if type(receipt) is not dict or set(receipt) != {
            "agent_id", "task_sha256", "artifact_sha256", "status",
        }:
            raise FleetSkillError("RECEIPT_SCHEMA_DENIED")
        agent_id = receipt["agent_id"]
        if type(agent_id) is not str or not _ID.fullmatch(agent_id):
            raise FleetSkillError("RECEIPT_ID_DENIED")
        if agent_id in seen or agent_id not in indexed:
            raise FleetSkillError("DUPLICATE_OR_UNREGISTERED_AGENT_DENIED")
        seen.add(agent_id)
        if receipt["task_sha256"] != indexed[agent_id]["task_sha256"]:
            raise FleetSkillError("TASK_SCOPE_MISMATCH")
        if (type(receipt["artifact_sha256"]) is not str or
            not SHA256.fullmatch(receipt["artifact_sha256"]) or
            receipt["status"] != "SYNTHETIC_ONLY"):
            raise FleetSkillError("UNTRUSTED_EVIDENCE_OR_STATUS_DENIED")
        redacted.append({"agent_id": agent_id, "task_sha256": receipt["task_sha256"],
                         "artifact_sha256": receipt["artifact_sha256"]})
    canonical_json(redacted)
    return {
        "schema": "imperial.skill.subagents-100.review.v1",
        "plan_sha256": p["plan_sha256"],
        "synthetic_receipts_received": len(seen),
        "receipts_missing": 100 - len(seen),
        "all_synthetic_receipts_present": len(seen) == 100,
        "submitted_receipt_sha256": hashlib.sha256(canonical_json(redacted)).hexdigest(),
        "independent_qa_verified": False, "professional_certified": False,
        "ai_passport_verified": False, "execution_authorized": False,
        "production_authorized": False, "spending_usd": 0,
    }
