"""Safe read-only CLI. Never executes a Skill, LLM, browser or external platform."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from .manifest import read_json_strict,validate_manifest,manifest_digest,SkillValidationError
from .registry import SkillRegistry
from .audit import LocalAuditLedger
from .exams import grade_offline_exam,validate_exam

def _read(path: Path) -> dict:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 65536:
        raise SkillValidationError("UNSAFE_FILE_OR_SIZE")
    return read_json_strict(path.read_bytes())

def main(argv: list[str] | None = None) -> int:
    parser=argparse.ArgumentParser(prog="imperial-skill",
      description="Enterprise Skill planning and inspection only; no execution authority")
    sub=parser.add_subparsers(dest="command",required=True)
    val=sub.add_parser("validate",help="Validate a Skills manifest and print its SHA-256")
    val.add_argument("manifest",type=Path)
    plan=sub.add_parser("plan",help="Resolve exact dependency graph and return non-executing plan")
    plan.add_argument("--directory",required=True,type=Path)
    plan.add_argument("--tenant",required=True)
    plan.add_argument("--orchestrator",required=True)
    plan.add_argument("--domain",required=True)
    plan.add_argument("--skill-id",required=True)
    plan.add_argument("--version",required=True)
    audit=sub.add_parser("audit-verify",help="Check local SQLite hash-linked Audit Ledger")
    audit.add_argument("db",type=Path)
    exam=sub.add_parser("exam-grade",help="Only reference hash matching; NOT independent QA")
    exam.add_argument("exam",type=Path)
    exam.add_argument("responses",type=Path)
    args=parser.parse_args(argv)
    try:
        if args.command=="validate":
            data=_read(args.manifest)
            validate_manifest(data)
            result={"valid":True,"manifest_sha256":manifest_digest(data),
                    "execution_authorized":False}
        elif args.command=="plan":
            if not args.directory.is_dir() or args.directory.is_symlink():
                raise SkillValidationError("REGISTRY_DIRECTORY_INVALID")
            paths=sorted(args.directory.glob("*.json"))
            if not paths or len(paths)>256:
                raise SkillValidationError("REGISTRY_FILE_COUNT_INVALID")
            registry=SkillRegistry()
            for path in paths:
                registry.register(_read(path))
            result=registry.resolve(tenant_id=args.tenant,orchestrator_id=args.orchestrator,
                 runtime_domain=args.domain,skill_id=args.skill_id,version=args.version)
        elif args.command=="audit-verify":
            if args.db.is_symlink() or not args.db.is_file():
                raise SkillValidationError("LEDGER_FILE_REQUIRED")
            result=LocalAuditLedger(args.db).verify()
            if not result["verified"]:
                raise SkillValidationError("AUDIT_LEDGER_INTEGRITY_FAILURE")
        else:
            definition=_read(args.exam)
            validate_exam(definition)
            responses=_read(args.responses)
            if any(type(x) is not str for x in responses.values()):
                raise SkillValidationError("RESPONSES_MUST_BE_UTF8_STRINGS")
            result=grade_offline_exam(definition,{k:v.encode("utf-8") for k,v in responses.items()})
        print(json.dumps(result,sort_keys=True,indent=2))
        return 0
    except (SkillValidationError, OSError, UnicodeError, ValueError) as exc:
        print(json.dumps({"ok":False,"error":type(exc).__name__,
                          "execution_authorized":False}),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
