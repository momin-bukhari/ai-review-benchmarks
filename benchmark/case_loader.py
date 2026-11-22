"""Load review cases from the cases/ directory."""

from dataclasses import dataclass, field
from pathlib import Path


CASES_DIR = Path(__file__).resolve().parent.parent / "cases"


@dataclass(frozen=True)
class Case:
    id: str
    title: str
    body: str
    patch: str
    evidence: str | None = None
    has_evidence: bool = False


def load_case(case_id: str) -> Case:
    case_dir = CASES_DIR / case_id
    if not case_dir.is_dir():
        raise FileNotFoundError(f"Case directory not found: {case_dir}")
    title = (case_dir / "title.txt").read_text(encoding="utf-8").strip()
    body = (case_dir / "body.md").read_text(encoding="utf-8").strip()
    patch = (case_dir / "change.patch").read_text(encoding="utf-8").strip()
    evidence_path = case_dir / "evidence.md"
    evidence = evidence_path.read_text(encoding="utf-8").strip() if evidence_path.exists() else None
    return Case(
        id=case_id,
        title=title,
        body=body,
        patch=patch,
        evidence=evidence,
        has_evidence=evidence is not None,
    )


def load_all_cases() -> list[Case]:
    cases = []
    for case_dir in sorted(CASES_DIR.iterdir()):
        if case_dir.is_dir() and (case_dir / "change.patch").exists():
            cases.append(load_case(case_dir.name))
    return cases


def load_baseline_source() -> str:
    reports_path = Path(__file__).resolve().parent.parent / "reports.py"
    return reports_path.read_text(encoding="utf-8")
