# DesignDocs Evidence Review

Review date: 2026-10-05

Scope: the root DESIGN.md files of the 14 projects registered in qa_manager.

## Claims tested

| Claim | Evidence | Result |
|---|---|---|
| A design description should record and communicate design information to relevant stakeholders. | [IEEE 1016-2009 official page](https://standards.ieee.org/ieee/1016/4502/) says an SDD records design information and communicates it to key design stakeholders. | Supported |
| One structural list is insufficient for all audiences; stakeholder concerns should be addressed through relevant views and scenarios. | [Kruchten, 1995](https://www.cs.ubc.ca/~gregor/teaching/papers/4%2B1view-architecture.pdf) presents multiple concurrent views for different stakeholders and uses scenarios to connect them. [SEI, 2009](https://www.sei.cmu.edu/library/a-structured-approach-for-reviewing-architecture-documentation/) reviews architecture documentation from the stakeholder perspective. | Supported |
| Module boundaries should isolate likely changes rather than merely follow execution steps. | [Parnas, 1972](https://doi.org/10.1145/361598.361623) compares decompositions and ties modularization effectiveness to the criterion used to divide the system, emphasizing flexibility and comprehensibility. The DOI landing page blocked automated access, so the passage was cross-checked against a [Carnegie Mellon archive record](https://doi.org/10.1184/r1/6607958) and an accessible university-hosted reprint. | Supported, with access limitation disclosed |
| Quality objectives need to be explicit enough to specify, measure, and evaluate. | [ISO/IEC 25010:2023 official abstract](https://www.iso.org/standard/78176.html) defines nine product-quality characteristics and describes their use for requirements, design objectives, testing, and acceptance criteria. | Supported, but the complete standard is paywalled |
| Architecture detail should be selected by stakeholder concerns rather than imposed as one universal diagram set. | [ISO/IEC/IEEE 42010:2022 official page](https://www.iso.org/standard/74393.html) publicly confirms requirements for architecture descriptions, viewpoints, and model kinds. [SEI Views and Beyond](https://www.sei.cmu.edu/library/views-and-beyond-the-sei-approach-for-architecture-documentation/) makes views the organizing principle, while the [SEI stakeholder-centered review method](https://www.sei.cmu.edu/library/a-structured-approach-for-reviewing-architecture-documentation/) checks whether documentation lets stakeholders perform their intended work. | Supported |
| Security should be integrated into the lifecycle and tied to design risk, not appended only at release. | [NIST SP 800-218 SSDF 1.1](https://doi.org/10.6028/NIST.SP.800-218) recommends integrating secure-development practices into each SDLC implementation. | Supported |

## Findings and changes

The first draft already documented purpose, boundaries, components, verification, and human-review HOLD conditions. It did not explicitly map stakeholders to concerns, identify a representative scenario, state key decisions and tradeoffs, or identify its evidence basis.

All 14 DesignDocs now include:

1. purpose and system boundary;
2. named stakeholders and their concerns;
3. a representative end-to-end scenario;
4. major components or development view;
5. key decisions and tradeoffs;
6. verification plus human-review limits;
7. an evidence section that avoids claiming formal standards conformance;
8. a project-specific detailed structure section covering only the module, execution, data/trust, or allocation views justified by that repository.

## Counterevidence and limits

- ISO/IEC/IEEE 42010 and SEI Views and Beyond require relevance to stakeholder concerns; they do not justify forcing identical detail on every repository. Complex runtimes therefore receive several views, while static or record-oriented repositories receive the smaller flow and boundary views they actually need.
- Kruchten's 4+1 model is a method for software-intensive architecture description, not a requirement that every small repository contain five diagrams. The documents therefore use the principle of multiple relevant views and a scenario, not a ceremonial five-view template.
- IEEE 1016-2009 is marked inactive-reserved and its full text requires purchase. Only the official public description was used; no full-conformance claim is made.
- The ACM DOI for Parnas's paper returned an automated-access error. The publication identity and relevant passage were checked through the Carnegie Mellon archive and university-hosted reprints; the DOI remains the canonical citation.
- ISO/IEC 25010 supplies a quality model, not project-specific acceptance thresholds. The existing executable checks and human HOLD conditions remain the source of local acceptance criteria.
- NIST SSDF is a high-level secure-development framework. Mentioning it does not prove that a project has implemented every SSDF practice.
- The source set supports the document structure. It does not independently prove that every project-specific architecture statement is complete; that still requires maintainers and users familiar with the runtime.

## Conclusion

The revised documents are not identical: they share a reviewable core schema, while every detailed section is tied to project-specific files, flows, and trust boundaries. The qa_manager regression test now requires a unique detailed section and a project-specific marker for every registered project. The documents are aligned with the inspected evidence at the level appropriate for repository DesignDocs. They are evidence-informed architecture summaries, not IEEE, ISO, NIST, or SEI certifications.
