"""ProofGraph: hash-bound local result + externally pinned QA signer verification."""
from __future__ import annotations
import base64
import hashlib
import hmac
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from .manifest import canonical_json, SkillValidationError, SHA256

PROOF_DOMAIN = b"IMPERIAL_SKILL_PROOFGRAPH_QA_V1\n"
FIELDS = frozenset({"schema","plan_sha256","artifact_sha256","exam_sha256",
                    "result_sha256","previous_sha256","qa_claim","qa_issuer_id",
                    "production_authorized","external_effects","spending_usd"})

def make_local_proof(*, plan_sha256: str, artifact: bytes,
                     exam_sha256: str, grade_report: dict,
                     previous_sha256: str = "0" * 64) -> dict:
    for dig in (plan_sha256, exam_sha256, previous_sha256):
        if type(dig) is not str or not SHA256.fullmatch(dig):
            raise SkillValidationError("PROOF_INPUT_HASH_DENIED")
    if type(artifact) is not bytes or len(artifact) > 8_388_608:
        raise SkillValidationError("PROOF_ARTIFACT_SIZE_DENIED")
    if type(grade_report) is not dict:
        raise SkillValidationError("PROOF_GRADE_REQUIRED")
    raw = canonical_json(grade_report)
    proof = {"schema":"imperial.skill.proofgraph.local.v1",
             "plan_sha256":plan_sha256,
             "artifact_sha256":hashlib.sha256(artifact).hexdigest(),
             "exam_sha256":exam_sha256,
             "result_sha256":hashlib.sha256(raw).hexdigest(),
             "previous_sha256":previous_sha256,
             "qa_claim":"UNVERIFIED_LOCAL_REFERENCE",
             "qa_issuer_id":"",
             "production_authorized":False,"external_effects":False,"spending_usd":0}
    return {**proof,"proof_sha256":hashlib.sha256(canonical_json(proof)).hexdigest()}

def verify_local_proof(proof: dict, artifact: bytes, grade_report: dict,
                       *, previous_sha256: str) -> dict:
    result = {"integrity_verified":False,"independent_qa_verified":False,
              "production_authorized":False}
    if type(proof) is not dict or set(proof) != (FIELDS | {"proof_sha256"}):
        return result
    try:
        payload = {k: v for k,v in proof.items() if k!="proof_sha256"}
        if (payload["schema"]!="imperial.skill.proofgraph.local.v1"
            or payload["qa_claim"]!="UNVERIFIED_LOCAL_REFERENCE"
            or payload["qa_issuer_id"]!=""
            or payload["production_authorized"] is not False
            or payload["external_effects"] is not False
            or type(payload["spending_usd"]) is not int or payload["spending_usd"]!=0
            or previous_sha256!=payload["previous_sha256"]):
            return result
        for k in ("plan_sha256","artifact_sha256","exam_sha256","result_sha256",
                  "previous_sha256","proof_sha256"):
            if type(proof[k]) is not str or not SHA256.fullmatch(proof[k]):
                return result
        if (not hmac.compare_digest(hashlib.sha256(canonical_json(payload)).hexdigest(),
                                   proof["proof_sha256"])
            or not hmac.compare_digest(hashlib.sha256(artifact).hexdigest(),proof["artifact_sha256"])
            or not hmac.compare_digest(hashlib.sha256(canonical_json(grade_report)).hexdigest(),
                                      proof["result_sha256"])):
            return result
    except (ValueError,TypeError,KeyError,OverflowError):
        return result
    return {"integrity_verified":True,"independent_qa_verified":False,
            "production_authorized":False,"proof_sha256":proof["proof_sha256"]}

def verify_independent_qa_receipt(*, proof_sha256: str, qa_receipt: dict,
                                  signature: str, trusted_qa_spki: bytes,
                                  trusted_qa_id: str) -> dict:
    """Signature means pinned examiner signed the receipt, not external certification.

    Production authority always remains FALSE. Caller verifies independent trust custody.
    """
    deny = {"signature_valid":False,"independent_qa_receipt_signed":False,
            "production_authorized":False}
    fields = {"schema","proof_sha256","examiner_id","decision",
              "external_effects","production_authorized","spending_usd"}
    if (type(qa_receipt) is not dict or set(qa_receipt)!=fields
        or type(signature) is not str or not 85 <= len(signature) <= 88
        or any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for c in signature)
        or type(trusted_qa_spki) is not bytes
        or len(trusted_qa_spki)!=32 or type(trusted_qa_id) is not str):
        return deny
    if (qa_receipt["schema"]!="imperial.skill.external-qa-receipt.v1"
        or qa_receipt["examiner_id"]!=trusted_qa_id
        or qa_receipt["proof_sha256"]!=proof_sha256
        or type(proof_sha256) is not str or not SHA256.fullmatch(proof_sha256)
        or qa_receipt["decision"]!="PASS"
        or qa_receipt["production_authorized"] is not False
        or qa_receipt["external_effects"] is not False
        or type(qa_receipt["spending_usd"]) is not int
        or qa_receipt["spending_usd"]!=0):
        return deny
    try:
        raw=base64.urlsafe_b64decode(signature+"="*(-len(signature)%4))
        if len(raw)!=64:
            return deny
        Ed25519PublicKey.from_public_bytes(trusted_qa_spki).verify(
            raw,PROOF_DOMAIN+canonical_json(qa_receipt))
    except (ValueError,TypeError,InvalidSignature):
        return deny
    return {"signature_valid":True,"independent_qa_receipt_signed":True,
            "production_authorized":False,"proof_sha256":proof_sha256}
