# Threat Model — IMPERIAL Skill v0.1

## Protected assets

Owner authority and original project code, scope-limited AI Passports, skill definitions, federation routes, independent examiner keys, generated artifacts, audit history and payment boundaries.

| Threat | Present mitigation | Still required |
| --- | --- | --- |
| Arbitrary code execution via Skill | Closed data-only schema; no executable entrypoint | Production sandbox and tool policy |
| Tenant/orchestrator pivot | Per-node federated DAG boundary checks | Shared server tenant ACL |
| Skill substitution / supply-chain | Exact semver + manifest SHA-256 | Verified release signatures and version storage |
| Owner/issuer impersonation | Distinct pinned Ed25519 trust roots | Owner key enrollment and rotation |
| Signature replay | 5-minute TTL + SQLite atomic JTI/nonce reservation | Distributed database authority and revocation |
| QA forgery | Offline exam explicitly not independent; pinned QA Ed25519 receipt verifier | External examiner custody and case independence |
| Audit tampering | Chained SHA-256 + ordinary update/delete triggers | External append-only anchor |
| Hidden financial effects | 0 spend / no effects / narrow capability allowlist | Enforced runtime egress/wallet boundary |
| Model output misuse | No model execution in this repository | Separate non-networked independent QA |
| Resource exhaustion | Bounded file size, DAG size, exam case size | Runtime budgets and quotas |

No successful unit test or data-integrity hash constitutes professional certification, production entitlement, legal compliance or commercial success.
