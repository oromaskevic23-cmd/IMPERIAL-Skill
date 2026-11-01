import concurrent.futures
import sqlite3
import tempfile
import unittest
from pathlib import Path
from imperial_skill.audit import LocalAuditLedger
from imperial_skill.manifest import SkillValidationError

class AuditTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path=Path(tmp.name)/"audit.db"
        self.ledger=LocalAuditLedger(self.path)
    def test_append_and_verify(self):
        a=self.ledger.append({"event":"ROUTE_PROPOSED","production":False})
        b=self.ledger.append({"event":"QA_EVALUATED","production":False})
        self.assertEqual(a["seq"],1)
        self.assertEqual(b["previous_sha256"],a["entry_sha256"])
        self.assertEqual(self.ledger.verify()["entries"],2)
        self.assertFalse(self.ledger.verify()["externally_attested"])
    def test_reopen_preserves_chain(self):
        self.ledger.append({"case":"first"})
        r=LocalAuditLedger(self.path)
        self.assertTrue(r.verify()["verified"])
        self.assertEqual(r.events()[0],{"case":"first"})
    def test_tamper_and_rehash_denied(self):
        self.ledger.append({"case":"first"})
        with sqlite3.connect(self.path) as db:
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute("UPDATE audit SET event_json='forged' WHERE seq=1")
        self.assertTrue(self.ledger.verify()["verified"])
    def test_chain_detects_deleted_history_by_integrity_after_trigger_removed(self):
        self.ledger.append({"case":"first"})
        self.ledger.append({"case":"second"})
        with sqlite3.connect(self.path) as db:
            db.execute("DROP TRIGGER audit_block_delete")
            db.execute("DELETE FROM audit WHERE seq=1")
        self.assertFalse(self.ledger.verify()["verified"])
        with self.assertRaises(SkillValidationError):
            self.ledger.append({"case":"third"})
    def test_parallel_appends_have_strict_sequence(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(lambda n:self.ledger.append({"i":n}),range(20)))
        self.assertEqual(self.ledger.verify()["entries"],20)
    def test_bad_event_rejected(self):
        with self.assertRaises(SkillValidationError):self.ledger.append("not_a_dict")
    def test_no_immutable_external_claim(self):
        self.ledger.append({"no_external_anchor":True})
        self.assertFalse(self.ledger.verify()["immutable"])
