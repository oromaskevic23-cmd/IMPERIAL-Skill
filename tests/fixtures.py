"""Synthetic input and ephemeral TEST keys only. No actual Owner identity is issued."""
import base64
import secrets
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from imperial_skill.admission import DOMAIN, PinnedAuthorities
from imperial_skill.manifest import canonical_json
from imperial_skill.registry import SkillRegistry

NOW = 1800000000

def manifest(**changes):
    result = {
        "schema": "imperial.skill.manifest.v1",
        "skill_id": "imperial.skill.code-review",
        "version": "0.1.0",
        "tenant_id": "imperial-internal",
        "orchestrator_id": "engineering-orch",
        "runtime_domain": "CODE_ENGINEERING",
        "description": "Offline source-code review proposal with no execution privileges",
        "capabilities": ["read:public", "simulate:task"],
        "dependencies": [],
        "input_fields": ["task_id", "source_sha256"],
        "output_fields": ["review_json"],
        "exam_sha256": "a"*64,
        "max_input_bytes": 8192,
        "max_output_bytes": 16384,
        "risk_tier": "GUARDED",
        "data_only": True,
        "independent_qa_required": True,
        "owner_approval_required": True,
        "external_effects": False,
        "production_authorized": False,
        "spending_usd": 0,
    }
    result.update(changes)
    return result

def plan(**changes):
    r = SkillRegistry()
    r.register(manifest())
    return r.resolve(tenant_id="imperial-internal",
                     orchestrator_id="engineering-orch",
                     skill_id="imperial.skill.code-review", version="0.1.0",
                     runtime_domain="CODE_ENGINEERING") | changes

def keys():
    owner = Ed25519PrivateKey.generate()
    passport = Ed25519PrivateKey.generate()
    public = lambda k: k.public_key().public_bytes(
        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
    authorities = PinnedAuthorities(
        owner_public_key=public(owner), passport_issuer_public_key=public(passport),
        owner_key_id="owner-test-key-01", passport_key_id="issuer-test-key-01")
    return owner, passport, authorities

def payload(purpose, *, plan_sha256, agent_id="NCA-424",
            task_id="TASK-001", jti=None, nonce=None, owner_grant_id="",
            **changes):
    result = {
        "schema":"imperial.skill.approval.v1",
        "purpose":purpose,
        "issuer":"OWNER" if purpose=="OWNER_APPROVAL" else "HANTER_DELEGATED_ISSUER",
        "key_id":"owner-test-key-01" if purpose=="OWNER_APPROVAL" else "issuer-test-key-01",
        "jti":jti or secrets.token_hex(32),
        "nonce_hex":nonce or secrets.token_hex(32),
        "tenant_id":"imperial-internal","orchestrator_id":"engineering-orch",
        "agent_id":agent_id,"task_id":task_id,"plan_sha256":plan_sha256,
        "owner_grant_id":owner_grant_id,"scope":"LAB_PLAN_ONLY",
        "issued_at":NOW-10,"not_before":NOW-10,"expires_at":NOW+100,
        "production_authorized":False,"external_effects":False,"spending_usd":0}
    result.update(changes)
    return result

def sign(claims, key):
    sig = key.sign(DOMAIN + canonical_json(claims))
    return {"claims":claims,
            "signature":base64.urlsafe_b64encode(sig).rstrip(b"=").decode("ascii")}

def envelopes(p, owner_key, issuer_key, **changes):
    own = payload("OWNER_APPROVAL", plan_sha256=p["plan_sha256"])
    own.update(changes.get("owner_changes",{}))
    passp = payload("AI_PASSPORT", plan_sha256=p["plan_sha256"],
                    owner_grant_id=own["jti"])
    passp.update(changes.get("passport_changes",{}))
    return sign(own, owner_key), sign(passp, issuer_key)
