"""Federated, immutable Enterprise Skills catalog with dependency DAG resolution."""
from __future__ import annotations
import copy
import hashlib
from .manifest import SkillValidationError, validate_manifest, canonical_json, manifest_digest

class SkillRegistry:
    """Records exact versions. Never imports or executes the described skill."""
    def __init__(self) -> None:
        self._entries: dict[tuple[str, str, str], dict] = {}

    def register(self, descriptor: dict) -> str:
        item = validate_manifest(descriptor)
        key = (item["tenant_id"], item["skill_id"], item["version"])
        if key in self._entries:
            raise SkillValidationError("VERSION_REPLACEMENT_DENIED")
        self._entries[key] = item
        return manifest_digest(item)

    def resolve(self, *, tenant_id: str, orchestrator_id: str, skill_id: str,
                version: str, runtime_domain: str) -> dict:
        visited: set[tuple[str, str, str]] = set()
        visiting: set[tuple[str, str, str]] = set()
        order: list[dict] = []

        def visit(sid: str, ver: str) -> None:
            key = (tenant_id, sid, ver)
            if key in visiting:
                raise SkillValidationError("CYCLIC_SKILL_DEPENDENCY")
            if key in visited:
                return
            item = self._entries.get(key)
            if item is None:
                raise SkillValidationError("MISSING_PINNED_DEPENDENCY")
            if item["orchestrator_id"] != orchestrator_id:
                raise SkillValidationError("CROSS_ORCHESTRATOR_SKILL_DENIED")
            if item["runtime_domain"] != runtime_domain:
                raise SkillValidationError("CROSS_RUNTIME_DOMAIN_SKILL_DENIED")
            if len(visited) + len(visiting) >= 256:
                raise SkillValidationError("SKILL_GRAPH_TOO_LARGE")
            visiting.add(key)
            for d in item["dependencies"]:
                visit(d["skill_id"], d["version"])
            visiting.remove(key)
            visited.add(key)
            order.append({"skill_id": sid, "version": ver,
                          "manifest_sha256": manifest_digest(item)})
        visit(skill_id, version)
        policy = {"schema": "imperial.skill.plan.v1", "tenant_id": tenant_id,
                  "orchestrator_id": orchestrator_id,
                  "runtime_domain": runtime_domain, "steps": order,
                  "stage": "PLAN_ONLY", "owner_approval_verified": False,
                  "ai_passport_verified": False, "independent_qa_verified": False,
                  "execution_authorized": False,
                  "production_authorized": False, "external_effects": False,
                  "spending_usd": 0}
        fingerprint = hashlib.sha256(canonical_json(policy)).hexdigest()
        return {**copy.deepcopy(policy), "plan_sha256": fingerprint}

    def snapshot(self) -> list[dict]:
        return [copy.deepcopy(self._entries[k]) for k in sorted(self._entries)]

    def integrity_digest(self) -> str:
        return hashlib.sha256(canonical_json(self.snapshot())).hexdigest()
