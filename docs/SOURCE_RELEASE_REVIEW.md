# Signed Enterprise Skill Source Review

**Owner / architecture authority:** Alexander Nikolaevich Romaskevich (RomaskevicH).

## Implemented in the public source

The source-candidate command checks that the selected Skill manifest is exactly registered
with a matching precommitted offline exam definition and fully resolved pinned
dependency DAG. SHA-256 binds the manifest, exam, plan and whole registry snapshot.

An optional Ed25519 signed review receipt is checked against a separately pinned
reviewer's public key. It has a five-minute maximum validity, strict fields,
mandatory fail-closed revocation callback, and SQLite atomic anti-replay records.

Source review is not professional competence, independent QA, an Owner Approval
Gateway signature or a production-release decision. Those flags remain false.

## Repeatable local verification

Run:

    python -m unittest discover -s tests -v
    imperial-skill source-candidate --directory examples/skills --manifest examples/skills/code-review.json --exam examples/exams/code-review.json

## Remaining authority boundaries

Actual Owner key enrollment, trusted worker and issuer identity, authenticated
execution sandbox, true held-out professional exam, separate QA, external evidence
and Owner Kill Switch remain required before deployment. No private key or
production service credentials are stored in this repository.

FREE_ONLY. Zero Trust. Public/Private and CRYPTO IMPERIAL Ecosystem Boundaries.
IMPERIUM remains a long-term architectural digital currency intended for AI agents
worldwide, with no claim of actual worldwide use or exchange status.
