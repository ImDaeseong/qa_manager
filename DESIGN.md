# qa_manager Design

Updated: 2026-09-27

## Purpose

Run real checks registered by multiple local repositories and present current verifier outcomes as static dashboards.

## Stakeholders, concerns, and scenarios

- Project maintainer: see which executable checks currently pass or fail.
- Reviewer/release owner: distinguish verification evidence from release approval.
- Dashboard reader: understand expected-failure semantics without confusing target failure with verifier failure.
- Representative scenario: load a checklist, resolve its project root, run each check with sanitized output, classify the result, and regenerate static reports.

## Boundaries

- `qa_manager` executes registered checks but does not repair target repositories.
- Generated dashboards contain check metadata and sanitized diagnostics, not secrets or private source content.
- Verifier verdict, target exit status, and expected-failure assessment are separate concepts.
- Automated PASS does not grant commercial-release approval.

## Main components

- `projects/*/checklist.yaml`: requirement, development item, and executable test definitions.
- `scripts/_checklist_lib.py`: checklist loading, path resolution, and status semantics.
- `scripts/run_checklist.py`: text execution report.
- Dashboard generators and generated `index.html`/`dashboard.html` files.

## Key decisions and tradeoffs

- Keep raw exit status, verifier verdict, and semantic presentation separate.
- Execute only explicit registered commands; this avoids invented checks but requires checklist maintenance.
- Generate static dashboards for portability, accepting that they represent the most recent run rather than live state.

## Verification and human review

Run `python -m pytest -p no:cacheprovider` and the registered project checklists. Release, privacy, legal, accessibility, and subjective quality decisions remain human-review HOLD conditions.

## Evidence basis and limits

The design-description structure is informed by [IEEE 1016-2009](https://standards.ieee.org/ieee/1016/4502/), stakeholder concerns and scenarios from [Kruchten](https://www.cs.ubc.ca/~gregor/teaching/papers/4%2B1view-architecture.pdf), modular change boundaries from [Parnas (1972)](https://doi.org/10.1145/361598.361623), product-quality objectives from [ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html), and secure-development integration from [NIST SSDF 1.1](https://doi.org/10.6028/NIST.SP.800-218). Dashboard PASS is evidence for registered checks, not certification or release approval.
