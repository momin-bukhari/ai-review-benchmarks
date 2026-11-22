"""AI Review Benchmark CLI."""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from benchmark.case_loader import load_case, load_all_cases, load_baseline_source
from benchmark.scorer import load_answer_key, score_all, save_score_template
from benchmark.reporter import write_report


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PROMPTS_DIR = DATA_DIR / "prompts"


def generate_prompt(case_id: str) -> str:
    case = load_case(case_id)
    baseline = load_baseline_source()

    parts = [
        "Review this proposed pull request change to a Python report scheduling service.",
        "Identify any bugs, risks, correctness issues, or concerns. Also note positive aspects.",
        "",
        f"## PR Title",
        case.title,
        "",
        f"## PR Description",
        case.body,
        "",
        "## Current Source Code (reports.py)",
        "```python",
        baseline,
        "```",
        "",
        "## Proposed Change (patch)",
        "```diff",
        case.patch,
        "```",
    ]
    if case.evidence:
        parts.extend([
            "",
            "## Deployment Evidence",
            case.evidence,
        ])
    parts.extend([
        "",
        "## Instructions",
        "Review this change as if you were a code reviewer on the PR.",
        "Focus on: correctness bugs, deployment risks, edge cases, and whether the change achieves its stated goal.",
        "Be specific — cite code and line references where possible.",
    ])
    return "\n".join(parts)


def cmd_run(args):
    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    if args.all:
        cases = load_all_cases()
    else:
        cases = [load_case(args.case)]
    for case in cases:
        prompt = generate_prompt(case.id)
        prompt_path = PROMPTS_DIR / f"{case.id}.md"
        prompt_path.write_text(prompt, encoding="utf-8")
        review_path = DATA_DIR / "reviews" / args.provider / f"{case.id}.md"
        review_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_note = " (includes deployment evidence)" if case.has_evidence else ""
        print(f"  Case {case.id}: {case.title}{evidence_note}")
        print(f"    Prompt:  {prompt_path}")
        print(f"    Review:  {review_path} {'(exists)' if review_path.exists() else '(needed)'}")
    print()
    total = len(cases)
    done = sum(1 for c in cases if (DATA_DIR / "reviews" / args.provider / f"{c.id}.md").exists())
    print(f"Progress: {done}/{total} reviews collected for '{args.provider}'")
    if done < total:
        print(f"To collect a review: open data/prompts/<case>.md, review the change,")
        print(f"and save your review to data/reviews/{args.provider}/<case>.md")


def cmd_score(args):
    key = load_answer_key()
    provider = args.provider
    print(f"Scoring provider: {provider}")
    for case_id in sorted(key.keys()):
        review_path = DATA_DIR / "reviews" / provider / f"{case_id}.md"
        if not review_path.exists():
            print(f"  Case {case_id}: no review found, skipping")
            continue
        save_score_template(provider, case_id, key[case_id])
    print()
    print("Next steps:")
    print(f"  1. Edit files in data/scores/{provider}/ to set outcome and reasoning")
    print(f"  2. Valid outcomes: found, partial, missed, false_positive")
    print(f"  3. Run: python3 benchmark/run.py report")


def cmd_report(args):
    key = load_answer_key()
    config = json.loads((Path(__file__).resolve().parent / "config.json").read_text(encoding="utf-8"))
    all_scores = {}
    for provider_name in config["providers"]:
        scores = score_all(provider_name)
        has_any = any(s.findings for s in scores)
        if has_any:
            all_scores[provider_name] = scores
    if not all_scores:
        print("No scored reviews found. Run 'score' first.")
        return
    write_report(all_scores)


def cmd_status(args):
    key = load_answer_key()
    config = json.loads((Path(__file__).resolve().parent / "config.json").read_text(encoding="utf-8"))
    cases = load_all_cases()
    print(f"Cases: {len(cases)}")
    for c in cases:
        ev = " +evidence" if c.has_evidence else ""
        print(f"  {c.id}: {c.title}{ev}")
    print()
    print("Providers:")
    for name, info in config["providers"].items():
        reviews_dir = DATA_DIR / "reviews" / name
        count = len(list(reviews_dir.glob("*.md"))) if reviews_dir.exists() else 0
        scores_dir = DATA_DIR / "scores" / name
        scored = len(list(scores_dir.glob("*.json"))) if scores_dir.exists() else 0
        print(f"  {name}: status={info['status']}, reviews={count}/8, scored={scored}/8")


def main():
    parser = argparse.ArgumentParser(description="AI Review Benchmark")
    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="Generate review prompts and track collection")
    run_p.add_argument("--provider", required=True, help="Provider name")
    run_g = run_p.add_mutually_exclusive_group(required=True)
    run_g.add_argument("--case", help="Single case ID (e.g. 01)")
    run_g.add_argument("--all", action="store_true", help="All cases")

    score_p = sub.add_parser("score", help="Create score templates for grading")
    score_p.add_argument("--provider", required=True, help="Provider name")

    sub.add_parser("report", help="Generate coverage table and report")
    sub.add_parser("status", help="Show benchmark status")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    {"run": cmd_run, "score": cmd_score, "report": cmd_report, "status": cmd_status}[args.command](args)


if __name__ == "__main__":
    main()
