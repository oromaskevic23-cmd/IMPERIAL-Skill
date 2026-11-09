# IMPERIAL Enterprise Skill — 100 Subagents

**Skill ID:** imperial.skill.subagents-100
**Version:** 0.1.0 (source-only executable planning reference; no deployed agents).
**Original architect:** Alexander Nikolaevich Romaskevich (RomaskevicH), Founder, Owner, CEO of IMPERIAL Core.

## Goal

Prepare exactly **100 symbolic sub-NCA assignments**, divided into **10 professional squads of 10**, each with a deterministic task SHA-256. Bounded scheduling plans use at most 10 parallel symbolic slots. This Skill belongs to the future HANTER → federated orchestrators → NCA runtime. It is not a single global orchestrator, 100 running agents, or a production release.

## Artifacts

- Enterprise Skill contract: examples/skills/subagents-100.json
- Hash-precommitted synthetic exam: examples/exams/subagents-100.json
- Original pure-Python planning adapter: src/imperial_skill/subagents_100.py
- Adversarial tests: tests/test_subagents_100.py
- Read-only demonstration: tools/demo_subagents_100.py
- Governance and rollout controls: docs/SUBAGENTS_100.md

## Safety and operations

Architect → HANTER Command Center → scoped federated orchestrators → NCA/sub-NCA. Every real worker requires separate AI Passport, Enterprise Skills, Guardian Core, Approval Gateway, independent QA, ProofGraph, Audit Ledger, IntentLock, rollback, revocation, Zero Trust and Owner Kill Switch. Keep Public/Private Boundary and CRYPTO IMPERIAL Ecosystem Boundary. VELION is the model fabric; MAX is a mode. ORION supplies collective intelligence advice, not authority.

All symbolic identities remain PLANNED_ONLY. Unknown scopes, count other than exactly 100, parallelism above 10, spending, external effects and disabled Owner Kill Switch fail closed. Synthetic SHA-256 receipts cannot prove independent QA, certification or execution authority. No secrets, models, Git mutations, network access, payments, cloud workers or actual agent processes are created.

## Verify

After installing the existing repository dependencies:

    python -m unittest discover -s tests -p 'test_subagents_100.py' -v
    python tools/demo_subagents_100.py
    python tools/verify_examples.py

Real activation requires separate Owner Ed25519 enrollment, individually revocable AI Passport, isolated workers, authenticated HANTER/federation dispatch and independent QA. No production activation is claimed.
