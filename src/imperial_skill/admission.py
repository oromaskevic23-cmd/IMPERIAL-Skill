"""Owner + issuer Ed25519 verification for limited skill PLAN admission.

This is an offline verifier, not the REAL Owner Approval Gateway.
Never treats valid signatures as authority to start a worker or perform external effects.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from .manifest import SkillValidationError, canonical_json

SHA = re.compile(r"^[a-f0-9]{64}$")
IDENT = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.:-]{2,99}$")
TOKEN = re.compile(r"^[A-Za-z0-9_-]{84,88}$")
CLAIM_FIELDS = frozenset({
    "schema", "purpose", "issuer", "key_id", "jti", "nonce_hex",
    "tenant_id", "orchestrator_id", "agent_id", "task_id",
    "plan_sha256", "owner_grant_id", "scope",
    "issued_at", "not_before", "expires_at",
    "production_authorized", "external_effects", "spending_usd",
})
ENVELOPE_FIELDS = frozenset({"claims", "signature"})
DOMAIN = b"IMPERIAL_SKILL_SIGNED_PLAN_V1\n"

@dataclass(frozen=True)
class PinnedAuthorities:
    """Key bytes MUST be configured out of band by a trusted runtime operator."""
    owner_public_key: bytes
    passport_issuer_public_key: bytes
    owner_key_id: str
    passport_key_id: str

    def __post_init__(self) -> None:
        if (type(self.owner_public_key) is not bytes
            or type(self.passport_issuer_public_key) is not bytes
            or len(self.owner_public_key) != 32
            or len(self.passport_issuer_public_key) != 32
            or self.owner_public_key == self.passport_issuer_public_key):
            raise SkillValidationError("TRUST_ROOTS_MISSING_OR_NOT_SEPARATED")
        if (not isinstance(self.owner_key_id, str)
            or not isinstance(self.passport_key_id, str)
            or not IDENT.fullmatch(self.owner_key_id)
            or not IDENT.fullmatch(self.passport_key_id)
            or self.owner_key_id == self.passport_key_id):
            raise SkillValidationError("TRUST_KEY_IDS_NOT_SEPARATED")

def _verify(envelope: object, public: bytes, purpose: str,
            issuer: str, key_id: str, *, now: int) -> dict:
    if type(envelope) is not dict or set(envelope) != ENVELOPE_FIELDS:
        raise SkillValidationError("SIGNED_ENVELOPE_SCHEMA_DENIED")
    claims, sig = envelope["claims"], envelope["signature"]
    if type(claims) is not dict or set(claims) != CLAIM_FIELDS:
        raise SkillValidationError("SIGNED_CLAIM_SCHEMA_DENIED")
    canonical = canonical_json(claims)
    if (claims["schema"] != "imperial.skill.approval.v1"
        or claims["purpose"] != purpose
        or claims["issuer"] != issuer or claims["key_id"] != key_id
        or not isinstance(claims["jti"], str) or not SHA.fullmatch(claims["jti"])
        or not isinstance(claims["nonce_hex"], str) or not SHA.fullmatch(claims["nonce_hex"])
        or not isinstance(claims["plan_sha256"], str) or not SHA.fullmatch(claims["plan_sha256"])
        or not isinstance(claims["owner_grant_id"], str)
        or (purpose == "OWNER_APPROVAL" and claims["owner_grant_id"] != "")
        or (purpose == "AI_PASSPORT" and not SHA.fullmatch(claims["owner_grant_id"]))
        or claims["scope"] != "LAB_PLAN_ONLY"
        or claims["production_authorized"] is not False
        or claims["external_effects"] is not False
        or type(claims["spending_usd"]) is not int or claims["spending_usd"] != 0):
        raise SkillValidationError("SIGNED_CLAIM_SCOPE_DENIED")
    for label in ("tenant_id", "orchestrator_id", "agent_id", "task_id"):
        if type(claims[label]) is not str or not IDENT.fullmatch(claims[label]):
            raise SkillValidationError("SIGNED_IDENTITY_INVALID")
    iat, nbf, exp = (claims[k] for k in ("issued_at", "not_before", "expires_at"))
    if (any(type(x) is not int for x in (iat, nbf, exp))
        or iat > now + 30 or iat < now - 300
        or nbf < iat or nbf > now or exp <= now
        or exp > iat + 300):
        raise SkillValidationError("SIGNED_CLAIM_EXPIRED")
    if type(sig) is not str or not TOKEN.fullmatch(sig):
        raise SkillValidationError("SIGNATURE_ENCODING_DENIED")
    try:
        raw = base64.urlsafe_b64decode(sig + "=" * (-len(sig) % 4))
        if len(raw) != 64:
            raise SkillValidationError("SIGNATURE_LENGTH_DENIED")
        Ed25519PublicKey.from_public_bytes(public).verify(raw, DOMAIN + canonical)
    except (ValueError, InvalidSignature, TypeError) as exc:
        raise SkillValidationError("SIGNATURE_INVALID") from exc
    return claims

class AtomicReplayLedger:
    """SQLite demo replay protection; production requires shared durable DB RPC."""
    def __init__(self, path: str | Path):
        self.path = str(path)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS consumed (
                jti TEXT PRIMARY KEY, nonce_hex TEXT UNIQUE NOT NULL,
                tenant_id TEXT NOT NULL, consumed_at INTEGER NOT NULL
            )""")

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=15)
        db.execute("PRAGMA busy_timeout=15000")
        return db

    def consume_pair(self, owner: dict, passport: dict, now: int) -> None:
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            for claims in (owner, passport):
                try:
                    db.execute("INSERT INTO consumed(jti,nonce_hex,tenant_id,consumed_at)"
                               " VALUES(?,?,?,?)", (claims["jti"], claims["nonce_hex"],
                               claims["tenant_id"], now))
                except sqlite3.IntegrityError as exc:
                    raise SkillValidationError("SIGNED_REPLAY_DENIED") from exc

