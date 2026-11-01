"""Local tamper-evident Audit Ledger. Not immutable or externally attested."""
from __future__ import annotations
import hashlib
import hmac
import json
import sqlite3
from pathlib import Path
from .manifest import canonical_json, SkillValidationError

ZERO = "0" * 64

class LocalAuditLedger:
    def __init__(self, path: str | Path):
        self.path = str(path)
        with self._db() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS audit(
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                previous_sha256 TEXT NOT NULL,
                event_json TEXT NOT NULL,
                entry_sha256 TEXT NOT NULL
            )""")
            db.execute("""CREATE TRIGGER IF NOT EXISTS audit_block_update
                BEFORE UPDATE ON audit BEGIN SELECT RAISE(ABORT, 'AUDIT_APPEND_ONLY'); END""")
            db.execute("""CREATE TRIGGER IF NOT EXISTS audit_block_delete
                BEFORE DELETE ON audit BEGIN SELECT RAISE(ABORT, 'AUDIT_APPEND_ONLY'); END""")

    def _db(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=10)
        db.execute("PRAGMA busy_timeout=10000")
        return db

    @staticmethod
    def _hash(seq: int, previous: str, raw: str) -> str:
        payload = b"IMPERIAL_SKILL_LOCAL_AUDIT_V1\n" + canonical_json(
            {"seq": seq, "previous_sha256": previous, "event_json": raw})
        return hashlib.sha256(payload).hexdigest()

    @classmethod
    def _verify_db(cls, db: sqlite3.Connection) -> tuple[int, str]:
        rows = db.execute(
            "SELECT seq,previous_sha256,event_json,entry_sha256 FROM audit ORDER BY seq"
        ).fetchall()
        previous = ZERO
        for expected, (seq, prev, raw, signature) in enumerate(rows, 1):
            if (seq != expected or not hmac.compare_digest(previous, prev)
                or not hmac.compare_digest(cls._hash(seq, prev, raw), signature)):
                raise SkillValidationError("AUDIT_LEDGER_INTEGRITY_FAILURE")
            previous = signature
        return len(rows), previous

    def append(self, event: dict) -> dict:
        if not isinstance(event, dict):
            raise SkillValidationError("AUDIT_EVENT_NOT_OBJECT")
        raw = canonical_json(event).decode("utf-8")
        if len(raw) > 16384:
            raise SkillValidationError("AUDIT_EVENT_TOO_LARGE")
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            count, previous = self._verify_db(db)
            seq = count + 1
            signature = self._hash(seq, previous, raw)
            db.execute("INSERT INTO audit(seq,previous_sha256,event_json,entry_sha256)"
                       " VALUES(?,?,?,?)", (seq, previous, raw, signature))
            return {"seq": seq, "entry_sha256": signature,
                    "previous_sha256": previous, "externally_attested": False}

    def verify(self) -> dict:
        with self._db() as db:
            try:
                count, latest = self._verify_db(db)
                return {"verified": True, "entries": count, "head_sha256": latest,
                        "immutable": False, "externally_attested": False}
            except (sqlite3.Error, SkillValidationError, TypeError, ValueError):
                return {"verified": False, "immutable": False,
                        "externally_attested": False}

    def events(self) -> list[dict]:
        with self._db() as db:
            self._verify_db(db)
            return [json.loads(row[0]) for row in db.execute(
                "SELECT event_json FROM audit ORDER BY seq").fetchall()]
