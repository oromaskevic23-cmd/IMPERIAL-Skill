# Enterprise Skills Standard v0.1

A Skill is a strict, data-only capability descriptor with exact-version dependencies and a canonical manifest SHA-256.

## Fields and meaning

The manifest binds schema, skill ID, semantic version, tenant ID, federated orchestrator ID, Runtime Domain, description, explicit allowed capabilities, pinned dependencies, named input/output fields, examination definition SHA-256, maximum input/output byte counts, risk tier, obligatory Owner approval and independent QA requirements.

A descriptor must always declare data_only=true, owner_approval_required=true and independent_qa_required=true. It must declare external_effects=false, production_authorized=false and spending_usd=0.

Supported non-executing capabilities are compatible with IMPERIAL-Plugins: read:public, simulate:task, route:internal. Neither repository constitutes authority to execute tools.

An exam_sha256 must match an actually supplied canonical examiner definition, not a fictitious success marker. In the example graph, code-draft v0.1.0 depends on code-review v0.1.0. Both belong to the same engineering-orch and CODE_ENGINEERING Runtime Domain.

VELION can independently plan models, but MAX is a mode and a Skill does not acquire autonomous model access by manifest validation. Do not count a registered or sample Skill as a trained NCA.
