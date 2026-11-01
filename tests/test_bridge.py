import unittest
from fixtures import manifest,plan
from imperial_skill.bridge import (
    to_plugins_manifest,make_hanter_intent,verify_hanter_intent,velion_route_hint)
from imperial_skill.manifest import SkillValidationError

class BridgeTests(unittest.TestCase):
    def test_exact_plugin_contract_not_runtime_credential(self):
        m=to_plugins_manifest(manifest())
        self.assertEqual(set(m),{"id","version","capabilities","description"})
        self.assertEqual(m["id"],"imperial.skill-code-review")
        self.assertEqual(m["capabilities"],["read:public","simulate:task"])
    def test_does_not_convert_external_effects_to_plugin(self):
        with self.assertRaises(SkillValidationError):
            to_plugins_manifest(manifest(external_effects=True))
    def test_hanter_intent_binds_task_route_and_input_sha256(self):
        intent=make_hanter_intent(skill_plan=plan(),agent_id="NCA-424",task_id="TASK-001",
                                  input_data=b"private synthetic request")
        self.assertEqual(intent["stage"],"INTENT_PROPOSAL_ONLY")
        self.assertFalse(intent["execution_authorized"])
        self.assertTrue(verify_hanter_intent(intent,expected_plan=plan(),
                     expected_agent_id="NCA-424",expected_task_id="TASK-001",
                     input_data=b"private synthetic request"))
    def test_input_replacement_denied(self):
        intent=make_hanter_intent(skill_plan=plan(),agent_id="NCA-424",
                                  task_id="TASK-001",input_data=b"original")
        self.assertFalse(verify_hanter_intent(intent,expected_plan=plan(),
                     expected_agent_id="NCA-424",expected_task_id="TASK-001",
                     input_data=b"replaced"))
    def test_cross_tenant_agent_or_orchestrator_denied(self):
        intent=make_hanter_intent(skill_plan=plan(),agent_id="NCA-424",
                                  task_id="TASK-001",input_data=b"real input")
        for changes in ({"agent_id":"NCA-999"},{"tenant_id":"other-tenant"},
                        {"orchestrator_id":"security-orch"},
                        {"task_id":"TASK-002"},{"stage":"DISPATCHED"}):
            with self.subTest(changes=changes):
                self.assertFalse(verify_hanter_intent(intent|changes,expected_plan=plan(),
                         expected_agent_id="NCA-424",expected_task_id="TASK-001",
                         input_data=b"real input"))
    def test_max_is_mode_not_new_model(self):
        intent=make_hanter_intent(skill_plan=plan(),agent_id="NCA-424",task_id="TASK-001",
                                  input_data=b"synthetic",mode="MAX")
        hint=velion_route_hint(intent,approved_model="local-qwen-1.5b")
        self.assertEqual(hint["mode"],"MAX")
        self.assertFalse(hint["actual_model_called"])
        self.assertFalse(hint["production_authorized"])
    def test_tampered_intent_never_becomes_model_plan(self):
        intent=make_hanter_intent(skill_plan=plan(),agent_id="NCA-424",
                                  task_id="TASK-001",input_data=b"synthetic")
        for bad in ({"mode":"UNSAFE"},{"execution_authorized":True},
                    {"intent_sha256":"0"*64}):
            with self.subTest(bad=bad),self.assertRaises(SkillValidationError):
                velion_route_hint(intent|bad,approved_model="local-qwen-1.5b")
    def test_reject_untrusted_input(self):
        for bad in (b"",b"x"*65537,"text"):
            with self.subTest(bad=str(type(bad))),self.assertRaises(SkillValidationError):
                make_hanter_intent(skill_plan=plan(),agent_id="NCA-424",
                     task_id="TASK-001",input_data=bad)
    def test_invalid_model_id_denied(self):
        intent=make_hanter_intent(skill_plan=plan(),agent_id="NCA-424",task_id="TASK-001",input_data=b"ok")
        with self.assertRaises(SkillValidationError):
            velion_route_hint(intent,approved_model="https://untrusted-url")
