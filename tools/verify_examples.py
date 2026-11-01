"""Verify that example Skill manifests bind to real offline exam definitions."""
from pathlib import Path
from imperial_skill.manifest import read_json_strict
from imperial_skill.registry import SkillRegistry
from imperial_skill.exams import validate_exam,grade_offline_exam

BASE=Path(__file__).resolve().parents[1]
EXAMPLES=BASE/"examples"
def check():
    registry=SkillRegistry()
    count=0
    for p in sorted((EXAMPLES/"skills").glob("*.json")):
        manifest=read_json_strict(p.read_bytes())
        exam=read_json_strict((EXAMPLES/"exams"/p.name).read_bytes())
        metadata=validate_exam(exam)
        assert manifest["exam_sha256"]==metadata["exam_sha256"],"EXAM_HASH_MISMATCH"
        assert manifest["skill_id"]==exam["skill_id"],"SKILL_EXAM_ID_MISMATCH"
        assert manifest["version"]==exam["version"],"SKILL_EXAM_VERSION_MISMATCH"
        registry.register(manifest)
        count+=1
    plan=registry.resolve(tenant_id="imperial-internal",orchestrator_id="engineering-orch",
              runtime_domain="CODE_ENGINEERING",skill_id="imperial.skill.code-draft",
              version="0.1.0")
    assert len(plan["steps"])==2 and plan["execution_authorized"] is False
    e=read_json_strict((EXAMPLES/"exams"/"code-review.json").read_bytes())
    responses=read_json_strict((EXAMPLES/"exams"/"code-review-responses.json").read_bytes())
    result=grade_offline_exam(e,{k:v.encode("utf-8") for k,v in responses.items()})
    assert result["reference_match_pass"] is True
    assert result["independent_qa_verified"] is False
    print("EXAMPLE_CONTRACTS_VERIFIED",count,"PLAN_STEPS",len(plan["steps"]),
          "OFFLINE_REFERENCE_MATCH",result["matches"],"REAL_INDEPENDENT_QA",False)
if __name__=="__main__":
    check()
