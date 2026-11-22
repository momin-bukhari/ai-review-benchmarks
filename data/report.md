# AI Review Benchmark Report

## Summary

This benchmark compares AI pull request reviewers on 8 proposed changes to a Python report scheduling service. 1 provider(s) were evaluated.

## Coverage

| Provider | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | Completed | Score |
|----------|----|----|----|----|----|----|----|----|-----------|-------|
| command-code | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 8/8 | 100% |

## Methodology

- Each provider reviewed the same 8 proposed changes independently.
- Reviews were collected using a standardized prompt with the PR title, body, baseline source code, patch diff, and (for cases 04-06) deployment evidence.
- The answer key was defined before any reviews were collected.
- Each finding is scored: found (1.0), partial (0.5), missed (0.0), false_positive (-0.5).
- Per-case score = sum of finding scores / max possible score.

## Case-by-Case Analysis

### Case 01: Page report history by scheduled time

**Context:** code-only

**Expected findings:**

- `01-cursor-tiebreaker` (bug, high): Identifies the pagination correctness bug

- `01-cursor-extraction` (note, low): Notes the cursor contract change


**Results:**

*command-code:* 100%

  - `01-cursor-tiebreaker`: **FOUND** — Review explicitly identifies the tiebreaker mismatch with a concrete example showing how rows get skipped across pages.

  - `01-cursor-extraction`: **FOUND** — Review notes the cursor contract change from id to timestamp and flags the backward compatibility concern.


### Case 02: Stream the report export

**Context:** code-only

**Expected findings:**

- `02-csv-escaping` (bug, high): Identifies the data corruption risk from dropped CSV escaping

- `02-streaming-good` (note, low): Acknowledges the streaming improvement


**Results:**

*command-code:* 100%

  - `02-csv-escaping`: **FOUND** — Review clearly identifies the CSV escaping loss with specific examples (commas, quotes, newlines) and provides a fix that keeps csv.writer while still enabling streaming.

  - `02-streaming-good`: **FOUND** — Review acknowledges that cursor iteration is the correct streaming approach and separates it from the escaping regression.


### Case 03: Batch queued deliveries

**Context:** code-only

**Expected findings:**

- `03-remainder-bug` (bug, critical): Identifies the off-by-one remainder handling bug

- `03-batching-approach` (note, low): Acknowledges the batching optimization intent


**Results:**

*command-code:* 100%

  - `03-remainder-bug`: **FOUND** — Review identifies the off-by-one with a concrete example (25 jobs -> 20 processed) and provides the correct fix using range(0, len(jobs), batch_size).

  - `03-batching-approach`: **FOUND** — Review acknowledges executemany as a reasonable optimization and separates the approach from the loop bounds bug.


### Case 04: Retire the legacy delivery column

**Context:** with-evidence

**Expected findings:**

- `04-elm-workers-break` (risk, critical): Identifies that dropping the column breaks live elm workers

- `04-deploy-ordering` (note, medium): Suggests deployment ordering or gating


**Results:**

*command-code:* 100%

  - `04-elm-workers-break`: **FOUND** — Review identifies the exact workers-17 query at elm, explains the column-drop impact, and notes cedar is unaffected.

  - `04-deploy-ordering`: **FOUND** — Review provides three concrete mitigation options: upgrade workers first, add pre-migration check, or use expand-and-contract pattern.


### Case 05: Increase export batch size

**Context:** with-evidence

**Expected findings:**

- `05-cedar-rejection` (risk, critical): Identifies that batch size 50 exceeds cedar's limit of 40

- `05-elm-ok` (note, low): Notes the asymmetric impact


**Results:**

*command-code:* 100%

  - `05-cedar-rejection`: **FOUND** — Review identifies that batch size 50 exceeds cedar's limit of 40, quotes the rejection policy, and explains that all 70 ready rows would be stuck.

  - `05-elm-ok`: **FOUND** — Review notes the asymmetric impact: elm at limit 100 handles it fine, cedar at 40 does not.


### Case 06: Use the new delivery queue

**Context:** with-evidence

**Expected findings:**

- `06-elm-no-consumer` (risk, critical): Identifies that elm has no consumer for the new queue

- `06-cedar-ok` (note, low): Notes the asymmetric impact


**Results:**

*command-code:* 100%

  - `06-elm-no-consumer`: **FOUND** — Review identifies that elm only subscribes to 'reports', notes the 8 jobs due in the window would be stranded, and correctly distinguishes new vs existing jobs.

  - `06-cedar-ok`: **FOUND** — Review notes cedar subscribes to both queues and would handle the change.


### Case 07: Index pending deliveries

**Context:** code-only

**Expected findings:**

- `07-clean-change` (good, none): Correctly identifies this as a clean change or stays quiet


**Results:**

*command-code:* 100%

  - `07-clean-change`: **FOUND** — Review correctly identifies this as a clean change, explains how the index columns match the worker query, and raises no false concerns.


### Case 08: Include a total in the activity summary

**Context:** code-only

**Expected findings:**

- `08-clean-change` (good, none): Correctly identifies this as a clean change or stays quiet


**Results:**

*command-code:* 100%

  - `08-clean-change`: **FOUND** — Review correctly identifies this as a clean change, verifies the math (count(delivered_at) + (count(*) - count(delivered_at)) = count(*)), and raises no false concerns.


## Adding a Provider

1. Register the provider in `benchmark/config.json`.
2. Create a provider class in `benchmark/providers/` that implements the `Provider` interface.
3. Run `python3 benchmark/run.py run --provider <name> --all` to generate prompts.
4. Collect reviews and save them to `data/reviews/<provider>/<case>.md`.
5. Run `python3 benchmark/run.py score --provider <name>` to create score templates.
6. Edit the score templates to grade each finding.
7. Run `python3 benchmark/run.py report` to regenerate this report.

## Limitations

- 8 cases in one application give limited evidence about general review quality.
- Manual scoring introduces subjective judgment.
- Only one provider evaluated so far; comparisons require more providers.
- No repeat runs to measure variability.
- AWS deployment trace not included (no AWS access for this run).
