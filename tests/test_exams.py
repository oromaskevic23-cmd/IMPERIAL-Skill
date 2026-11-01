import hashlib
import unittest
from imperial_skill.exams import validate_exam,grade_offline_exam
from imperial_skill.manifest import SkillValidationError

def exam():
    return {"schema":"imperial.skill.offline-exam.v1",
            "skill_id":"imperial.skill.code-review","version":"0.1.0",
            "cases":[{"case_id":"correct_review","expected_sha256":hashlib.sha256(b"OK").hexdigest(),"critical":True},
                     {"case_id":"rejected_task","expected_sha256":hashlib.sha256(b"DENIED").hexdigest(),"critical":True}],
            "minimum_percent":100,"independent_qa_required":True}
class ExamTests(unittest.TestCase):
    def test_reference_match_is_not_independent_qa(self):
        r=grade_offline_exam(exam(),{"correct_review":b"OK","rejected_task":b"DENIED"})
        self.assertTrue(r["reference_match_pass"])
        self.assertFalse(r["independent_qa_verified"])
        self.assertFalse(r["professional_certified"])
        self.assertFalse(r["production_authorized"])
    def test_incorrect_case_fails(self):
        r=grade_offline_exam(exam(),{"correct_review":b"WRONG","rejected_task":b"DENIED"})
        self.assertFalse(r["reference_match_pass"])
        self.assertEqual(r["matches"],1)
    def test_missing_extra_responses_denied(self):
        for r in ({"correct_review":b"OK"},{"correct_review":b"OK","rejected_task":b"DENIED","extra":b"x"}):
            with self.assertRaises(SkillValidationError):grade_offline_exam(exam(),r)
    def test_invalid_untrusted_input_rejected(self):
        for x in ("OK",b"x"*65537,None,{"code":"ok"}):
            with self.subTest(x=type(x)),self.assertRaises(SkillValidationError):
                grade_offline_exam(exam(),{"correct_review":x,"rejected_task":b"DENIED"})
    def test_cannot_skip_critical_case_or_lower_threshold(self):
        e=exam();e["minimum_percent"]=80
        with self.assertRaises(SkillValidationError):validate_exam(e)
        e=exam();e["cases"][0]["critical"]=False
        with self.assertRaises(SkillValidationError):validate_exam(e)
    def test_duplicate_exam_case_denied(self):
        e=exam();e["cases"].append(e["cases"][0])
        with self.assertRaises(SkillValidationError):validate_exam(e)
