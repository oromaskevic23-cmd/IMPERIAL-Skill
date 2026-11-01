import base64
import hashlib
import unittest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from imperial_skill.proofgraph import (make_local_proof,verify_local_proof,
                                        verify_independent_qa_receipt,PROOF_DOMAIN)
from imperial_skill.manifest import canonical_json,SkillValidationError

ARTIFACT=b"export function clamp(v,l,h){return Math.min(h,Math.max(l,v));}"
GRADE={"reference_match_pass":True,"independent_qa_verified":False}
def proof():
    return make_local_proof(plan_sha256="a"*64,artifact=ARTIFACT,
                 exam_sha256="b"*64,grade_report=GRADE)
class ProofGraphTests(unittest.TestCase):
    def test_local_proof_hash_integrity_not_claiming_independence(self):
        p=proof();r=verify_local_proof(p,ARTIFACT,GRADE,previous_sha256="0"*64)
        self.assertTrue(r["integrity_verified"])
        self.assertFalse(r["independent_qa_verified"])
        self.assertFalse(r["production_authorized"])
    def test_artifact_and_grading_data_bound(self):
        p=proof()
        self.assertFalse(verify_local_proof(p,ARTIFACT+b"x",GRADE,previous_sha256="0"*64)["integrity_verified"])
        self.assertFalse(verify_local_proof(p,ARTIFACT,GRADE|{"reference_match_pass":False},previous_sha256="0"*64)["integrity_verified"])
    def test_chain_mismatch_denied(self):
        p=proof()
        self.assertFalse(verify_local_proof(p,ARTIFACT,GRADE,previous_sha256="f"*64)["integrity_verified"])
    def test_metadata_tampering_denied(self):
        p=proof()
        for changes in ({"qa_claim":"CERTIFIED"},{"production_authorized":True},
                        {"external_effects":True},{"spending_usd":100},
                        {"qa_issuer_id":"pretend-qa"}):
            with self.subTest(changes=changes):
                self.assertFalse(verify_local_proof(p|changes,ARTIFACT,GRADE,previous_sha256="0"*64)["integrity_verified"])
    def test_unknown_fields_denied(self):
        self.assertFalse(verify_local_proof(proof()|{"admin":"yes"},ARTIFACT,GRADE,previous_sha256="0"*64)["integrity_verified"])
    def test_oversize_artifact_denied(self):
        with self.assertRaises(SkillValidationError):
            make_local_proof(plan_sha256="a"*64,exam_sha256="b"*64,
                             artifact=b"x"*8388609,grade_report=GRADE)
    def test_pinned_qa_signer_receipt(self):
        key=Ed25519PrivateKey.generate()
        pub=key.public_key().public_bytes(encoding=serialization.Encoding.Raw,
                                           format=serialization.PublicFormat.Raw)
        digest=proof()["proof_sha256"]
        receipt={"schema":"imperial.skill.external-qa-receipt.v1",
                 "proof_sha256":digest,"examiner_id":"independent-qa-01",
                 "decision":"PASS","production_authorized":False,
                 "external_effects":False,"spending_usd":0}
        sig=base64.urlsafe_b64encode(key.sign(PROOF_DOMAIN+canonical_json(receipt))).decode().rstrip("=")
        result=verify_independent_qa_receipt(proof_sha256=digest,qa_receipt=receipt,
                         signature=sig,trusted_qa_spki=pub,trusted_qa_id="independent-qa-01")
        self.assertTrue(result["independent_qa_receipt_signed"])
        self.assertFalse(result["production_authorized"])
        self.assertFalse(verify_independent_qa_receipt(proof_sha256=digest,qa_receipt=receipt|{"decision":"FAIL"},
          signature=sig,trusted_qa_spki=pub,trusted_qa_id="independent-qa-01")["signature_valid"])
        self.assertFalse(verify_independent_qa_receipt(proof_sha256=digest,qa_receipt=receipt,
          signature=sig,trusted_qa_spki=Ed25519PrivateKey.generate().public_key().public_bytes(
                  encoding=serialization.Encoding.Raw,format=serialization.PublicFormat.Raw),
          trusted_qa_id="independent-qa-01")["signature_valid"])
    def test_qa_claim_not_owner_or_production_grant(self):
        receipt={"schema":"imperial.skill.external-qa-receipt.v1",
                 "proof_sha256":proof()["proof_sha256"],"examiner_id":"independent-qa-01",
                 "decision":"PASS","production_authorized":True,
                 "external_effects":False,"spending_usd":0}
        self.assertFalse(verify_independent_qa_receipt(proof_sha256=receipt["proof_sha256"],
          qa_receipt=receipt,signature="invalid",trusted_qa_spki=b"x"*32,
          trusted_qa_id="independent-qa-01")["signature_valid"])
