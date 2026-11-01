# Integration Contracts — HANTER, VELION, IMPERIAL-Plugins

The IMPERIAL-Skill software exposes **data-only adapters**, not credentials or production runtime integrations.

## IMPERIAL-Plugins

The to_plugins_manifest adapter converts a validated Skill into the existing four-field plugin prototype descriptor: id, version, capabilities and description. It never grants a plugin arbitrary code execution.

GitHub Actions independently checks all example descriptors against the **real original IMPERIAL-Plugins Python validator**, pinned at c983d81d1d2f7385bebd416e90909c5ae0d9d1eb. This ensures source-level compatibility against an immutable upstream reference. It does not imply a live server-to-server connection.

## HANTER

make_hanter_intent produces a hashed, tenant/orchestrator/task-bound intent lock carrying an immutable Skill plan digest and input SHA-256. This is an **INTENT_PROPOSAL_ONLY**, not an executed HANTER command. Real dispatch requires the separate authenticated HANTER gateway, AI Passport, Owner Approval and Guardian Core.

## VELION

velion_route_hint supplies a model configuration hint and FAST/BALANCED/MAX mode based on a validated task intent. MAX is one operating mode. A hint does not route or invoke a model and is explicitly marked **actual_model_called=false**.

## Offline demonstration

Run: python tools/demo_federation.py

This demonstrates validation → federated dependency plan → task-intent lock → VELION planning hint → offline reference comparison → local ProofGraph hash → local Audit Ledger. It makes **zero** model/API calls, grants **zero** production execution, and never claims independent professional QA.

## Next cross-service E2E

Only after real Owner Ed25519 enrollment, signed AI Passports, federated HANTER identity, separately authenticated worker, independent QA, actual VELION inference and verified kill switch can a production adapter be proposed. Read [release gates](RELEASE_GATES.md).
