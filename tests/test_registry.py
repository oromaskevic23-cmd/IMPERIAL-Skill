import unittest
from fixtures import manifest
from imperial_skill.registry import SkillRegistry
from imperial_skill.manifest import SkillValidationError

def item(name,depends=(),**kwargs):
    return manifest(skill_id=name,dependencies=[
        {"skill_id":skill,"version":"0.1.0"} for skill in depends],**kwargs)

class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.r=SkillRegistry()
    def resolve(self,name="imperial.skill.code-review",tenant="imperial-internal",
                orch="engineering-orch",domain="CODE_ENGINEERING"):
        return self.r.resolve(tenant_id=tenant,orchestrator_id=orch,skill_id=name,
                              version="0.1.0",runtime_domain=domain)
    def test_registry_plan_never_executes(self):
        self.r.register(manifest())
        p=self.resolve()
        self.assertEqual(p["stage"],"PLAN_ONLY")
        self.assertFalse(p["execution_authorized"])
        self.assertFalse(p["ai_passport_verified"])
        self.assertFalse(p["production_authorized"])
    def test_order_dependencies_topologically(self):
        self.r.register(item("imperial.skill.base-check"))
        self.r.register(item("imperial.skill.code-review",
                             ["imperial.skill.base-check"]))
        p=self.resolve()
        self.assertEqual([x["skill_id"] for x in p["steps"]],
           ["imperial.skill.base-check","imperial.skill.code-review"])
    def test_duplicate_registration_denied(self):
        self.r.register(manifest())
        with self.assertRaises(SkillValidationError):self.r.register(manifest())
    def test_missing_version_not_auto_upgraded(self):
        self.r.register(manifest(version="0.2.0"))
        with self.assertRaisesRegex(SkillValidationError,"MISSING_PINNED"):
            self.resolve()
    def test_cyclic_dependencies_denied(self):
        self.r.register(item("imperial.skill.code-review",["imperial.skill.base-check"]))
        self.r.register(item("imperial.skill.base-check",["imperial.skill.code-review"]))
        with self.assertRaisesRegex(SkillValidationError,"CYCLIC"):
            self.resolve()
    def test_cross_tenant_dependency_denied(self):
        self.r.register(item("imperial.skill.code-review",["imperial.skill.base-check"]))
        self.r.register(item("imperial.skill.base-check",tenant_id="other-tenant"))
        with self.assertRaisesRegex(SkillValidationError,"MISSING_PINNED"):
            self.resolve()
    def test_cross_orchestrator_dependency_denied(self):
        self.r.register(item("imperial.skill.code-review",["imperial.skill.base-check"]))
        self.r.register(item("imperial.skill.base-check",orchestrator_id="security-orch"))
        with self.assertRaisesRegex(SkillValidationError,"CROSS_ORCHESTRATOR"):
            self.resolve()
    def test_cross_runtime_domain_denied(self):
        self.r.register(item("imperial.skill.code-review",["imperial.skill.base-check"]))
        self.r.register(item("imperial.skill.base-check",runtime_domain="SECURITY_DEFENSIVE"))
        with self.assertRaisesRegex(SkillValidationError,"CROSS_RUNTIME"):
            self.resolve()
    def test_plan_integrity_stable(self):
        self.r.register(manifest())
        self.assertEqual(self.resolve()["plan_sha256"],self.resolve()["plan_sha256"])
    def test_snapshot_does_not_expose_mutable_objects(self):
        m=manifest();self.r.register(m)
        m["description"]="edited upstream"
        a=self.r.snapshot();a[0]["capabilities"].append("execute:payment")
        self.assertNotIn("execute:payment",self.r.snapshot()[0]["capabilities"])
        self.assertNotEqual(self.r.snapshot()[0]["description"],"edited upstream")
