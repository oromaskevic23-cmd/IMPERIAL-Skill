# IMPERIAL Enterprise Skill — Playwright E2E

**Skill ID:** `imperial.skill.playwright-e2e`  
**Version:** 0.1.0  
**Architect and original integration design:** Alexander Nikolaevich Romaskevich (RomaskevicH), Founder · Owner · CEO · Chief Systems Architect, IMPERIAL Core.  
**Status:** SOURCE-REGISTERED / NOT PRODUCTION ACTIVATED. Third-party tools retain their vendors' licenses, brands and terms.

## Objective

Reproducible browser end-to-end checks and screenshots for CONSTRUCTOR AI before an independent release approval.

## Installation or connection path

Install in the target Node project with `npm install -D @playwright/test` and install the browser with `npx playwright install chromium` (CI may also need system dependencies). GitHub Actions should pin dependencies and run on an isolated test site.

This document and its registered manifest do **not** install provider software, provision credentials, authorize a vendor account, run a server agent, or grant live permissions.

## Governed workflow

Define deterministic test fixtures, web-first assertions, sanitized trace output, and negative tests; run Chromium smoke tests in a nonproduction sandbox; attach test report and SHA-256 evidence to ProofGraph.

## Boundaries and approvals

Never execute arbitrary LLM-generated test scripts on production infrastructure; never submit real purchases, credentials or messages; prohibit secrets in traces; prevent external-network access except allowlisted test origins.

Execution path: Architect → HANTER Command Center → federated orchestrator `engineering-orch` → scoped NCA → Guardian Core + AI Passport + IntentLock → Approval Gateway → isolated tool adapter → independent QA → ProofGraph → Audit Ledger. The Owner Kill Switch, revocation and rollback must be enforced **at runtime**, not represented only in documentation. VELION supplies model routing (MAX is a mode); ORION may advise but cannot authorize. Maintain Zero Trust, Public/Private Boundary and CRYPTO IMPERIAL Ecosystem Boundary. FREE_ONLY until the Owner explicitly approves a funded provider account.

## Source evidence

- Manifest: `examples/skills/playwright-e2e.json`
- Synthetic exam (hash-bound): `examples/exams/playwright-e2e.json`
- Governance: `docs/FIVE_PROVIDER_SKILLS.md`
- CI validation: `python tools/verify_examples.py` and `python -m unittest discover -s tests -v`

**Important:** Offline reference-match exams and the presence of this skill do not demonstrate service connectivity, licensed use, external independent QA, permission to operate, or successful production E2E. Vendor integration and security testing are separate release gates.
