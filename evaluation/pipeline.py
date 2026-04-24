"""Evaluation pipeline — runs golden dataset through rule-based scorer."""
import json
import sys
import argparse
from pathlib import Path
from datetime import datetime

from evaluation.models import (
    EvalReport,
    EvalResult,
    EvalScores,
    GoldenConversation,
)
from evaluation.scorer import score_conversation

GOLDEN_DATASET_PATH = Path(__file__).parent / "golden" / "golden_dataset.json"
PASS_THRESHOLD = 0.85


def _load_dataset(dataset_path: Path) -> list[GoldenConversation]:
    with open(dataset_path) as f:
        raw = json.load(f)
    return [GoldenConversation(**entry) for entry in raw]


def run_single_eval(conversation: GoldenConversation) -> EvalResult:
    """Score a single golden conversation using the rule-based scorer.

    The 'agent_response' field in the golden dataset contains the expected
    (or sample) response to score. In a live eval, this would be replaced
    by the actual agent response.
    """
    agent_response: str = getattr(conversation, "agent_response", "")
    if not agent_response:
        # Fall back to last assistant turn in the conversation
        for turn in reversed(conversation.conversation):
            if turn.role == "assistant":
                agent_response = turn.content
                break

    actual_scores = score_conversation(conversation, agent_response)

    # A result passes if it scores at or above the expected scores
    # For failure scenarios (expected score < 1) we just compare actual == expected
    passes = (
        actual_scores.task_completion >= conversation.expected_scores.task_completion
        and actual_scores.hallucination_free >= conversation.expected_scores.hallucination_free
        and actual_scores.allergen_safe >= conversation.expected_scores.allergen_safe
        and actual_scores.on_scope >= conversation.expected_scores.on_scope
    )

    failure_reasons = []
    if actual_scores.task_completion < conversation.expected_scores.task_completion:
        failure_reasons.append("task_completion below expected")
    if actual_scores.hallucination_free < conversation.expected_scores.hallucination_free:
        failure_reasons.append("hallucination_free below expected")
    if actual_scores.allergen_safe < conversation.expected_scores.allergen_safe:
        failure_reasons.append("allergen_safe below expected")
    if actual_scores.on_scope < conversation.expected_scores.on_scope:
        failure_reasons.append("on_scope below expected")

    return EvalResult(
        golden_id=conversation.id,
        passed=passes,
        actual_scores=actual_scores,
        expected_scores=conversation.expected_scores,
        agent_response=agent_response,
        failure_reasons=failure_reasons,
    )


def run_eval_pipeline(dataset_path: Path = GOLDEN_DATASET_PATH) -> EvalReport:
    """Load golden dataset and score all conversations."""
    conversations = _load_dataset(dataset_path)

    if not conversations:
        raise ValueError(f"No conversations found in {dataset_path}")

    results = [run_single_eval(c) for c in conversations]

    passed = [r for r in results if r.passed]
    pass_rate = len(passed) / len(results)

    report = EvalReport(
        total=len(results),
        passed=len(passed),
        failed=len(results) - len(passed),
        pass_rate=pass_rate,
        avg_task_completion=sum(r.actual_scores.task_completion for r in results) / len(results),
        avg_hallucination_free=sum(r.actual_scores.hallucination_free for r in results) / len(results),
        avg_allergen_safe=sum(r.actual_scores.allergen_safe for r in results) / len(results),
        avg_on_scope=sum(r.actual_scores.on_scope for r in results) / len(results),
        results=results,
    )

    _print_report(report)
    return report


def _print_report(report: EvalReport) -> None:
    print(f"\nEval Report — {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 50)
    print(f"Total conversations: {report.total}")
    print(f"Passed:             {report.passed}")
    print(f"Failed:             {report.failed}")
    print(f"Pass rate:          {report.pass_rate:.1%}  (threshold: {PASS_THRESHOLD:.0%})")
    print(f"\nAverage scores:")
    print(f"  task_completion:  {report.avg_task_completion:.2f}")
    print(f"  hallucination_free: {report.avg_hallucination_free:.2f}")
    print(f"  allergen_safe:    {report.avg_allergen_safe:.2f}")
    print(f"  on_scope:         {report.avg_on_scope:.2f}")
    print()

    if report.failed > 0:
        print("Failed conversations:")
        for r in report.results:
            if not r.passed:
                print(f"  [{r.golden_id}] {', '.join(r.failure_reasons)}")

    status = "PASS" if report.meets_threshold else "FAIL"
    print(f"\nRESULT: {status}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run evaluation pipeline")
    parser.add_argument("--dataset", default="golden", help="Dataset name to run")
    args = parser.parse_args()

    dataset_path = GOLDEN_DATASET_PATH
    report = run_eval_pipeline(dataset_path)
    sys.exit(0 if report.meets_threshold else 1)
