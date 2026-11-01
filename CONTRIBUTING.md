# Contribution and Review Policy

IMPERIAL-Skill is maintained under the final architectural authority of **Alexander Nikolaevich Romaskevich**, Founder, Owner, CEO and Chief Systems Architect of IMPERIAL Core.

Code, comments, commit messages, Skills and GitHub documentation must be in English. Preserve canonical component names and the **federated Multi-Orchestrator Architecture**.

Contributions should include a strict versioned manifest, independently reviewed dependency graph, bounded input/output contract, examiner definition and SHA-256, security impact, independent adversarial tests, author attribution and verifiable evidence.

Do not add arbitrary executable plugin entrypoints, external financial actions, new privileged dependencies or autonomous release routes without separately scoped Owner approval. Third-party contributors retain the applicable rights in their contributions unless a separate agreement provides otherwise.

Tests:

~~~shell
python -m pip install -e .
python -m unittest discover -s tests -v
python tools/verify_examples.py
~~~
