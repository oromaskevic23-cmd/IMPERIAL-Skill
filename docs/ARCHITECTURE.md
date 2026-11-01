# IMPERIAL Skill — Enterprise Architecture v0.1

## Federated organizational model

~~~text
Alexander Nikolaevich Romaskevich — Final Architectural Authority
                         |
                   HANTER Command Center
                         |
       +-----------------+-------------------+
       |                 |                   |
 engineering-orch   security-orch      further federated
       |                 |                orchestrators
 CODE_ENGINEERING  SECURITY_DEFENSIVE      Runtime Domains
       |                 |                   |
      NCA               NCA                 NCA
       +-----------------+-------------------+
                         |
             Enterprise Skill Registry
                         |
        Guardian Core / Owner Approval / AI Passport
                         |
                 VELION model routing
                         |
          Independent QA / ProofGraph / Audit Ledger
                         |
                    Owner Kill Switch
~~~

HANTER coordinates commands, but the system does **not** have one global execution orchestrator. ASTRA is a specialized orchestrator, ORION supplies collective intelligence, and VELION provides a modular model fabric; MAX is one operating mode.

## Executable boundary

A Skill manifest is only data: strict schema, immutable version, pinned skill dependency graph, tenant, domain, orchestrator, zero budget and signed-exam expectation. The current registry resolves a **PLAN_ONLY** dependency sequence and cannot run arbitrary code, web tasks, OS processes, tools or LLM calls.

Cryptographic admission verifies distinct Owner and delegated issuer Ed25519 keys, task scope, 5-minute TTL, replay and revocation. Only an externally enrolled trust-root and real admission service can provide genuine Owner authorization. The current local verifier uses test keys in CI; no key is generated or stored for the Owner here.

Offline exam results are reference matches, not independent professional QA. ProofGraph binds hashes, but external QA receipts require a separately trusted examiner identity. Local SQLite Audit Ledger is tamper-evident against ordinary changes, not immutable against database administrators.

## Boundary commitments

Guardian Core, Approval Gateway, AI Passport, Enterprise Skills, Audit Ledger, ProofGraph, IntentLock, Zero Trust, Owner Kill Switch, Public/Private Boundary and CRYPTO IMPERIAL Ecosystem Boundary remain mandatory.

IMPERIUM is the long-term **architectural digital currency intended for AI agents worldwide**, not an assertion of present global usage, listing or price.

**Architecture → Implementation → Evidence.**
