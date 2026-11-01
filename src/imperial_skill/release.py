"""Cryptographically reviewed Enterprise Skill source; never production authority."""
from __future__ import annotations
import base64
import hashlib
import re
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from .manifest import SkillValidationError, canonical_json, manifest_digest, validate_manifest, SHA256, IDENT
from .exams import validate_exam
from .registry import SkillRegistry

DOMAIN = b"IMPERIAL_SKILL_SOURCE_REVIEW_V1\n"
REVIEW_FIELDS = frozenset({"schema", "candidate_sha256", "reviewer_id", "key_id",
                           "review_id", "nonce_hex", "decision", "issued_at",
                           "expires_at", "production_authorized", "external_effects", "spending_usd"})
NO_EFFECT = {"production_authorized": False, "external_effects": False, "spending_usd": 0}
TOKEN = re.compile(r"^[a-f0-9]{64}$")
CANDIDATE_FIELDS = frozenset({
    "schema", "skill_id", "version", "tenant_id", "orchestrator_id",
    "runtime_domain", "manifest_sha256", "exam_sha256", "plan_sha256",
    "registry_sha256", "stage", "independent_qa_verified",
    "execution_authorized", "production_authorized", "external_effects",
    "spending_usd", "candidate_sha256",
})

def prepare_candidate(registry: SkillRegistry, descriptor: dict, exam: dict) -> dict:
    """Bind registered manifest, exam definition and exact federated plan."""
    if not isinstance(registry, SkillRegistry):
        raise SkillValidationError("PINNED_SKILL_REGISTRY_REQUIRED")
    item = validate_manifest(descriptor)
    exam_meta = validate_exam(exam)
    if (exam_meta["exam_sha256"] != item["exam_sha256"]
        or exam["skill_id"] != item["skill_id"] or exam["version"] != item["version"]):
        raise SkillValidationError("SKILL_EXAM_MISMATCH")
    plan = registry.resolve(tenant_id=item["tenant_id"],
                            orchestrator_id=item["orchestrator_id"],
                            runtime_domain=item["runtime_domain"],
                            skill_id=item["skill_id"], version=item["version"])
    if plan["steps"][-1]["manifest_sha256"] != manifest_digest(item):
        raise SkillValidationError("UNREGISTERED_SKILL_MUTATION")
    payload = {"schema": "imperial.skill.source-candidate.v1",
               "skill_id": item["skill_id"], "version": item["version"],
               "tenant_id": item["tenant_id"],
               "orchestrator_id": item["orchestrator_id"],
               "runtime_domain": item["runtime_domain"],
               "manifest_sha256": manifest_digest(item),
               "exam_sha256": item["exam_sha256"],
               "plan_sha256": plan["plan_sha256"],
               "registry_sha256": registry.integrity_digest(),
               "stage": "SOURCE_REVIEW_REQUIRED",
               "independent_qa_verified": False, "execution_authorized": False,
               **NO_EFFECT}
    return {**payload, "candidate_sha256": hashlib.sha256(canonical_json(payload)).hexdigest()}

@dataclass(frozen=True)
class PinnedSourceReviewer:
    public_key: bytes
    reviewer_id: str
    key_id: str

    def __post_init__(self):
        if type(self.public_key) is not bytes or len(self.public_key) != 32:
            raise SkillValidationError("REVIEWER_KEY_NOT_PINNED")
        for value in (self.reviewer_id, self.key_id):
            if type(value) is not str or not IDENT.fullmatch(value):
                raise SkillValidationError("REVIEWER_ID_NOT_PINNED")

