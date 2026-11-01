"""Read-only contract bridge to IMPERIAL-Plugins, HANTER and VELION.

No direct import of another project, account access, network or LLM invocation.
These are PROPOSED integration contracts; not evidence of an operational bridge.
"""
from __future__ import annotations
import copy
import hashlib
from .manifest import (validate_manifest, canonical_json,
                       SkillValidationError, IDENT, SHA256)

INTENT_FIELDS=frozenset({
    "schema","task_id","agent_id","tenant_id","orchestrator_id",
    "runtime_domain","skill_plan_sha256","input_sha256",
    "mode","stage","execution_authorized","external_effects",
    "production_authorized","spending_usd","intent_sha256",
})

def to_plugins_manifest(skill: dict) -> dict:
    """Strict compatibility with IMPERIAL-Plugins v0.3 data-only manifest format."""
    s=validate_manifest(skill)
    suffix=s["skill_id"][len("imperial.skill."):]
    plugin_id="imperial.skill-"+suffix
    if len(plugin_id)>72:
        raise SkillValidationError("PLUGIN_ID_LENGTH_DENIED")
    description="Enterprise Skill descriptor only; "+s["description"]
    return {"id":plugin_id,"version":s["version"],
            "capabilities":list(s["capabilities"]),
            "description":description[:300]}

def _verify_plan(plan: object) -> dict:
    if type(plan) is not dict or set(plan) != {
        "schema","tenant_id","orchestrator_id","runtime_domain","steps",
        "stage","owner_approval_verified","ai_passport_verified",
        "independent_qa_verified","execution_authorized",
        "production_authorized","external_effects","spending_usd","plan_sha256"}:
        raise SkillValidationError("SKILL_PLAN_SCHEMA_DENIED")
    payload={k:v for k,v in plan.items() if k!="plan_sha256"}
    digest=hashlib.sha256(canonical_json(payload)).hexdigest()
    if (plan["schema"]!="imperial.skill.plan.v1"
        or plan["stage"]!="PLAN_ONLY"
        or plan["execution_authorized"] is not False
        or plan["production_authorized"] is not False
        or plan["external_effects"] is not False
        or plan["owner_approval_verified"] is not False
        or plan["ai_passport_verified"] is not False
        or plan["independent_qa_verified"] is not False
        or type(plan["spending_usd"]) is not int or plan["spending_usd"]!=0
        or plan["plan_sha256"]!=digest
        or type(plan["steps"]) is not list
        or not plan["steps"]):
        raise SkillValidationError("UNTRUSTED_SKILL_PLAN")
    return copy.deepcopy(plan)

def make_hanter_intent(*, skill_plan: dict, agent_id: str, task_id: str,
                       input_data: bytes, mode: str = "BALANCED") -> dict:
    p=_verify_plan(skill_plan)
    if (type(agent_id) is not str or not IDENT.fullmatch(agent_id)
        or type(task_id) is not str or not IDENT.fullmatch(task_id)
        or type(input_data) is not bytes or not 0<len(input_data)<=65536
        or mode not in ("FAST","BALANCED","MAX")):
        raise SkillValidationError("INTENT_SCOPE_OR_INPUT_DENIED")
    payload={"schema":"imperial.hanter.skill-intent.v1",
             "task_id":task_id,"agent_id":agent_id,
             "tenant_id":p["tenant_id"],"orchestrator_id":p["orchestrator_id"],
             "runtime_domain":p["runtime_domain"],
             "skill_plan_sha256":p["plan_sha256"],
             "input_sha256":hashlib.sha256(input_data).hexdigest(),
             "mode":mode,"stage":"INTENT_PROPOSAL_ONLY",
             "execution_authorized":False,"external_effects":False,
             "production_authorized":False,"spending_usd":0}
    return {**payload,"intent_sha256":hashlib.sha256(canonical_json(payload)).hexdigest()}

def verify_hanter_intent(intent: object, *, expected_plan: dict,
                         expected_agent_id: str, expected_task_id: str,
                         input_data: bytes) -> bool:
    try:
        plan=_verify_plan(expected_plan)
        if type(intent) is not dict or set(intent)!=INTENT_FIELDS:
            return False
        if (intent["agent_id"]!=expected_agent_id or intent["task_id"]!=expected_task_id
            or type(intent["mode"]) is not str or intent["mode"] not in ("FAST","BALANCED","MAX")):
            return False
        original=make_hanter_intent(skill_plan=plan,agent_id=expected_agent_id,
              task_id=expected_task_id,input_data=input_data,mode=intent["mode"])
        return canonical_json(original)==canonical_json(intent)
    except (SkillValidationError,TypeError,ValueError,OverflowError):
        return False

def velion_route_hint(intent: dict, *, approved_model: str) -> dict:
    """A VELION configuration hint; never makes an actual model call."""
    if (type(intent) is not dict or set(intent)!=INTENT_FIELDS
        or type(approved_model) is not str or not IDENT.fullmatch(approved_model)
        or intent.get("stage")!="INTENT_PROPOSAL_ONLY"
        or intent.get("execution_authorized") is not False
        or intent.get("production_authorized") is not False
        or intent.get("external_effects") is not False
        or type(intent.get("spending_usd")) is not int
        or intent["spending_usd"] != 0
        or intent.get("schema") != "imperial.hanter.skill-intent.v1"
        or type(intent.get("skill_plan_sha256")) is not str
        or not SHA256.fullmatch(intent["skill_plan_sha256"])
        or type(intent.get("input_sha256")) is not str
        or not SHA256.fullmatch(intent["input_sha256"])
        or any(type(intent.get(k)) is not str or not IDENT.fullmatch(intent[k])
               for k in ("tenant_id", "orchestrator_id", "agent_id", "task_id"))
        or type(intent.get("runtime_domain")) is not str):
        raise SkillValidationError("VELION_INTENT_DENIED")
    payload={k:v for k,v in intent.items() if k!="intent_sha256"}
    if hashlib.sha256(canonical_json(payload)).hexdigest()!=intent.get("intent_sha256"):
        raise SkillValidationError("VELION_INTENT_TAMPERED")
    return {"stage":"VELION_MODEL_PLAN_ONLY","mode":intent["mode"],
            "tenant_id":intent["tenant_id"],"orchestrator_id":intent["orchestrator_id"],
            "agent_id":intent["agent_id"],"task_id":intent["task_id"],
            "model_hint":approved_model,"intent_sha256":intent["intent_sha256"],
            "actual_model_called":False,"execution_authorized":False,
            "production_authorized":False,"external_effects":False,"spending_usd":0}
