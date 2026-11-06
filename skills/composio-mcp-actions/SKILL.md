# IMPERIAL Enterprise Skill — Composio MCP Actions

**Skill ID:** `imperial.skill.composio-mcp-actions`  
**Version:** 0.1.0  
**Architect and original integration design:** Alexander Nikolaevich Romaskevich (RomaskevicH), Founder · Owner · CEO · Chief Systems Architect, IMPERIAL Core.  
**Status:** SOURCE-REGISTERED / NOT PRODUCTION ACTIVATED. Third-party tools retain their vendors' licenses, brands and terms.

## Objective

MCP-mediated discovery and execution of explicitly authorized external-service actions without a single global orchestrator.

## Installation or connection path

Composio Connect exposes https://connect.composio.dev/mcp; configure it only on a supported MCP client and authorize individual apps through the vendor OAuth flow. No Composio ChatGPT plugin installation was confirmed.

This document and its registered manifest do **not** install provider software, provision credentials, authorize a vendor account, run a server agent, or grant live permissions.

## Governed workflow

Discover tools by business intent; pin toolkit/version and schema; propose a scoped action; obtain Guardian Core and Approval Gateway decision; execute through a least-privilege service identity; record sanitized result and audit receipt.

## Boundaries and approvals

No autonomous connection of all apps; deny unapproved send, delete, publish, spend, permission changes and cross-tenant access; every write requires a specific, short-lived signed approval and revocable AI Passport.

Execution path: Architect → HANTER Command Center → federated orchestrator `automation-orch` → scoped NCA → Guardian Core + AI Passport + IntentLock → Approval Gateway → isolated tool adapter → independent QA → ProofGraph → Audit Ledger. The Owner Kill Switch, revocation and rollback must be enforced **at runtime**, not represented only in documentation. VELION supplies model routing (MAX is a mode); ORION may advise but cannot authorize. Maintain Zero Trust, Public/Private Boundary and CRYPTO IMPERIAL Ecosystem Boundary. FREE_ONLY until the Owner explicitly approves a funded provider account.

## Source evidence

- Manifest: `examples/skills/composio-mcp-actions.json`
- Synthetic exam (hash-bound): `examples/exams/composio-mcp-actions.json`
- Governance: `docs/FIVE_PROVIDER_SKILLS.md`
- CI validation: `python tools/verify_examples.py` and `python -m unittest discover -s tests -v`

**Important:** Offline reference-match exams and the presence of this skill do not demonstrate service connectivity, licensed use, external independent QA, permission to operate, or successful production E2E. Vendor integration and security testing are separate release gates.
