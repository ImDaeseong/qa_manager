"""Verify that qa_manager's architecture and LLM assurance documents exist."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
required = {
    "qa-manager-architecture.html": ("보안 게이트", "LLM 신뢰성", "checklist.yaml"),
    "LLM_QA_STANDARD.md": ("원자 주장", "프롬프트 주입", "citation_correctness"),
    "SECURITY_NETWORK_QA_STANDARD.md": ("CWE-798", "CWE-78", "qa:allow"),
}

missing: list[str] = []
for name, markers in required.items():
    path = ROOT / name
    if not path.is_file():
        missing.append(f"missing file: {name}")
        continue
    text = path.read_text(encoding="utf-8")
    for marker in markers:
        if marker not in text:
            missing.append(f"{name}: missing marker {marker!r}")

if missing:
    raise SystemExit("\n".join(missing))
print("PASS: required architecture and LLM QA documents are present")
