# Four original IMPERIAL Core Enterprise Skills — 2 November 2026

**Architect / author:** Alexander Nikolaevich Romaskevich (RomaskevicH).

This change adds original, source-level Skill contracts and bounded offline implementations. It does not copy, fork, vendor or install third-party repositories, use third-party trademarks as IMPERIAL marks, or claim their capabilities as already running in IMPERIAL Core.

| IMPERIAL Skill | External technical reference, no code copied | Upstream license | Scope |
| --- | --- | --- | --- |
| desktop-accessibility | https://github.com/vercel-labs/agent-desktop | Apache-2.0 | Offline, snapshot-scoped accessibility ref inspection; no OS actions |
| model-training-lab | https://github.com/karpathy/nanochat | MIT | Original-synthetic dataset review and train/eval leakage denial; no model training |
| authorized-web-extraction | https://github.com/D4Vinci/Scrapling | BSD-3-Clause | Offline operator-supplied HTML inspection only; no fetch/crawl |
| parallel-git-worktrees | https://github.com/max-sixty/worktrunk | MIT OR Apache-2.0 | Offline worktree status inspection; no Git command |

Each `examples/skills/*.json` manifest remains data-only and bound to an offline exam definition by SHA-256. See the four `skills/*/SKILL.md` documents and `src/imperial_skill/trending_skills.py` for source and negative tests. These contracts add **zero** actual runtime permissions. The exam fixtures only demonstrate hash provenance; they are not independent QA.

Run `python -m unittest discover -s tests -p 'test_*.py' -v` and `python tools/verify_examples.py`. The pinned cross-repository IMPERIAL-Plugins validator checks all eight example manifests; CI must pass before merge.

## Deployment gates

Live OS control, public-site data acquisition, training/inference and Git mutation require separately verified and owner-approved runtime integrations. Review third-party licenses, exact dependencies, target consent and robots/ToS, SSRF/egress restrictions, secret handling and independent QA. Enroll real Owner Ed25519 keys, AI Passport and Guardian Core; issue exact-scope Approval Gateway permits; record ProofGraph and Audit Ledger evidence; implement Owner Kill Switch and rollback. FREE_ONLY remains mandatory.

Canonical federation: Architect → HANTER (AI Command Center) → federated domain orchestrators → professional NCA. VELION is model intelligence (MAX is a mode); ORION is advisory. Enforce Zero Trust, Public/Private Boundary, and CRYPTO IMPERIAL Ecosystem Boundary. There is no monetary authority in these skills.
