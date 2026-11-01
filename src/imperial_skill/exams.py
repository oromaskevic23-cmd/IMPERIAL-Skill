"""Deterministic offline grading contracts, not a replacement for independent QA."""
from __future__ import annotations
import hashlib
from .manifest import SkillValidationError, SKILL_ID, VERSION, SHA256, canonical_json

def validate_exam(exam: object) -> dict:
    if type(exam) is not dict or set(exam) != {
        "schema", "skill_id", "version", "cases", "minimum_percent",
        "independent_qa_required"
    }:
        raise SkillValidationError("EXAM_SCHEMA_DENIED")
    if (exam["schema"] != "imperial.skill.offline-exam.v1"
        or type(exam["skill_id"]) is not str or not SKILL_ID.fullmatch(exam["skill_id"])
        or type(exam["version"]) is not str or not VERSION.fullmatch(exam["version"])
        or exam["minimum_percent"] != 100 or type(exam["minimum_percent"]) is not int
        or exam["independent_qa_required"] is not True):
        raise SkillValidationError("EXAM_POLICY_DENIED")
    cases = exam["cases"]
    if type(cases) is not list or not 1 <= len(cases) <= 128:
        raise SkillValidationError("EXAM_CASES_DENIED")
    names = set()
    for case in cases:
        if (type(case) is not dict or set(case) != {"case_id", "expected_sha256", "critical"}
            or type(case["case_id"]) is not str
            or not case["case_id"].replace("-", "").replace("_", "").isalnum()
            or len(case["case_id"]) > 64
            or type(case["expected_sha256"]) is not str
            or not SHA256.fullmatch(case["expected_sha256"])
            or case["critical"] is not True
            or case["case_id"] in names):
            raise SkillValidationError("INVALID_EXAM_CASE")
        names.add(case["case_id"])
    canonical_json(exam)
    return {"exam_sha256": hashlib.sha256(canonical_json(exam)).hexdigest(),
            "case_count": len(cases)}

def grade_offline_exam(exam: dict, submissions: object) -> dict:
    meta = validate_exam(exam)
    if type(submissions) is not dict or set(submissions) != {
        case["case_id"] for case in exam["cases"]
    }:
        raise SkillValidationError("EXAM_SUBMISSION_INCOMPLETE")
    checks = []
    for case in exam["cases"]:
        answer = submissions[case["case_id"]]
        if type(answer) is not bytes or len(answer) > 65536:
            raise SkillValidationError("EXAM_RESPONSE_INVALID")
        actual = hashlib.sha256(answer).hexdigest()
        checks.append({"case_id": case["case_id"],
                       "reference_hash_match": actual == case["expected_sha256"],
                       "critical": True})
    matches = sum(x["reference_hash_match"] for x in checks)
    return {"schema": "imperial.skill.offline-exam-result.v1",
            "exam_sha256": meta["exam_sha256"], "cases": checks,
            "matches": matches, "total": len(checks),
            "reference_match_pass": matches == len(checks),
            "independent_qa_verified": False,
            "professional_certified": False,
            "execution_authorized": False,
            "production_authorized": False}