class SkillAdmission:
    """Admit offline LAB PLAN only, never production or actual agent execution."""
    def __init__(self, authorities: PinnedAuthorities, replay: AtomicReplayLedger,
                 revocation_check: Callable[[str, str], bool]):
        if not isinstance(authorities, PinnedAuthorities) or not isinstance(replay, AtomicReplayLedger):
            raise SkillValidationError("ADMISSION_TRUST_NOT_CONFIGURED")
        if not callable(revocation_check):
            raise SkillValidationError("REVOCATION_CHECK_REQUIRED")
        self.authorities, self.replay, self.revocation_check = authorities, replay, revocation_check

    def admit(self, *, owner_envelope: dict, passport_envelope: dict,
              plan: dict, task_id: str, agent_id: str,
              now: int | None = None, owner_kill_switch: bool = True,
              guardian_approved: bool = False, competency_verified: bool = False) -> dict:
        if (owner_kill_switch is not False or guardian_approved is not True
            or competency_verified is not True):
            raise SkillValidationError("GUARDIAN_OR_OWNER_STOP")
        if type(now) is not int and now is not None:
            raise SkillValidationError("CLOCK_INVALID")
        stamp = int(time.time()) if now is None else now
        if type(plan) is not dict or plan.get("stage") != "PLAN_ONLY":
            raise SkillValidationError("SKILL_PLAN_REQUIRED")
        preimage = {k: v for k, v in plan.items() if k != "plan_sha256"}
        expected_plan = hashlib.sha256(canonical_json(preimage)).hexdigest()
        if (not isinstance(plan.get("plan_sha256"), str)
            or plan["plan_sha256"] != expected_plan
            or plan.get("execution_authorized") is not False
            or plan.get("production_authorized") is not False
            or plan.get("owner_approval_verified") is not False
            or plan.get("ai_passport_verified") is not False
            or plan.get("external_effects") is not False
            or plan.get("spending_usd") != 0):
            raise SkillValidationError("UNTRUSTED_PLAN")
        owner = _verify(owner_envelope, self.authorities.owner_public_key,
                        "OWNER_APPROVAL", "OWNER", self.authorities.owner_key_id, now=stamp)
        passport = _verify(passport_envelope, self.authorities.passport_issuer_public_key,
                           "AI_PASSPORT", "HANTER_DELEGATED_ISSUER",
                           self.authorities.passport_key_id, now=stamp)
        for claim in (owner, passport):
            if (claim["tenant_id"] != plan["tenant_id"]
                or claim["orchestrator_id"] != plan["orchestrator_id"]
                or claim["plan_sha256"] != plan["plan_sha256"]
                or claim["agent_id"] != agent_id or claim["task_id"] != task_id):
                raise SkillValidationError("SIGNED_ROUTE_OR_TASK_DENIED")
        if (passport["owner_grant_id"] != owner["jti"]
            or passport["jti"] == owner["jti"]
            or passport["nonce_hex"] == owner["nonce_hex"]):
            raise SkillValidationError("PASSPORT_OWNER_BINDING_DENIED")
        try:
            if (self.revocation_check("OWNER_APPROVAL", owner["jti"])
                or self.revocation_check("AI_PASSPORT", passport["jti"])):
                raise SkillValidationError("SIGNATURE_REVOKED")
        except SkillValidationError:
            raise
        except Exception as exc:
            raise SkillValidationError("REVOCATION_CHECK_UNAVAILABLE") from exc
        # Atomic pair write; no successfully consumed token may be used again.
        self.replay.consume_pair(owner, passport, stamp)
        return {"state": "LAB_PLAN_ADMITTED_NOT_EXECUTED",
                "skill_plan_sha256": expected_plan,
                "task_id": task_id, "agent_id": agent_id,
                "owner_signature_valid": True, "issuer_signature_valid": True,
                "external_effects": False, "production_authorized": False,
                "execution_authorized": False, "spending_usd": 0}