class ReviewNonceLedger:
    """Local atomic replay gate. A shared authoritative server is a separate requirement."""
    def __init__(self, path: str | Path):
        self.path = str(path)
        with self._db() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS reviews(
                review_id TEXT PRIMARY KEY, nonce_hex TEXT NOT NULL UNIQUE,
                candidate_sha256 TEXT NOT NULL, seen_at INTEGER NOT NULL)""")

    def _db(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.execute("PRAGMA busy_timeout=10000")
        return db

    def consume(self, claims: dict, at: int) -> None:
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                db.execute("INSERT INTO reviews VALUES (?,?,?,?)",
                           (claims["review_id"], claims["nonce_hex"],
                            claims["candidate_sha256"], at))
            except sqlite3.IntegrityError as exc:
                raise SkillValidationError("REVIEW_REPLAY_DENIED") from exc

def verify_source_review(*, candidate: dict, receipt: dict,
                         reviewer: PinnedSourceReviewer,
                         replay: ReviewNonceLedger, revoked: Callable[[str, str], bool],
                         now: int | None = None) -> dict:
    """A valid signature means reviewed SOURCE only; no NCA certification or release."""
    if not isinstance(reviewer, PinnedSourceReviewer) or not isinstance(replay, ReviewNonceLedger):
        raise SkillValidationError("PINNED_REVIEW_TRUST_REQUIRED")
    if not callable(revoked):
        raise SkillValidationError("REVIEW_REVOCATION_REQUIRED")
    if type(candidate) is not dict or set(candidate) != CANDIDATE_FIELDS:
        raise SkillValidationError("CANDIDATE_SCHEMA_DENIED")
    body = {k: v for k, v in candidate.items() if k != "candidate_sha256"}
    for field in ("manifest_sha256", "exam_sha256", "plan_sha256", "registry_sha256"):
        if type(body[field]) is not str or not SHA256.fullmatch(body[field]):
            raise SkillValidationError("CANDIDATE_HASH_SCHEMA_DENIED")
    for field in ("tenant_id", "orchestrator_id"):
        if type(body[field]) is not str or not IDENT.fullmatch(body[field]):
            raise SkillValidationError("CANDIDATE_BOUNDARY_DENIED")
    if any(type(body[k]) is not str for k in
           ("skill_id", "version", "runtime_domain")):
        raise SkillValidationError("CANDIDATE_IDENTITY_DENIED")
    if (body.get("schema") != "imperial.skill.source-candidate.v1"
        or body.get("stage") != "SOURCE_REVIEW_REQUIRED"
        or body.get("independent_qa_verified") is not False
        or body.get("execution_authorized") is not False
        or any(body.get(k) != v or type(body.get(k)) is not type(v)
               for k, v in NO_EFFECT.items())
        or type(candidate["candidate_sha256"]) is not str
        or not SHA256.fullmatch(candidate["candidate_sha256"])
        or hashlib.sha256(canonical_json(body)).hexdigest() != candidate["candidate_sha256"]):
        raise SkillValidationError("CANDIDATE_TAMPERED_OR_OVERPRIVILEGED")
    if type(receipt) is not dict or set(receipt) != {"claims", "signature"}:
        raise SkillValidationError("REVIEW_ENVELOPE_DENIED")
    claim = receipt["claims"]
    if type(claim) is not dict or set(claim) != REVIEW_FIELDS:
        raise SkillValidationError("REVIEW_CLAIM_SCHEMA_DENIED")
    if (claim["schema"] != "imperial.skill.source-review.v1"
        or claim["candidate_sha256"] != candidate["candidate_sha256"]
        or claim["reviewer_id"] != reviewer.reviewer_id
        or claim["key_id"] != reviewer.key_id
        or claim["decision"] != "SOURCE_CODE_REVIEWED"
        or any(claim[k] != v or type(claim[k]) is not type(v)
               for k, v in NO_EFFECT.items())
        or any(type(claim[k]) is not str or not TOKEN.fullmatch(claim[k])
               for k in ("review_id", "nonce_hex"))):
        raise SkillValidationError("REVIEW_SCOPE_DENIED")
    stamp = int(time.time()) if now is None else now
    issued, expiry = claim["issued_at"], claim["expires_at"]
    if (type(stamp) is not int or type(issued) is not int or type(expiry) is not int
        or issued < stamp-120 or issued > stamp+30
        or expiry <= stamp or expiry > issued+300):
        raise SkillValidationError("REVIEW_EXPIRED")
    signature = receipt["signature"]
    if type(signature) is not str or not re.fullmatch(r"[A-Za-z0-9_-]{85,88}", signature):
        raise SkillValidationError("REVIEW_SIGNATURE_ENCODING_DENIED")
    try:
        raw = base64.urlsafe_b64decode(signature + "=" * (-len(signature) % 4))
        if len(raw) != 64:
            raise ValueError("invalid length")
        Ed25519PublicKey.from_public_bytes(reviewer.public_key).verify(
            raw, DOMAIN + canonical_json(claim))
    except (ValueError, TypeError, InvalidSignature) as exc:
        raise SkillValidationError("REVIEW_SIGNATURE_DENIED") from exc
    try:
        state = revoked(claim["key_id"], claim["review_id"])
        if type(state) is not bool or state:
            raise SkillValidationError("REVIEW_REVOKED_OR_INDETERMINATE")
    except SkillValidationError:
        raise
    except Exception as exc:
        raise SkillValidationError("REVIEW_REVOCATION_UNAVAILABLE") from exc
    replay.consume(claim, stamp)
    return {"stage": "REVIEWED_SOURCE_ONLY", "signature_verified": True,
            "candidate_sha256": candidate["candidate_sha256"],
            "independent_qa_verified": False, "professional_certified": False,
            "owner_approval_verified": False, "ai_passport_verified": False,
            "execution_authorized": False, **NO_EFFECT, "externally_attested": False}
