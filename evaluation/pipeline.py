"""Evaluation pipeline — runs golden dataset against live agent."""
import json
import asyncio
import argparse
from pathlib import Path
from evaluation.models import GoldenConversation, EvalResult, EvalReport, EvalScores


GOLDEN_DATASET_PATH = Path(__file__).parent / "golden" / "golden_dataset.json"
PASS_THRESHOLD = 0.85


async def run_single_eval(conversation: GoldenConversation) -> EvalResult:
    """Run a single golden conversation through the agent and score it."""
    # TODO Week 6: call live agent, score response against rubric
    raise NotImplementedError("Implement in Week 6")


async def run_eval_pipeline(dataset_path: Path = GOLDEN_DATASET_PATH) -> EvalReport:
    """Load golden dataset and run all conversations through the agent."""
    with open(dataset_path) as f:
        raw = json.load(f)

    conversations = [GoldenConversation(**entry) for entry in raw]
    results = await asyncio.gather(*[run_single_eval(c) for c in conversations])

    passed = [r for r in results if r.passed]
    pass_rate = len(passed) / len(results) if results else 0.0

    report = EvalReport(
        total=len(results),
        passed=len(passed),
        failed=len(results) - len(passed),
        pass_rate=pass_rate,
        avg_task_completion=sum(r.actual_scores.task_completion for r in results) / len(results),
        avg_hallucination_free=sum(r.actual_scores.hallucination_free for r in results) / len(results),
        avg_allergen_safe=sum(r.actual_scores.allergen_safe for r in results) / len(results),
        avg_on_scope=sum(r.actual_scores.on_scope for r in results) / len(results),
        results=list(results),
    )

    print(f"\nEval Report")
    print(f"===========")
    print(f"Total:      {report.total}")
    print(f"Passed:     {report.passed}")
    print(f"Pass rate:  {report.pass_rate:.1%} (threshold: {PASS_THRESHOLD:.0%})")
    print(f"RESULT:     {'PASS' if report.meets_threshold else 'FAIL'}")

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="golden", help="Dataset name to run")
    args = parser.parse_args()
    asyncio.run(run_eval_pipeline())
