"""Score reviews against the pre-defined answer key."""

import json
from dataclasses import dataclass, field
from pathlib import Path


ANSWER_KEY_PATH = Path(__file__).resolve().parent / "answer_key.json"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

SCORES = {"found": 1.0, "partial": 0.5, "missed": 0.0, "false_positive": -0.5}


@dataclass
class FindingScore:
    finding_id: str
    category: str
    severity: str
    outcome: str
    score: float
    reasoning: str


@dataclass
class CaseScore:
    case_id: str
    case_title: str
    findings: list[FindingScore] = field(default_factory=list)
    total_score: float = 0.0
    max_score: float = 0.0
    pct: float = 0.0

    def finalize(self):
        self.total_score = sum(f.score for f in self.findings)
        self.max_score = sum(1.0 for f in self.findings if f.outcome != "false_positive")
        self.pct = self.total_score / self.max_score if self.max_score > 0 else 0.0


def load_answer_key() -> dict:
    return json.loads(ANSWER_KEY_PATH.read_text(encoding="utf-8"))


def load_review(provider: str, case_id: str) -> str:
    review_path = DATA_DIR / "reviews" / provider / f"{case_id}.md"
    if not review_path.exists():
        raise FileNotFoundError(f"Review not found: {review_path}")
    return review_path.read_text(encoding="utf-8").strip()


def score_review(provider: str, case_id: str, review_text: str, case_key: dict) -> CaseScore:
    score_path = DATA_DIR / "scores" / provider / f"{case_id}.json"
    if not score_path.exists():
        raise FileNotFoundError(
            f"Score not found: {score_path}\n"
            f"Run manual scoring for case {case_id} with provider {provider}"
        )
    data = json.loads(score_path.read_text(encoding="utf-8"))
    findings = [
        FindingScore(
            finding_id=f["finding_id"],
            category=f["category"],
            severity=f["severity"],
            outcome=f["outcome"],
            score=SCORES.get(f["outcome"], 0.0),
            reasoning=f["reasoning"],
        )
        for f in data["findings"]
    ]
    cs = CaseScore(case_id=case_id, case_title=case_key["title"], findings=findings)
    cs.finalize()
    return cs


def score_all(provider: str) -> list[CaseScore]:
    key = load_answer_key()
    results = []
    for case_id, case_key in sorted(key.items()):
        try:
            review_text = load_review(provider, case_id)
            cs = score_review(provider, case_id, review_text, case_key)
            results.append(cs)
        except FileNotFoundError:
            results.append(CaseScore(case_id=case_id, case_title=case_key["title"]))
    return results


def save_score_template(provider: str, case_id: str, case_key: dict):
    out_dir = DATA_DIR / "scores" / provider
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{case_id}.json"
    if out_path.exists():
        print(f"  Score already exists: {out_path}")
        return
    template = {
        "case_id": case_id,
        "provider": provider,
        "findings": [
            {
                "finding_id": f["id"],
                "category": f["category"],
                "severity": f["severity"],
                "description": f["description"],
                "outcome": "missed",
                "reasoning": "",
            }
            for f in case_key["findings"]
        ],
    }
    out_path.write_text(json.dumps(template, indent=2) + "\n", encoding="utf-8")
    print(f"  Created score template: {out_path}")
    print(f"  Edit the file to set outcome (found/partial/missed/false_positive) and reasoning.")
