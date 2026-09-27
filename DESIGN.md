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

## Detailed structure and views

### Execution and reporting view

```text
projects/<name>/checklist.yaml
  -> scripts/_checklist_lib.py (schema + repo-root resolution)
  -> scripts/run_checklist.py (bounded subprocess execution)
  -> raw target result
  -> verifier judgment (PASS / DETECTED / MISSED / INVALID)
  -> sanitized project dashboard + root index.html
```

- `projects/*/checklist.yaml` is the registry and executable contract; generated `dashboard.html` files are snapshots of the latest run.
- `scripts/` owns loading, execution, sanitization, report generation, and public-path validation.
- `tests/` protects path confinement, atomic report replacement, expected-failure semantics, inventory, and privacy rejection.
- `RELEASE_READINESS_STANDARD.md`, `LLM_QA_STANDARD.md`, and `SECURITY_NETWORK_QA_STANDARD.md` define review policy; they do not create executable evidence until a checklist references a real command.

### Trust and failure view

Check commands run inside each registered repository root. Output is untrusted and sanitized before publication. A target failure can be verifier success when failure was expected; an unrelated crash is INVALID. Reports are replaced atomically only after validation so a failed run preserves the previous public artifact.

## Key decisions and tradeoffs

- Keep raw exit status, verifier verdict, and semantic presentation separate.
- Execute only explicit registered commands; this avoids invented checks but requires checklist maintenance.
- Generate static dashboards for portability, accepting that they represent the most recent run rather than live state.

## Verification and human review

Run `python -m pytest -p no:cacheprovider` and the registered project checklists. Release, privacy, legal, accessibility, and subjective quality decisions remain human-review HOLD conditions.

## Evidence basis and limits

The design-description structure is informed by [IEEE 1016-2009](https://standards.ieee.org/ieee/1016/4502/), stakeholder concerns and scenarios from [Kruchten](https://www.cs.ubc.ca/~gregor/teaching/papers/4%2B1view-architecture.pdf), modular change boundaries from [Parnas (1972)](https://doi.org/10.1145/361598.361623), product-quality objectives from [ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html), and secure-development integration from [NIST SSDF 1.1](https://doi.org/10.6028/NIST.SP.800-218). Dashboard PASS is evidence for registered checks, not certification or release approval.

The choice of detailed views is also guided by [ISO/IEC/IEEE 42010:2022](https://www.iso.org/standard/74393.html), whose public abstract specifies architecture descriptions, viewpoints, and model kinds, and the [SEI Views and Beyond approach](https://www.sei.cmu.edu/library/views-and-beyond-the-sei-approach-for-architecture-documentation/), which organizes documentation around views selected for stakeholder use. Only views supported by current repository evidence are included; omitted views are not implied.
