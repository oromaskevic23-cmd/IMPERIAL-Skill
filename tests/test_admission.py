import tempfile
import unittest
from pathlib import Path
from fixtures import NOW,plan,keys,envelopes
from imperial_skill.admission import (PinnedAuthorities,AtomicReplayLedger,
                                      SkillAdmission,SkillValidationError)

class AdmissionTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.owner,self.issuer,self.authorities=keys()
        self.replay=AtomicReplayLedger(Path(tmp.name)/"replays.db")
        self.revoked=set()
        self.auth=SkillAdmission(self.authorities,self.replay,
           lambda kind,jti:(kind,jti) in self.revoked)
        self.plan=plan()
        self.owner_doc,self.passport_doc=envelopes(self.plan,self.owner,self.issuer)
    def admit(self,**changes):
        args={"owner_envelope":self.owner_doc,
              "passport_envelope":self.passport_doc,
              "plan":self.plan,"task_id":"TASK-001","agent_id":"NCA-424",
              "now":NOW,"owner_kill_switch":False,
              "guardian_approved":True,"competency_verified":True}
        args.update(changes)
        return self.auth.admit(**args)
    def denied(self,**changes):
        with self.assertRaises(SkillValidationError):self.admit(**changes)
    def test_separate_owner_and_issuer_verified_without_production(self):
        result=self.admit()
        self.assertTrue(result["owner_signature_valid"])
        self.assertTrue(result["issuer_signature_valid"])
        self.assertFalse(result["execution_authorized"])
        self.assertFalse(result["production_authorized"])
        self.assertEqual(result["spending_usd"],0)
    def test_repeated_owner_and_passport_pair_rejected(self):
        self.admit()
        with self.assertRaisesRegex(SkillValidationError,"REPLAY"):
            self.admit()
    def test_replay_preserved_across_process_or_registry_instance(self):
        self.admit()
        copy=SkillAdmission(self.authorities,
            AtomicReplayLedger(self.replay.path),lambda kind,jti:False)
        with self.assertRaisesRegex(SkillValidationError,"REPLAY"):
            copy.admit(owner_envelope=self.owner_doc,passport_envelope=self.passport_doc,
                       plan=self.plan,task_id="TASK-001",agent_id="NCA-424",now=NOW,
                       owner_kill_switch=False,guardian_approved=True,
                       competency_verified=True)
    def test_revoked_owner_denied(self):
        self.revoked.add(("OWNER_APPROVAL",self.owner_doc["claims"]["jti"]))
        self.denied()
    def test_revoked_passport_denied(self):
        self.revoked.add(("AI_PASSPORT",self.passport_doc["claims"]["jti"]))
        self.denied()
    def test_revocation_service_failure_denied(self):
        auth=SkillAdmission(self.authorities,self.replay,
                            lambda kind,jti:(_ for _ in ()).throw(ConnectionError()))
        with self.assertRaisesRegex(SkillValidationError,"REVOCATION_CHECK_UNAVAILABLE"):
            self.admit(**{"owner_envelope":self.owner_doc,
              "passport_envelope":self.passport_doc,"plan":self.plan,
              "task_id":"TASK-001","agent_id":"NCA-424",
              "now":NOW,"owner_kill_switch":False,
              "guardian_approved":True,"competency_verified":True,
              "guardian_approved":True}) if False else auth.admit(
                 owner_envelope=self.owner_doc,passport_envelope=self.passport_doc,
                 plan=self.plan,task_id="TASK-001",agent_id="NCA-424",
                 now=NOW,owner_kill_switch=False,guardian_approved=True,
                 competency_verified=True)
    def test_default_owner_kill_switch(self):
        self.denied(owner_kill_switch=True)
        self.denied(owner_kill_switch=False,guardian_approved=False)
        self.denied(owner_kill_switch=False,competency_verified=False)
    def test_forged_owner_signature_denied(self):
        changed=dict(self.owner_doc)
        changed["signature"]="A"*86
        self.denied(owner_envelope=changed)
    def test_forged_passport_signature_denied(self):
        changed=dict(self.passport_doc);changed["signature"]="A"*86
        self.denied(passport_envelope=changed)
    def test_changed_owner_scope_denied(self):
        claim=dict(self.owner_doc["claims"]);claim["scope"]="PRODUCTION"
        self.denied(owner_envelope={**self.owner_doc,"claims":claim})
    def test_cross_tenant_or_orchestrator_denied(self):
        self.denied(plan=plan(tenant_id="other-tenant"))
        self.denied(agent_id="NCA-999")
        self.denied(task_id="TASK-OTHER")
    def test_broken_passport_owner_jti_binding_denied(self):
        from fixtures import sign
        changed=dict(self.passport_doc["claims"]);changed["owner_grant_id"]="b"*64
        self.denied(passport_envelope=sign(changed,self.issuer))
    def test_expired_both_credentials_denied(self):
        self.denied(now=NOW+301)
    def test_extra_signed_metadata_denied(self):
        claim=dict(self.owner_doc["claims"]);claim["execute_tool"]="shell"
        self.denied(owner_envelope={**self.owner_doc,"claims":claim})
    def test_fake_authorized_plan_denied(self):
        self.denied(plan={**self.plan,"execution_authorized":True})
    def test_unknown_or_same_trust_root_denied(self):
        public=self.authorities.owner_public_key
        with self.assertRaises(SkillValidationError):
            PinnedAuthorities(public,public,"owner-test-key-01","issuer-test-key-01")
    def test_missing_revocation_enforcement_denied(self):
        with self.assertRaises(SkillValidationError):
            SkillAdmission(self.authorities,self.replay,None)
    def test_expired_owner_even_with_new_passport_denied(self):
        from fixtures import sign
        changed=dict(self.owner_doc["claims"])
        changed["expires_at"]=NOW-1
        self.denied(owner_envelope=sign(changed,self.owner))
    def test_owner_stopped_pair_never_recorded(self):
        self.denied(owner_kill_switch=True)
        self.assertEqual(self.replay._connect().execute("SELECT COUNT(*) FROM consumed").fetchone()[0],0)

if __name__=="__main__":unittest.main()
