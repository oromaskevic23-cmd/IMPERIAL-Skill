# IMPERIAL Enterprise Skill — PostHog Analytics

**Skill ID:** `imperial.skill.posthog-analytics`  
**Version:** 0.1.0  
**Architect and original integration design:** Alexander Nikolaevich Romaskevich (RomaskevicH), Founder · Owner · CEO · Chief Systems Architect, IMPERIAL Core.  
**Status:** SOURCE-REGISTERED / NOT PRODUCTION ACTIVATED. Third-party tools retain their vendors' licenses, brands and terms.

## Objective

Privacy-controlled product analytics, conversion metrics and controlled error diagnostics for CONSTRUCTOR AI and IMPERIAL Core.

## Installation or connection path

PostHog is already installed as a ChatGPT plugin. Product instrumentation is separate: use `npm install --save posthog-js` only in the target frontend, and configure the correct project token and ingestion host through environment management.

This document and its registered manifest do **not** install provider software, provision credentials, authorize a vendor account, run a server agent, or grant live permissions.

## Governed workflow

Specify a minimal event taxonomy and baseline; review privacy settings, opt-in/consent and event payloads; analyze aggregated funnel, retention and errors; return a documented decision, not raw user identity.

## Boundaries and approvals

Do not capture secrets, wallet keys, request bodies, private code or sensitive user fields; default to no session replay and disable autocapture until privacy review; no unapproved flag flips or data exports.

Execution path: Architect → HANTER Command Center → federated orchestrator `analytics-orch` → scoped NCA → Guardian Core + AI Passport + IntentLock → Approval Gateway → isolated tool adapter → independent QA → ProofGraph → Audit Ledger. The Owner Kill Switch, revocation and rollback must be enforced **at runtime**, not represented only in documentation. VELION supplies model routing (MAX is a mode); ORION may advise but cannot authorize. Maintain Zero Trust, Public/Private Boundary and CRYPTO IMPERIAL Ecosystem Boundary. FREE_ONLY until the Owner explicitly approves a funded provider account.

## Source evidence

- Manifest: `examples/skills/posthog-analytics.json`
- Synthetic exam (hash-bound): `examples/exams/posthog-analytics.json`
- Governance: `docs/FIVE_PROVIDER_SKILLS.md`
- CI validation: `python tools/verify_examples.py` and `python -m unittest discover -s tests -v`

**Important:** Offline reference-match exams and the presence of this skill do not demonstrate service connectivity, licensed use, external independent QA, permission to operate, or successful production E2E. Vendor integration and security testing are separate release gates.
