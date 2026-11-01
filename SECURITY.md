# Security Policy — IMPERIAL Skill

This repository contains **data-only Enterprise Skills contracts, non-executing plans and offline test helpers**. It does not grant authority to run NCA, access web services or spend funds.

## Non-negotiable controls

- No manifest, passing unit test, offline exam match or local hash may authorize a production action.
- Never commit Owner Ed25519 private keys, HANTER delegated issuer keys, service-role credentials, worker JWTs or CRYPTO IMPERIAL wallet secrets.
- A real runtime must independently verify enrolled Owner and issuer public keys, AI Passport, worker identity, expiration, revocation, Guardian Core, Approval Gateway and Owner Kill Switch.
- Reject cross-tenant, cross-orchestrator, cross-Runtime Domain access and silent dependency upgrades.
- Never import or execute untrusted Skill content or generated code based on a manifest.
- All capabilities are limited to read:public, simulate:task and route:internal; real external operations are not supported.
- This project is **FREE_ONLY**. No funding, transfers, token exchange or outside-platform employment claims.

## Vulnerability reporting

Use a private GitHub Security Advisory; do not publish exploit payloads, credentials or sensitive data.

## Required production proof

Protected Owner key custody, real signed permit E2E, independently revocable AI Passport, sandboxed worker execution, distinct role-appropriate independent QA and its signature, time-bounded task identity, externally anchored audit evidence where appropriate, true process-level kill switch and explicit separate production release.

**Architecture → Implementation → Evidence.**
