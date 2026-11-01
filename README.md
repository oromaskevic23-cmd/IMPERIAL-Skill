# IMPERIAL Skill

**Enterprise-grade, federated AI Skills architecture for IMPERIAL Core**

[![Enterprise Skills CI](https://github.com/oromaskevic23-cmd/IMPERIAL-Skill/actions/workflows/enterprise-skill-ci.yml/badge.svg)](https://github.com/oromaskevic23-cmd/IMPERIAL-Skill/actions/workflows/enterprise-skill-ci.yml)

**Founder · Owner · CEO · Chief Systems Architect:** Alexander Nikolaevich Romaskevich  
**Signature:** RomaskevicH  
**Engineering philosophy:** Architecture → Implementation → Evidence

IMPERIAL Skill is a modular, versioned framework for declaring, validating, examining and tracing professional Enterprise Skills used by HANTER, VELION, federated orchestrators and Nano Core Agents. Designed for organizational boundaries, independent quality assurance, Zero Trust and auditable evidence.

## The federated architecture

~~~text
             ARCHITECT / OWNER
                    |
              HANTER Command Center
                    |
           Federated Orchestrators
          /          |           \
  engineering-orch security-orch ... domain orchestrators
        |            |                      |
     Nano Core Agents and scoped Runtime Domains
                    |
  Enterprise Skills → Guardian Core → AI Passport / Approval Gateway
                    |
  VELION model route → independent QA → ProofGraph → Audit Ledger
                    |
      Owner Kill Switch / revocation / rollback
~~~

HANTER is the command center, **not a single global execution orchestrator**. ASTRA is one of the orchestrators. VELION is the model fabric and **MAX is a mode**. ORION is advisory collective intelligence.

**Source milestone:** v0.2.0 — source-level engineering framework, not a published
PyPI release or a production NCA platform. CI validates wheel installation and
the safety of both Python 3.11 and 3.12 execution.

## Current engineered modules

| Module | Real functionality | Explicit limit |
| --- | --- | --- |
| **Manifest Kernel** | Strict, closed-schema, data-only Skill contract with SHA-256 | Does not execute code |
| **Enterprise Registry** | Exact-version Skill DAG with tenant/orchestrator/domain isolation | Plan only |
| **Owner + AI Passport** | Separate Ed25519 trust roots, scope/TTL checks and atomic anti-replay | No real Owner keys enrolled here |
| **Enterprise Examination** | Fixed, hash-precommitted offline case grading | Not independent professional certification |
| **ProofGraph** | Hash-bind artifact and exam evidence; optional pinned QA-signature check | No external immutable anchor |
| **Audit Ledger** | Transactional SQLite hash chain and tamper detection | Local only, DB owner can override |
| **Signed Source Review** | Exact Skill, exam and DAG fingerprints; Ed25519 reviewer signature, 5-minute TTL, replay defense | Source review is not Owner approval or an NCA certificate |
| **Command-line tools** | Validate, resolve DAG, grade offline cases and audit inspection | No network or model invocation |

## Quick start

Requires Python 3.11+.

~~~shell
python -m pip install -e .
python -m unittest discover -s tests -v
python tools/verify_examples.py

imperial-skill validate examples/skills/code-review.json
imperial-skill plan --directory examples/skills \
  --tenant imperial-internal --orchestrator engineering-orch \
  --domain CODE_ENGINEERING \
  --skill-id imperial.skill.code-draft --version 0.1.0
imperial-skill exam-grade \
  examples/exams/code-review.json \
  examples/exams/code-review-responses.json
~~~

The sample engineering Skill graph contains **code-review → code-draft** with pinned versions, precommitted exam definitions and strict tenant/domain routing. Even when offline tests pass, the CLI returns **execution_authorized=false** or **independent_qa_verified=false**.

## Production release policy

**This repository is a working local software framework, not a deployed agent fleet.** It does not claim 100 or 1700 NCA are online. No worker has been granted execution authority by these manifests. No model is called in the Skill tests. A successful CI run establishes test success, not production readiness.

Before activating any professional NCA: verified Owner Ed25519 enrollment, independently issued revocable AI Passport, authenticated worker and federated route, scoped Approval Gateway permit, real sandbox execution with appropriate LLM, separate professional QA, ProofGraph evidence, Audit Ledger and process-level kill switch. Every NCA is certified individually.

**FREE_ONLY · Zero Trust · Public/Private Boundary · CRYPTO IMPERIAL Ecosystem Boundary.**

IMPERIUM is a **long-term architectural digital currency envisioned for AI agents worldwide**, not a claim of current global usage, exchange trading or market status.

## Signed source-review and release candidate

The source-review module binds a validated Enterprise Skill, pinned dependency graph,
precommitted exam definition and registry snapshot into a SHA-256 candidate. Optional
Ed25519 reviewer receipts use a separately pinned public key and atomic local nonce
ledger; verification does **not** issue an AI Passport or certify an NCA.

~~~shell
imperial-skill source-candidate \
  --directory examples/skills \
  --manifest examples/skills/code-review.json \
  --exam examples/exams/code-review.json
~~~

The output is explicitly SOURCE_REVIEW_REQUIRED, with independent QA, execution and
production permissions all false. See [signed source-review design](docs/SOURCE_RELEASE_REVIEW.md).

## Federated integration adapters

Four inspectable example Skills now cover code review, code drafting, defensive security and data quality across separate Runtime Domains and tenant/orchestrator assignments. The system also includes **data-only** compatibility adapters for HANTER, VELION and IMPERIAL-Plugins. An independent GitHub Actions job checks our descriptors against the **actual pinned IMPERIAL-Plugins validator**, not just a mock.

~~~shell
python tools/demo_federation.py
~~~

This is a local skill-planning demonstration only. It does not invoke a real LLM, deploy workers, accept wallets or bypass Owner Approval. See [integrations](docs/INTEGRATIONS.md).

## Documentation

- [Enterprise architecture](docs/ARCHITECTURE.md)
- [Inter-repository integration contracts](docs/INTEGRATIONS.md)
- [Threat model](docs/THREAT_MODEL.md)
- [Skill standard](docs/SKILL_STANDARD.md)
- [Production release gates](docs/RELEASE_GATES.md)
- [Security policy](SECURITY.md)
- [Source license notice](LICENSE.md)

## Ownership and third parties

Original IMPERIAL Core architecture and original project work are attributed to Alexander Nikolaevich Romaskevich (RomaskevicH). Third-party software and model weights retain their own terms; this project does not claim to own or be endorsed by their vendors. See [LICENSE.md](LICENSE.md). GitHub documentation and code are in English.
