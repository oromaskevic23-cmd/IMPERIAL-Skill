import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout,redirect_stderr
from pathlib import Path
from fixtures import manifest
from imperial_skill.audit import LocalAuditLedger
from imperial_skill.cli import main

class CliTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.d=Path(temp.name)
    def call(self,*args):
        out=io.StringIO()
        err=io.StringIO()
        with redirect_stdout(out),redirect_stderr(err):
            ret=main(list(map(str,args)))
        return ret,out.getvalue(),err.getvalue()
    def test_validate_manifest(self):
        f=self.d/"manifest.json"
        f.write_text(json.dumps(manifest()),encoding="utf-8")
        rc,out,_=self.call("validate",f)
        self.assertEqual(rc,0)
        self.assertFalse(json.loads(out)["execution_authorized"])
    def test_validate_denies_untrusted_nonfinite(self):
        f=self.d/"bad.json";f.write_text('{"bad":NaN}')
        rc,_,err=self.call("validate",f)
        self.assertEqual(rc,2)
        self.assertIn('"ok": false',err)
    def test_offline_plan_no_execution_authority(self):
        f=self.d/"skills";f.mkdir()
        (f/"review.json").write_text(json.dumps(manifest()))
        rc,out,_=self.call("plan","--directory",f,
                           "--tenant","imperial-internal","--orchestrator","engineering-orch",
                           "--domain","CODE_ENGINEERING",
                           "--skill-id","imperial.skill.code-review","--version","0.1.0")
        self.assertEqual(rc,0)
        self.assertFalse(json.loads(out)["execution_authorized"])
    def test_unknown_ledger_does_not_modify_database(self):
        import sqlite3
        f=self.d/"foreign.sqlite"
        with sqlite3.connect(f) as db: db.execute("CREATE TABLE alien(x TEXT)")
        before=f.read_bytes()
        rc,_,_=self.call("audit-verify",f)
        self.assertEqual(rc,2)
        self.assertEqual(before,f.read_bytes())
        with sqlite3.connect(f) as db:
            self.assertIsNone(db.execute("SELECT name FROM sqlite_master WHERE name='audit'").fetchone())
    def test_existing_ledger_can_be_inspected_readonly(self):
        f=self.d/"audit.sqlite"
        audit=LocalAuditLedger(f)
        audit.append({"event":"ONE"})
        rc,out,_=self.call("audit-verify",f)
        self.assertEqual(rc,0)
        self.assertEqual(json.loads(out)["entries"],1)
    def test_empty_ledger_not_claimed_as_evidence(self):
        f=self.d/"audit.sqlite"
        LocalAuditLedger(f)
        rc,_,err=self.call("audit-verify",f)
        self.assertEqual(rc,2)
        self.assertIn("SkillValidationError",err)
