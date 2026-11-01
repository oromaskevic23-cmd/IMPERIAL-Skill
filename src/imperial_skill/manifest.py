"""Deny-by-default Enterprise Skill manifest validation.

No dynamic code import, network access, shell execution or resource acquisition.
A valid descriptor does not constitute an AI Passport, Owner Approval, or QA PASS.
"""
from __future__ import annotations
import copy
import hashlib
import json
import re
from typing import Any

SCHEMA = "imperial.skill.manifest.v1"
CAPABILITIES = frozenset({"read:public", "simulate:task", "route:internal"})
DOMAINS = frozenset({"CODE_ENGINEERING", "SECURITY_DEFENSIVE", "AUTOMATION_LAB",
                     "DATA_ANALYSIS", "CREATIVE_STUDIO", "OPERATIONS_LAB"})
SKILL_ID = re.compile(r"^imperial\.skill\.[a-z][a-z0-9-]{2,63}$")
VERSION = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
IDENT = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.:-]{2,99}$")
FIELD = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
FIELDS = frozenset({
    "schema", "skill_id", "version", "tenant_id", "orchestrator_id",
    "runtime_domain", "description", "capabilities", "dependencies",
    "input_fields", "output_fields", "exam_sha256",
    "max_input_bytes", "max_output_bytes", "risk_tier", "data_only",
    "independent_qa_required", "owner_approval_required",
    "external_effects", "production_authorized", "spending_usd",
})
MAX_MANIFEST_BYTES = 64 * 1024

class SkillValidationError(ValueError):
    """Invalid, untrusted, or overprivileged Enterprise Skill descriptor."""

def canonical_json(value: Any) -> bytes:
    try:
        out = json.dumps(value, ensure_ascii=False, separators=(",", ":"),
                         sort_keys=True, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, OverflowError, RecursionError) as exc:
        raise SkillValidationError("NON_CANONICAL_JSON") from exc
    if len(out) > MAX_MANIFEST_BYTES:
        raise SkillValidationError("OVERSIZE_JSON")
    return out

def read_json_strict(data: bytes) -> dict:
    if not isinstance(data, bytes) or len(data) > MAX_MANIFEST_BYTES:
        raise SkillValidationError("MANIFEST_SIZE_DENIED")
    def reject_duplicates(pairs):
        out = {}
        for k, value in pairs:
            if k in out:
                raise SkillValidationError("DUPLICATE_JSON_KEY")
            out[k] = value
        return out
    def reject_constant(_: str) -> None:
        raise SkillValidationError("NON_FINITE_NUMBER")
    try:
        item = json.loads(data.decode("utf-8"), object_pairs_hook=reject_duplicates,
                          parse_constant=reject_constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise SkillValidationError("INVALID_MANIFEST_JSON") from exc
    if not isinstance(item, dict):
        raise SkillValidationError("MANIFEST_NOT_AN_OBJECT")
    return item

def _strmatch(v: Any, pattern: re.Pattern[str]) -> bool:
    return type(v) is str and pattern.fullmatch(v) is not None

def validate_manifest(value: object) -> dict:
    if not isinstance(value, dict) or set(value) != FIELDS:
        raise SkillValidationError("MANIFEST_SCHEMA_DENIED")
    canonical_json(value)
    if value["schema"] != SCHEMA or not _strmatch(value["skill_id"], SKILL_ID):
        raise SkillValidationError("SKILL_ID_OR_SCHEMA_DENIED")
    if not _strmatch(value["version"], VERSION):
        raise SkillValidationError("VERSION_DENIED")
    for k in ("tenant_id", "orchestrator_id"):
        if not _strmatch(value[k], IDENT):
            raise SkillValidationError("FEDERATION_BOUNDARY_DENIED")
    if type(value["runtime_domain"]) is not str or value["runtime_domain"] not in DOMAINS:
        raise SkillValidationError("RUNTIME_DOMAIN_DENIED")
    if type(value["description"]) is not str or not 20 <= len(value["description"]) <= 300:
        raise SkillValidationError("DESCRIPTION_DENIED")
    caps = value["capabilities"]
    if (type(caps) is not list or not caps or len(caps) > 3
        or any(type(x) is not str or x not in CAPABILITIES for x in caps)
        or len(set(caps)) != len(caps)):
        raise SkillValidationError("CAPABILITY_DENIED")
    deps = value["dependencies"]
    if type(deps) is not list or len(deps) > 16:
        raise SkillValidationError("DEPENDENCY_SCHEMA_DENIED")
    seen = set()
    for item in deps:
        if (type(item) is not dict or set(item) != {"skill_id", "version"}
            or not _strmatch(item["skill_id"], SKILL_ID)
            or not _strmatch(item["version"], VERSION)
            or item["skill_id"] == value["skill_id"]):
            raise SkillValidationError("DEPENDENCY_DENIED")
        dep_key = (item["skill_id"], item["version"])
        if dep_key in seen:
            raise SkillValidationError("DUPLICATE_DEPENDENCY")
        seen.add(dep_key)
    for key in ("input_fields", "output_fields"):
        fields = value[key]
        if (type(fields) is not list or not 1 <= len(fields) <= 32
            or any(not _strmatch(x, FIELD) for x in fields)
            or len(set(fields)) != len(fields)):
            raise SkillValidationError("IO_CONTRACT_DENIED")
    if not _strmatch(value["exam_sha256"], SHA256):
        raise SkillValidationError("EXAM_PROVENANCE_REQUIRED")
    for key in ("max_input_bytes", "max_output_bytes"):
        if type(value[key]) is not int or not 1 <= value[key] <= 1_048_576:
            raise SkillValidationError("RESOURCE_BOUND_DENIED")
    if type(value["risk_tier"]) is not str or value["risk_tier"] not in {"LOW", "GUARDED"}:
        raise SkillValidationError("RISK_TIER_DENIED")
    for required in ("data_only", "independent_qa_required", "owner_approval_required"):
        if value[required] is not True:
            raise SkillValidationError("SECURITY_GATE_REQUIRED")
    if (value["external_effects"] is not False or
        value["production_authorized"] is not False or
        type(value["spending_usd"]) is not int or value["spending_usd"] != 0):
        raise SkillValidationError("UNAUTHORIZED_EFFECT_DENIED")
    return copy.deepcopy(value)

def manifest_digest(value: object) -> str:
    return hashlib.sha256(canonical_json(validate_manifest(value))).hexdigest()
