# IMPERIAL Enterprise Skill — Firecrawl Extraction

**Skill ID:** `imperial.skill.firecrawl-extraction`  
**Version:** 0.1.0  
**Architect and original integration design:** Alexander Nikolaevich Romaskevich (RomaskevicH), Founder · Owner · CEO · Chief Systems Architect, IMPERIAL Core.  
**Status:** SOURCE-REGISTERED / NOT PRODUCTION ACTIVATED. Third-party tools retain their vendors' licenses, brands and terms.

## Objective

Authorized website and documentation extraction with robots, terms, privacy, and rate limits.

## Installation or connection path

Firecrawl is already installed in the ChatGPT plugin environment. For a separate IMPERIAL Core server connection, provision the official Firecrawl API key via secret manager; use its v2 API/SDK only in a controlled adapter.

This document and its registered manifest do **not** install provider software, provision credentials, authorize a vendor account, run a server agent, or grant live permissions.

## Governed workflow

Accept an approved public URL allowlist; check authorization and robots policy; limit page count, depth, concurrency and output size; extract structured Markdown or JSON with provenance; persist only redacted evidence.

## Boundaries and approvals

Never scrape authenticated or private sources without specific authorization; no crawling arbitrary IPs or internal networks; rate-limit and credit budgets must be checked before each job.

Execution path: Architect → HANTER Command Center → federated orchestrator `analytics-orch` → scoped NCA → Guardian Core + AI Passport + IntentLock → Approval Gateway → isolated tool adapter → independent QA → ProofGraph → Audit Ledger. The Owner Kill Switch, revocation and rollback must be enforced **at runtime**, not represented only in documentation. VELION supplies model routing (MAX is a mode); ORION may advise but cannot authorize. Maintain Zero Trust, Public/Private Boundary and CRYPTO IMPERIAL Ecosystem Boundary. FREE_ONLY until the Owner explicitly approves a funded provider account.

## Source evidence

- Manifest: `examples/skills/firecrawl-extraction.json`
- Synthetic exam (hash-bound): `examples/exams/firecrawl-extraction.json`
- Governance: `docs/FIVE_PROVIDER_SKILLS.md`
- CI validation: `python tools/verify_examples.py` and `python -m unittest discover -s tests -v`

**Important:** Offline reference-match exams and the presence of this skill do not demonstrate service connectivity, licensed use, external independent QA, permission to operate, or successful production E2E. Vendor integration and security testing are separate release gates.
