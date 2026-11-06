"""Offline governance regression tests for five third-party skill adapters.

Copyright (c) 2026 Alexander Nikolaevich Romaskevich.
No remote credentials, vendor API requests, browsers or live permissions are used.
"""
from __future__ import annotations

from pathlib import Path
from copy import deepcopy
import unittest

from imperial_skill.manifest import (
    read_json_strict, validate_manifest, SkillValidationError
)
from imperial_skill.exams import validate_exam, grade_offline_exam
from imperial_skill.registry import SkillRegistry

BASE = Path(__file__).resolve().parents[1]
SLUGS = (
    "perplexity-research",
    "firecrawl-extraction",
    "posthog-analytics",
    "playwright-e2e",
    "composio-mcp-actions",
)


class FiveProviderSkillsTests(unittest.TestCase):
    def load(self, slug: str):
        manifest = read_json_strict(
            (BASE / "examples" / "skills" / f"{slug}.json").read_bytes()
        )
        exam = read_json_strict(
            (BASE / "examples" / "exams" / f"{slug}.json").read_bytes()
        )
        return manifest, exam

    def test_all_five_manifests_registered_and_offline(self):
        registry = SkillRegistry()
        for slug in SLUGS:
            with self.subTest(skill=slug):
                manifest, exam = self.load(slug)
                self.assertEqual(
                    validate_exam(exam)["exam_sha256"],
                    manifest["exam_sha256"]
                )
                self.assertEqual(manifest["skill_id"], exam["skill_id"])
                self.assertEqual(manifest["version"], exam["version"])
                validate_manifest(manifest)
                registry.register(manifest)
                self.assertIs(manifest["data_only"], True)
                self.assertIs(manifest["production_authorized"], False)
                self.assertIs(manifest["external_effects"], False)
                self.assertEqual(manifest["spending_usd"], 0)
                self.assertIs(manifest["independent_qa_required"], True)
                self.assertIs(manifest["owner_approval_required"], True)
                plan = registry.resolve(
                    tenant_id=manifest["tenant_id"],
                    orchestrator_id=manifest["orchestrator_id"],
                    runtime_domain=manifest["runtime_domain"],
                    skill_id=manifest["skill_id"],
                    version=manifest["version"],
                )
                self.assertIs(plan["execution_authorized"], False)

    def test_synthetic_reference_match_never_claims_independent_qa(self):
        for slug in SLUGS:
            with self.subTest(skill=slug):
                _, exam = self.load(slug)
                answers = {
                    "accept-synthetic": ("ALLOW:" + slug).encode("utf-8"),
                    "deny-unsafe": ("DENY:" + slug).encode("utf-8"),
                }
                report = grade_offline_exam(exam, answers)
                self.assertIs(report["reference_match_pass"], True)
                self.assertIs(report["independent_qa_verified"], False)
                self.assertIs(report["execution_authorized"], False)
                self.assertIs(report["production_authorized"], False)

    def test_mutated_manifests_fail_closed(self):
        for slug in SLUGS:
            manifest, _ = self.load(slug)
            for field, forbidden in (
                ("owner_approval_required", False),
                ("independent_qa_required", False),
                ("external_effects", True),
                ("production_authorized", True),
                ("spending_usd", 1),
                ("capabilities", ["execute:external"]),
                ("runtime_domain", "UNSCOPED"),
            ):
                with self.subTest(skill=slug, field=field):
                    modified = deepcopy(manifest)
                    modified[field] = forbidden
                    with self.assertRaises(SkillValidationError):
                        validate_manifest(modified)

    def test_wrong_synthetic_exam_answer_does_not_pass(self):
        for slug in SLUGS:
            _, exam = self.load(slug)
            report = grade_offline_exam(
                exam,
                {"accept-synthetic": b"WRONG", "deny-unsafe": b"WRONG"},
            )
            self.assertIs(report["reference_match_pass"], False)
            self.assertIs(report["execution_authorized"], False)


if __name__ == "__main__":
    unittest.main()
