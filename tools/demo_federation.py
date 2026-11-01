"""Deterministic on-disk demo, with no NCA, network, model or real Owner keys."""
from pathlib import Path
from tempfile import TemporaryDirectory
from imperial_skill.manifest import read_json_strict
from imperial_skill.registry import SkillRegistry
from imperial_skill.bridge import to_plugins_manifest,make_hanter_intent,velion_route_hint
from imperial_skill.exams import grade_offline_exam
from imperial_skill.proofgraph import make_local_proof,verify_local_proof
from imperial_skill.audit import LocalAuditLedger

def main():
    base=Path(__file__).resolve().parents[1]/"examples"
    registry=SkillRegistry()
    for path in sorted((base/"skills").glob("*.json")):
        registry.register(read_json_strict(path.read_bytes()))
    p=registry.resolve(tenant_id="imperial-internal",
             orchestrator_id="engineering-orch",runtime_domain="CODE_ENGINEERING",
             skill_id="imperial.skill.code-draft",version="0.1.0")
    intent=make_hanter_intent(skill_plan=p,agent_id="NCA-424",
                             task_id="TASK-DEMO-01",input_data=b"synthetic demo requirements",mode="MAX")
    model=velion_route_hint(intent,approved_model="qwen-local-coder")
    definition=read_json_strict((base/"exams"/"code-review.json").read_bytes())
    responses=read_json_strict((base/"exams"/"code-review-responses.json").read_bytes())
    result=grade_offline_exam(definition,{k:v.encode("utf-8") for k,v in responses.items()})
    sample=b"NONEXECUTED_SKILL_CODE_DRAFT"
    proof=make_local_proof(plan_sha256=p["plan_sha256"],
              artifact=sample,exam_sha256=p["steps"][0]["manifest_sha256"],
              grade_report=result)
    checked=verify_local_proof(proof,sample,result,previous_sha256="0"*64)
    with TemporaryDirectory() as directory:
        ledger=LocalAuditLedger(Path(directory)/"audit.db")
        receipt=ledger.append({"intent_sha256":intent["intent_sha256"],
                "proof_sha256":proof["proof_sha256"],"lab_only":True})
        assertion=ledger.verify()
    assert len(p["steps"])==2 and model["actual_model_called"] is False
    assert checked["integrity_verified"] is True and checked["independent_qa_verified"] is False
    assert assertion["verified"] is True and assertion["externally_attested"] is False
    assert result["reference_match_pass"] and not result["professional_certified"]
    assert receipt["seq"]==1 and model["production_authorized"] is False
    print("END_TO_END_LOCAL_PIPELINE_PASS",
          "plan_steps",len(p["steps"]), "exam_reference_matches",result["matches"],
          "independent_qa",False,"real_model_calls",0,"production_authorized",False)
if __name__=="__main__":
    main()
