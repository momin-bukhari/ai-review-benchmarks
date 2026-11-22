"""Generate coverage table and benchmark report."""

import json
from pathlib import Path

from benchmark.scorer import load_answer_key, score_all, CaseScore, SCORES


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
REPORT_PATH = DATA_DIR / "report.md"
CONFIG_PATH = Path(__file__).resolve().parent / "config.json"


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def coverage_table(all_scores: dict[str, list[CaseScore]]) -> str:
    key = load_answer_key()
    case_ids = sorted(key.keys())
    header = "| Provider | " + " | ".join(case_ids) + " | Completed | Score |"
    sep = "|----------|" + "|".join(["----"] * len(case_ids)) + "|-----------|-------|"
    rows = [header, sep]
    for provider, scores in sorted(all_scores.items()):
        score_map = {s.case_id: s for s in scores}
        cells = []
        completed = 0
        total_pct = 0.0
        scored_count = 0
        for cid in case_ids:
            cs = score_map.get(cid)
            if cs and cs.findings:
                cells.append(f"{cs.pct:.0%}")
                completed += 1
                total_pct += cs.pct
                scored_count += 1
            else:
                cells.append("--")
        avg = f"{total_pct / scored_count:.0%}" if scored_count else "--"
        rows.append(f"| {provider} | " + " | ".join(cells) + f" | {completed}/{len(case_ids)} | {avg} |")
    return "\n".join(rows)


def generate_report(all_scores: dict[str, list[CaseScore]]) -> str:
    key = load_answer_key()
    config = load_config()
    table = coverage_table(all_scores)

    sections = []
    sections.append("# AI Review Benchmark Report\n")
    sections.append("## Summary\n")
    sections.append(
        f"This benchmark compares AI pull request reviewers on {len(key)} proposed changes "
        f"to a Python report scheduling service. "
        f"{len(all_scores)} provider(s) were evaluated.\n"
    )

    sections.append("## Coverage\n")
    sections.append(table + "\n")

    sections.append("## Methodology\n")
    sections.append(
        "- Each provider reviewed the same 8 proposed changes independently.\n"
        "- Reviews were collected using a standardized prompt with the PR title, body, "
        "baseline source code, patch diff, and (for cases 04-06) deployment evidence.\n"
        "- The answer key was defined before any reviews were collected.\n"
        "- Each finding is scored: found (1.0), partial (0.5), missed (0.0), false_positive (-0.5).\n"
        "- Per-case score = sum of finding scores / max possible score.\n"
    )

    sections.append("## Case-by-Case Analysis\n")
    for case_id in sorted(key.keys()):
        case_key = key[case_id]
        sections.append(f"### Case {case_id}: {case_key['title']}\n")
        sections.append(f"**Context:** {case_key['context']}\n")
        sections.append("**Expected findings:**\n")
        for f in case_key["findings"]:
            sections.append(f"- `{f['id']}` ({f['category']}, {f['severity']}): {f['credit']}\n")
        sections.append("\n**Results:**\n")
        for provider, scores in sorted(all_scores.items()):
            cs = next((s for s in scores if s.case_id == case_id), None)
            if cs and cs.findings:
                sections.append(f"*{provider}:* {cs.pct:.0%}\n")
                for fs in cs.findings:
                    emoji = {"found": "FOUND", "partial": "PARTIAL", "missed": "MISSED", "false_positive": "FP"}
                    sections.append(
                        f"  - `{fs.finding_id}`: **{emoji.get(fs.outcome, fs.outcome)}** — {fs.reasoning}\n"
                    )
            else:
                sections.append(f"*{provider}:* not run\n")
        sections.append("")

    sections.append("## Adding a Provider\n")
    sections.append(
        "1. Register the provider in `benchmark/config.json`.\n"
        "2. Create a provider class in `benchmark/providers/` that implements the `Provider` interface.\n"
        "3. Run `python3 benchmark/run.py run --provider <name> --all` to generate prompts.\n"
        "4. Collect reviews and save them to `data/reviews/<provider>/<case>.md`.\n"
        "5. Run `python3 benchmark/run.py score --provider <name>` to create score templates.\n"
        "6. Edit the score templates to grade each finding.\n"
        "7. Run `python3 benchmark/run.py report` to regenerate this report.\n"
    )

    sections.append("## Limitations\n")
    sections.append(
        "- 8 cases in one application give limited evidence about general review quality.\n"
        "- Manual scoring introduces subjective judgment.\n"
        "- Only one provider evaluated so far; comparisons require more providers.\n"
        "- No repeat runs to measure variability.\n"
        "- AWS deployment trace not included (no AWS access for this run).\n"
    )

    return "\n".join(sections)


def write_report(all_scores: dict[str, list[CaseScore]]):
    report = generate_report(all_scores)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Report written to {REPORT_PATH}")
    print()
    print(coverage_table(all_scores))
