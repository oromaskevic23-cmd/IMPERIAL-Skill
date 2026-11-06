# Five Governed Provider Skills — Research, Extraction, Analytics, E2E, MCP

**Owner and architectural authority:** Alexander Nikolaevich Romaskevich (RomaskevicH)  
**Programme:** IMPERIAL Core / Enterprise Skills  
**Prepared:** 2026-11-06  
**Status:** Source-integrated only; no production deployment, billing, vendor authentication or independent QA claims.

## Provider integration inventory

| Skill | Provider capability | ChatGPT plugin state checked 2026-11-06 | IMPERIAL Core server activation |
| --- | --- | --- | --- |
| [Perplexity](../skills/perplexity-research/SKILL.md) | Grounded search and research, official MCP / API | No installable plugin found in ChatGPT plugin search | NOT CONNECTED; credential and allowlisted research adapter required |
| [Firecrawl](../skills/firecrawl-extraction/SKILL.md) | Website/document extraction | Installed in ChatGPT | NOT CONNECTED to IMPERIAL server worker |
| [PostHog](../skills/posthog-analytics/SKILL.md) | Product analytics and error diagnostics | Installed in ChatGPT | Instrumentation and account validation not established |
| [Playwright](../skills/playwright-e2e/SKILL.md) | Automated browser E2E | Not a ChatGPT plugin; Node test dependency | NOT INSTALLED in CONSTRUCTOR AI runtime by this change |
| [Composio](../skills/composio-mcp-actions/SKILL.md) | Authenticated third-party tools through MCP | No installable plugin found in ChatGPT plugin search | NOT CONNECTED; client support, OAuth and app scopes required |

Availability is an observation from the ChatGPT plugin search at the stated date, not a statement about all vendors' distribution channels. All five Enterprise Skill contracts in this repository are offline, and no external execution is authorized.

## Correct architectural placement

```text
ARCHITECT / OWNER
      |
    HANTER  (Command Center; does NOT execute all workflows)
      |
      +-- analytics-orch --> Perplexity / Firecrawl / PostHog (research/analysis)
      +-- engineering-orch --> Playwright (isolated CONSTRUCTOR AI E2E)
      +-- automation-orch --> Composio MCP (app actions, gated)
      |
  Scoped Nano Core Agents + Enterprise Skills
      |
  IntentLock / AI Passport / Guardian Core
      |
  Approval Gateway -> short-lived action permit -> scoped tool adapter
      |
  Independent QA -> ProofGraph -> Audit Ledger
      |
  Revocation / rollback / Owner Kill Switch
```

VELION routes appropriate model workloads; MAX is a VELION mode. ORION is advisory. ASTRA remains one of many orchestrators; no global single-executor architecture is introduced.

## Provider-specific setup — controlled and optional

**Perplexity:** Official remote MCP address is `https://api.perplexity.ai/mcp`; supply the approved Bearer token through a secrets manager. For a Python-side integration, the upstream client is `perplexityai`. Research API usage is not assumed free. Preserve original URLs and verify citations.

**Firecrawl:** The ChatGPT app is already installed. A separate server-side adapter needs its own authenticated vendor session and limited credits. Respect robots and contracts, allowlist public domains and enforce SSRF and DNS-rebinding controls in a real outbound egress proxy. Account-wide crawls are not pre-approved.

**PostHog:** ChatGPT plugin availability does not instrument a product. Only introduce `posthog-js` into a target application after privacy and data minimization review. Explicitly disable autocapture and session recording by default until consent, jurisdiction, processing basis and retention are reviewed. Never send AI prompts with secrets or personal data.

**Playwright:** In a specifically selected Node application, the upstream instructions use `npm install -D @playwright/test` then `npx playwright install chromium`. CI should run an isolated staged app with one worker, sanitized screenshots/traces and no transactions. Check browser test fixtures and network allowlists; do not automate real user accounts without Owner-approved test credentials.

**Composio:** Upstream MCP Connect is `https://connect.composio.dev/mcp`; OAuth is per app. For a future server integration prefer a restricted per-user session and a tool allowlist over blanket access to all upstream services. Credential refresh, revocation, permission changes, app charges and write actions need explicit operational policy. Never reuse external write authority across tenants.

## Admission and cost policy

1. **FREE_ONLY** means no third-party trial activation, API bill or subscription is inferred from repository presence; non-free calls require explicit Owner budget approval.
2. The runtime must **deny by default** when provider identity, tenant, purpose, URL/host, secret scope, resource limit or signed permit is missing.
3. Prior to each external action validate the tenant-scoped AI Passport, IntentLock, authenticated federated route, Guardian Core policy, short-lived Approval Gateway permit, idempotency key, budget and public/private classification.
4. On requests to send, delete, purchase, publish, change permissions, ingest private information or call unknown tools, obtain purpose-specific Owner authorization. A natural-language instruction is not a permit.
5. Enforce sandbox network egress allowlists, credential vaulting, provider-specific quotas, bounded concurrency and timeouts. No secrets in Audit Ledger.
6. Store an append-only attempt and result receipt to Audit Ledger; attach sanitized execution artifact hashes to ProofGraph; use independent QA and rollback before production release.
7. HANTER Owner Kill Switch must revoke new dispatches **and** terminate running processes through the actual worker, not just change a DB flag.

## Release checklist (not yet satisfied)

- [x] Five original SKILL.md specifications.
- [x] Five closed-schema data-only manifests.
- [x] Five SHA-256-bound synthetic exam definitions.
- [x] Negative policy tests authored for CI.
- [ ] Green GitHub Actions run for this exact commit (verify before marking).
- [ ] Owner-enrolled credential and signing roots for each worker.
- [ ] Evidence of real provider authentication and budget controls.
- [ ] Hardened adapter, outbound egress, secrets and privacy review.
- [ ] End-to-end independent QA, authorization, revocation, rollback and kill-switch drill.
- [ ] Production deployment with health probes and measured results.

These files provide the reproducible **source and governance installation**, not a running tool service.

## Verification commands

```bash
python -m pip install -e .
python -m unittest discover -s tests -p 'test_five_provider_skills.py' -v
python tools/verify_examples.py
```

## Official upstream references

- [Perplexity official MCP implementation](https://github.com/perplexityai/modelcontextprotocol)
- [Perplexity official Python SDK](https://github.com/perplexityai/perplexity-py)
- [Firecrawl upstream v2 docs](https://docs.firecrawl.dev/)
- [PostHog JS documentation](https://posthog.com/docs/libraries/js)
- [Playwright official installation and CI](https://playwright.dev/docs/intro)
- [Composio official Connect](https://docs.composio.dev/docs/composio-connect)

Original IMPERIAL Core integration design is authored under the project owner's attribution. No ownership, trademark right, exclusive license or endorsement is claimed over the third-party providers.
