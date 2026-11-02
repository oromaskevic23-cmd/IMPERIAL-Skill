"""Original adversarial offline regression tests for the four guarded skills."""
import unittest
from imperial_skill.trending_skills import (
    SkillBoundaryError, desktop_ref_review, model_dataset_review,
    public_html_review, worktree_status_review,
)

class TrendingSkillsTests(unittest.TestCase):
    def snapshot(self):
        return {'ok':True,'data':{'complete':True,'snapshot_id':'s1234',
                'tree':{'role':'window','children':[
                  {'ref_id':'@s1234:e1','available_actions':['Click'],'name':'Private name'}]}}}

    def test_desktop_ref_scoped_not_acted_and_redacted(self):
        r=desktop_ref_review(self.snapshot(),'@s1234:e1','click')
        self.assertFalse(r['action_executed'])
        self.assertFalse(r['execution_authorized'])
        self.assertNotIn('Private name',str(r))

    def test_desktop_stale_ref_denied(self):
        with self.assertRaises(SkillBoundaryError):
            desktop_ref_review(self.snapshot(),'@s9999:e1','click')

    def test_desktop_unavailable_type_denied(self):
        with self.assertRaises(SkillBoundaryError):
            desktop_ref_review(self.snapshot(),'@s1234:e1','type')

    def test_desktop_duplicate_ref_denied(self):
        s=self.snapshot()
        s['data']['tree']['children'].append(s['data']['tree']['children'][0])
        with self.assertRaises(SkillBoundaryError):
            desktop_ref_review(s,'@s1234:e1')

    def test_dataset_synthetic_only(self):
        r=model_dataset_review(
            [{'prompt':'a','expected':'b','origin':'original-synthetic'}],
            [{'prompt':'c','expected':'d','origin':'original-synthetic'}])
        self.assertEqual(r['training_cases'],1)
        self.assertFalse(r['model_trained'])
        self.assertFalse(r['execution_authorized'])

    def test_dataset_leakage_and_external_origin_denied(self):
        row={'prompt':'a','expected':'b','origin':'original-synthetic'}
        with self.assertRaises(SkillBoundaryError):
            model_dataset_review([row],[row])
        with self.assertRaises(SkillBoundaryError):
            model_dataset_review([row],[{'prompt':'b','expected':'c','origin':'web'}])

    def test_html_offline_and_no_scripts(self):
        r=public_html_review('https://example.org/','<h1>Public &amp; safe</h1><script>private</script>',
                             approved=True,robots_allowed=True)
        self.assertEqual(r['texts'],['Public & safe'])
        self.assertFalse(r['network_called'])

    def test_html_requires_consent_and_public_host(self):
        for url,approved in [('https://example.org',False),('http://example.org',True),
                             ('https://127.0.0.1',True),('https://localhost',True)]:
            with self.subTest(url=url),self.assertRaises(SkillBoundaryError):
                public_html_review(url,'<p>text</p>',approved=approved,robots_allowed=True)

    def test_html_robots_denial(self):
        with self.assertRaises(SkillBoundaryError):
            public_html_review('https://example.org','<h1>test</h1>',approved=True,robots_allowed=False)

    def test_worktree_read_only(self):
        data='worktree /tmp/a\nHEAD '+'a'*40+'\nbranch refs/heads/main\n\n'+\
             'worktree /tmp/b\nHEAD '+'b'*40+'\nbranch refs/heads/feature\n'
        r=worktree_status_review(data)
        self.assertEqual(r['worktree_count'],2)
        self.assertFalse(r['git_command_executed'])

    def test_worktree_duplicate_branches_denied(self):
        data='worktree /tmp/a\nHEAD '+'a'*40+'\nbranch refs/heads/main\n\n'+\
             'worktree /tmp/b\nHEAD '+'b'*40+'\nbranch refs/heads/main\n'
        with self.assertRaises(SkillBoundaryError):
            worktree_status_review(data)

    def test_worktree_malformed_denied(self):
        for data in ('','HEAD '+'a'*40,'worktree /tmp/a\ncommand rm -rf /'):
            with self.subTest(data=data),self.assertRaises(SkillBoundaryError):
                worktree_status_review(data)
if __name__=='__main__':
    unittest.main()
