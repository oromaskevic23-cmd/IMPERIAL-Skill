import json
import unittest
from fixtures import manifest
from imperial_skill.manifest import (canonical_json, validate_manifest,
                                     manifest_digest, read_json_strict, SkillValidationError)

class ManifestTests(unittest.TestCase):
    def test_valid_manifest_is_data_not_permission(self):
        m = validate_manifest(manifest())
        self.assertFalse(m["production_authorized"])
        self.assertEqual(m["spending_usd"],0)
        self.assertTrue(m["owner_approval_required"])
    def test_hash_deterministic_independent_of_mapping_order(self):
        m=manifest()
        self.assertEqual(manifest_digest(m),manifest_digest(dict(reversed(list(m.items())))))
    def test_extra_field_or_execution_entrypoint_denied(self):
        for x in ({"entrypoint":"python -c evil"},{"shell":"sh"},{"tools":["browser"]}):
            with self.subTest(x=x),self.assertRaises(SkillValidationError):
                validate_manifest(manifest(**x))
    def test_unsafe_effects_or_false_security_gate_denied(self):
        for x in ({"external_effects":True},{"production_authorized":True},
                  {"spending_usd":100},{"spending_usd":False},
                  {"owner_approval_required":False},{"data_only":False},
                  {"independent_qa_required":False}):
            with self.subTest(x=x),self.assertRaises(SkillValidationError):
                validate_manifest(manifest(**x))
    def test_capability_allowlist_and_unique(self):
        for cap in (["execute:payment"],["read:public","read:public"],[],
                    ["run:browser"],["simulate:task",{}]):
            with self.subTest(cap=cap),self.assertRaises(SkillValidationError):
                validate_manifest(manifest(capabilities=cap))
    def test_no_cross_domain_or_unrecognized_domain(self):
        for x in ("CRYPTO_IMPERIAL", "PAYMENTS", ["CODE_ENGINEERING"], None):
            with self.subTest(x=x),self.assertRaises(SkillValidationError):
                validate_manifest(manifest(runtime_domain=x))
    def test_semantic_versions_without_leading_zero(self):
        for ver in ("0.01.0","latest","1.0","1.0.0+prod",0):
            with self.subTest(ver=ver),self.assertRaises(SkillValidationError):
                validate_manifest(manifest(version=ver))
    def test_unexpected_python_data_denied(self):
        for x in ({"input_fields":[[]]},{"output_fields":[{"exec":1}]},
                  {"dependencies":[{"skill_id":"x","version":"a"}]},
                  {"risk_tier":[]},{"tenant_id":{}},{"max_input_bytes":True}):
            with self.subTest(x=x),self.assertRaises(SkillValidationError):
                validate_manifest(manifest(**x))
    def test_dependencies_unique_no_self(self):
        dep={"skill_id":"imperial.skill.other-code","version":"0.1.0"}
        with self.assertRaises(SkillValidationError):
            validate_manifest(manifest(dependencies=[dep,dep]))
        with self.assertRaises(SkillValidationError):
            validate_manifest(manifest(dependencies=[{"skill_id":"imperial.skill.code-review",
                                                     "version":"0.1.0"}]))
    def test_duplicate_json_keys_rejected(self):
        with self.assertRaisesRegex(SkillValidationError,"DUPLICATE_JSON_KEY"):
            read_json_strict(b'{"schema":"x","schema":"y"}')
    def test_nonfinite_json_rejected(self):
        with self.assertRaises(SkillValidationError):
            read_json_strict(b'{"number": NaN}')
        with self.assertRaises(SkillValidationError):
            canonical_json({"number":float("nan")})
    def test_size_limit(self):
        with self.assertRaises(SkillValidationError):
            read_json_strict(b"x"*65537)
    def test_deep_copy_from_untrusted_caller(self):
        original=manifest()
        checked=validate_manifest(original)
        checked["input_fields"].append("injected")
        self.assertEqual(original["input_fields"],["task_id","source_sha256"])
    def test_exam_hash_required(self):
        with self.assertRaises(SkillValidationError):
            validate_manifest(manifest(exam_sha256="NOT_A_REAL_HASH"))
    def test_boolean_budget_and_resource_denied(self):
        for x in ({"max_input_bytes":0},{"max_output_bytes":False},
                  {"max_input_bytes":1048577}):
            with self.subTest(x=x),self.assertRaises(SkillValidationError):
                validate_manifest(manifest(**x))
