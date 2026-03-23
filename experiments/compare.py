"""
Compare results from the no-memory baseline and workflow-memory experiments.

Usage:
    python -m experiments.compare

Prerequisites:
    Both result files must exist:
      - logs/no_memory_results.json
      - logs/with_workflow_results.json
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.runner import load_results
from evaluation.metrics import compute_metrics, format_metrics, format_comparison

BASELINE_PATH = "logs/no_memory_results.json"
WORKFLOW_PATH = "logs/with_workflow_results.json"


def main():
    if not os.path.exists(BASELINE_PATH):
        print(f"ERROR: {BASELINE_PATH} not found. Run baseline experiment first.")
        sys.exit(1)
    if not os.path.exists(WORKFLOW_PATH):
        print(f"ERROR: {WORKFLOW_PATH} not found. Run workflow experiment first.")
        sys.exit(1)

    baseline_results = load_results(BASELINE_PATH)
    workflow_results = load_results(WORKFLOW_PATH)

    baseline_metrics = compute_metrics(baseline_results)
    workflow_metrics = compute_metrics(workflow_results)

    # Print individual summaries
    print(format_metrics(baseline_metrics, label="Baseline — No Workflow Memory"))
    print(format_metrics(workflow_metrics, label="With Workflow Memory"))

    # Print side-by-side comparison
    print(format_comparison(
        baseline_metrics, "No Memory",
        workflow_metrics, "With Workflow",
    ))

    # Compute improvement
    base_sr = baseline_metrics["success_rate"]
    wf_sr = workflow_metrics["success_rate"]
    base_steps = baseline_metrics["avg_steps_all"]
    wf_steps = workflow_metrics["avg_steps_all"]
    base_time = baseline_metrics["avg_time_all"]
    wf_time = workflow_metrics["avg_time_all"]

    print("  Key Findings:")
    if wf_sr > base_sr:
        print(f"  • Success rate improved: {base_sr:.1%} → {wf_sr:.1%} (+{wf_sr - base_sr:.1%})")
    elif wf_sr == base_sr:
        print(f"  • Success rate unchanged: {base_sr:.1%}")
    else:
        print(f"  • Success rate decreased: {base_sr:.1%} → {wf_sr:.1%} ({wf_sr - base_sr:.1%})")

    if base_steps > 0 and wf_steps > 0:
        if wf_steps < base_steps:
            pct = (base_steps - wf_steps) / base_steps * 100
            print(f"  • Steps reduced: {base_steps:.1f} → {wf_steps:.1f} (-{pct:.0f}%)")
        else:
            print(f"  • Avg steps: {base_steps:.1f} → {wf_steps:.1f}")

    if base_time > 0 and wf_time > 0:
        if wf_time < base_time:
            pct = (base_time - wf_time) / base_time * 100
            print(f"  • Time reduced: {base_time:.1f}s → {wf_time:.1f}s (-{pct:.0f}%)")
        else:
            diff_pct = (wf_time - base_time) / base_time * 100
            print(f"  • Avg time: {base_time:.1f}s → {wf_time:.1f}s (+{diff_pct:.0f}%)")
    print()


if __name__ == "__main__":
    main()
