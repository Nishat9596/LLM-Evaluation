# LLM Chatbot Evaluation

![LLM Evaluation](https://github.com/Nishat9596/LLM-Evaluation/actions/workflows/evaluate.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![pytest](https://img.shields.io/badge/pytest-0A9EDC?logo=pytest&logoColor=white)

A small evaluation tool that checks an AI chatbot's answers against a **golden test set** and catches the problems that matter most in LLM products: wrong answers, hallucinations, unsafe replies, inconsistent answers and regressions after a model or prompt change.

## How it works

1. **Golden set** ([`data/golden_set.json`](data/golden_set.json)) – 16 test prompts for "ShopBot", an online-store support assistant, with the facts each answer must include, content it must never include, and whether it should refuse.
2. **Recorded responses** – the bot's answers for each release:
   - [`responses_v1.json`](data/responses_v1.json): current release
   - [`responses_v2.json`](data/responses_v2.json): new candidate (new model and prompt)
3. **Evaluator** ([`evaluate.py`](evaluate.py)) – runs the checks, compares releases and writes a Markdown report.

| Check | What it catches | Example |
|---|---|---|
| Accuracy | Required facts missing or wrong | Says 30-day returns instead of 14 |
| Hallucination | Invented facts; not admitting it doesn't know | Gives an address for a store that doesn't exist |
| Safety | Prompt injection, personal data leaks, help with fraud | Reveals its system prompt |
| Consistency | Different answers to the same question asked in other words | 14 days in one answer, 30 in another |
| Tone | Rude, defensive or overly long replies | 82-word reply to an angry customer |
| Regression | Cases that passed before and fail now | Compares v2 against v1 |

## Results

| Release | Passed | Critical failures | Report |
|---|---|---|---|
| v1 | 16/16 (100%) | 0 | [reports/v1.md](reports/v1.md) |
| v2 | 11/16 (69%) | 2 | [reports/v2_vs_v1.md](reports/v2_vs_v1.md) |

The v2 candidate looks fine at first glance, but the evaluation finds **5 regressions**, including a hallucinated Paris store and a system-prompt leak. **Verdict: v2 should not be released.**

## Run it

```bash
pip install -r requirements.txt
pytest -v                                         # unit tests for the evaluator
python evaluate.py --responses data/responses_v1.json --fail-on high
python evaluate.py --responses data/responses_v2.json --baseline data/responses_v1.json \
    --report reports/v2_vs_v1.md
```

`--fail-on high` makes the script exit with an error when any high or critical case fails, so it can block a release in CI. GitHub Actions runs the unit tests and both evaluations on every push.

## Testing a real chatbot
Save the bot's answers in the same format as `data/responses_v1.json` (one answer per test ID), then run the evaluator on that file. Because LLM answers vary between runs, the checks look for **key facts and behaviour** rather than exact wording. For important prompts, collect several runs and evaluate each one.

## Design notes
- Phrase matching is case-insensitive and respects word boundaries, so "use" doesn't match "useful".
- Each required fact accepts several wordings (for example "14 days" or "fourteen days").
- Failures are sorted by severity, so critical problems appear first in the report.

---
**Nishat Shareef** · QA Tester · Dubai, UAE · [LinkedIn](https://www.linkedin.com/in/nishat-shareef-qa)
