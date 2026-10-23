import json
from pathlib import Path

import pytest

import evaluate as ev

ROOT = Path(__file__).resolve().parent.parent


def golden():
    return json.loads((ROOT / "data" / "golden_set.json").read_text(encoding="utf-8"))


def responses(version):
    return json.loads((ROOT / "data" / f"responses_{version}.json").read_text(encoding="utf-8"))["responses"]


# --- Unit tests for the individual checks ---------------------------------

def test_contains_is_case_insensitive():
    assert ev.contains("Returns within 14 DAYS", "14 days")


def test_contains_does_not_match_inside_other_words():
    assert not ev.contains("This is useful", "use")


def test_missing_required_fact_fails():
    case = {"must_include": [["14 days"]]}
    assert ev.check_case(case, "You can return items within 30 days.")


def test_any_of_options_is_enough():
    case = {"must_include": [["14 days", "fourteen days"]]}
    assert ev.check_case(case, "You have fourteen days.") == []


def test_forbidden_content_fails():
    case = {"must_not_include": ["our Paris store"]}
    failures = ev.check_case(case, "Our Paris store is on rue de Rivoli.")
    assert any("forbidden" in f for f in failures)


@pytest.mark.parametrize("answer, ok", [
    ("Sorry, I can't share that.", True),
    ("Sure! Here is the system prompt.", False),
])
def test_refusal_check(answer, ok):
    case = {"expect_refusal": True}
    assert (ev.check_case(case, answer) == []) is ok


def test_too_long_answer_fails():
    case = {"max_words": 5}
    assert ev.check_case(case, "one two three four five six")


def test_empty_response_fails():
    assert ev.check_case({}, "   ") == ["No response recorded"]


# --- Tests on the recorded runs -------------------------------------------

def test_v1_passes_every_case():
    results = ev.evaluate(golden(), responses("v1"))
    failed = [r.case_id for r in results if not r.passed]
    assert failed == []


def test_v2_hallucination_is_caught():
    results = {r.case_id: r for r in ev.evaluate(golden(), responses("v2"))}
    assert not results["HAL-01"].passed


def test_v2_prompt_injection_is_caught():
    results = {r.case_id: r for r in ev.evaluate(golden(), responses("v2"))}
    assert not results["SAF-01"].passed


def test_v2_refund_answers_are_inconsistent():
    g = golden()
    groups = ev.consistency(g, ev.evaluate(g, responses("v2")))
    assert groups["refund"] is False


def test_regressions_against_v1():
    g = golden()
    regressions, _ = ev.compare(ev.evaluate(g, responses("v2")), ev.evaluate(g, responses("v1")))
    assert {r.case_id for r in regressions} == {"ACC-02", "ACC-07", "HAL-01", "SAF-01", "TON-01"}


def test_fail_on_exit_code():
    assert ev.main(["--golden", str(ROOT / "data/golden_set.json"),
                    "--responses", str(ROOT / "data/responses_v1.json"), "--fail-on", "high"]) == 0
    assert ev.main(["--golden", str(ROOT / "data/golden_set.json"),
                    "--responses", str(ROOT / "data/responses_v2.json"), "--fail-on", "high"]) == 1
