import base64
import hashlib
import secrets
import tempfile
import unittest
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from fixtures import manifest
from imperial_skill.exams import validate_exam
from imperial_skill.manifest import SkillValidationError,canonical_json
from imperial_skill.registry import SkillRegistry
from imperial_skill.release import (DOMAIN,PinnedSourceReviewer,ReviewNonceLedger,
                                    prepare_candidate,verify_source_review)

def exam():
    return {"schema":"imperial.skill.offline-exam.v1",
            "skill_id":"imperial.skill.code-review","version":"0.1.0",
            "cases":[{"case_id":"block_unsafe",
                      "expected_sha256":hashlib.sha256(b"DENIED").hexdigest(),
                      "critical":True}],
            "minimum_percent":100,"independent_qa_required":True}

class SignedReleaseTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.exam=exam()
        self.desc=manifest(exam_sha256=validate_exam(self.exam)["exam_sha256"])
        self.reg=SkillRegistry()
        self.reg.register(self.desc)
        self.candidate=prepare_candidate(self.reg,self.desc,self.exam)
        self.signer=Ed25519PrivateKey.generate()
        raw=self.signer.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,format=serialization.PublicFormat.Raw)
        self.reviewer=PinnedSourceReviewer(raw,"reviewer-test-01","key-test-01")
        self.replay=ReviewNonceLedger(Path(t.name)/"reviews.db")
        self.now=1800000000

    def receipt(self,changes=None,signer=None):
        claims={"schema":"imperial.skill.source-review.v1",
                "candidate_sha256":self.candidate["candidate_sha256"],
                "reviewer_id":"reviewer-test-01","key_id":"key-test-01",
                "review_id":secrets.token_hex(32),"nonce_hex":secrets.token_hex(32),
                "decision":"SOURCE_CODE_REVIEWED","issued_at":self.now-5,
                "expires_at":self.now+100,"production_authorized":False,
                "external_effects":False,"spending_usd":0}
        claims.update(changes or {})
        signature=(signer or self.signer).sign(DOMAIN+canonical_json(claims))
        return {"claims":claims,
                "signature":base64.urlsafe_b64encode(signature).decode().rstrip("=")}

    def review(self,receipt=None,**overrides):
        args={"candidate":self.candidate,"receipt":receipt or self.receipt(),
              "reviewer":self.reviewer,"replay":self.replay,
              "revoked":lambda key,review:False,"now":self.now}
        args.update(overrides)
        return verify_source_review(**args)

    def test_registered_manifest_and_exam_bound(self):
        self.assertEqual(self.candidate["exam_sha256"],validate_exam(self.exam)["exam_sha256"])
        self.assertFalse(self.candidate["production_authorized"])

    def test_replaced_exam_denied(self):
        bad=exam();bad["cases"][0]["expected_sha256"]="a"*64
        with self.assertRaisesRegex(SkillValidationError,"EXAM_MISMATCH"):
            prepare_candidate(self.reg,self.desc,bad)

    def test_unregistered_descriptor_mutation_denied(self):
        changed=dict(self.desc,description="Changed code without registration")
        with self.assertRaisesRegex(SkillValidationError,"UNREGISTERED"):
            prepare_candidate(self.reg,changed,self.exam)

    def test_foreign_tenant_denied(self):
        for change in ({"tenant_id":"other-tenant"},{"orchestrator_id":"security-orch"},
                       {"runtime_domain":"DATA_ANALYSIS"}):
            with self.subTest(change=change),self.assertRaises(SkillValidationError):
                prepare_candidate(self.reg,dict(self.desc,**change),self.exam)

    def test_source_signature_does_not_certify_agent(self):
        r=self.review()
        self.assertTrue(r["signature_verified"])
        for flag in ("independent_qa_verified","professional_certified",
                     "owner_approval_verified","ai_passport_verified",
                     "execution_authorized","production_authorized","externally_attested"):
            self.assertFalse(r[flag])

    def test_exact_replay_denied(self):
        receipt=self.receipt()
        self.review(receipt)
        with self.assertRaisesRegex(SkillValidationError,"REPLAY"):
            self.review(receipt)

    def test_replay_persists_on_ledger_reopen(self):
        receipt=self.receipt()
        self.review(receipt)
        new_ledger=ReviewNonceLedger(self.replay.path)
        with self.assertRaisesRegex(SkillValidationError,"REPLAY"):
            self.review(receipt,replay=new_ledger)

    def test_forged_signer_denied(self):
        fake=Ed25519PrivateKey.generate()
        with self.assertRaisesRegex(SkillValidationError,"SIGNATURE_DENIED"):
            self.review(self.receipt(signer=fake))

    def test_overprivileged_review_denied(self):
        for patch in ({"production_authorized":True},{"external_effects":True},
                      {"spending_usd":1},{"spending_usd":False},
                      {"decision":"DEPLOY_AND_SPEND"}):
            with self.subTest(patch=patch),self.assertRaisesRegex(SkillValidationError,"REVIEW_SCOPE"):
                self.review(self.receipt(patch))

    def test_expired_and_long_ttl_denied(self):
        for patch in ({"expires_at":self.now-1},{"expires_at":self.now+500},
                      {"issued_at":self.now-300},{"issued_at":self.now+60}):
            with self.subTest(patch=patch),self.assertRaisesRegex(SkillValidationError,"REVIEW_EXPIRED"):
                self.review(self.receipt(patch))

    def test_revoked_reviewer_denied(self):
        with self.assertRaisesRegex(SkillValidationError,"REVIEW_REVOKED"):
            self.review(revoked=lambda k,j:True)

    def test_unavailable_revocation_is_deny(self):
        with self.assertRaisesRegex(SkillValidationError,"REVOCATION_UNAVAILABLE"):
            self.review(revoked=lambda k,j:(_ for _ in ()).throw(ConnectionError()))

    def test_indeterminate_revocation_is_deny(self):
        with self.assertRaisesRegex(SkillValidationError,"REVIEW_REVOKED"):
            self.review(revoked=lambda k,j:None)

    def test_candidate_tampering_rejected(self):
        for patch in ({"candidate_sha256":"0"*64},{"production_authorized":True},
                      {"independent_qa_verified":True},{"spending_usd":False},
                      {"source":"untrusted"}):
            bad=dict(self.candidate,**patch)
            with self.subTest(patch=patch),self.assertRaises(SkillValidationError):
                self.review(candidate=bad)

    def test_missing_pinned_public_key_denied(self):
        with self.assertRaisesRegex(SkillValidationError,"REVIEWER_KEY"):
            PinnedSourceReviewer(b"bad","reviewer-test-01","key-test-01")

    def test_local_ledger_has_no_private_signer_material(self):
        self.review()
        with self.replay._db() as db:
            row=db.execute("select candidate_sha256 from reviews").fetchone()
        self.assertEqual(row[0],self.candidate["candidate_sha256"])

if __name__=="__main__":unittest.main()
