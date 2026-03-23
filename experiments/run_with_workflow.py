"""
Workflow memory experiment — induce workflows from successful baseline
trajectories, then re-run the same tasks WITH workflow guidance.

Usage:
    python -m experiments.run_with_workflow [--headless] [--runs N]

Prerequisites:
    1. FastAPI environment running on localhost:3000
    2. Baseline results exist at logs/no_memory_results.json
       (run experiments.run_no_memory first)
"""

import argparse
import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.runner import run_experiment, save_results, load_results
from evaluation.metrics import compute_metrics, format_metrics
from memory.inducer import induce_workflow
from memory.store import save_workflow, load_workflows

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)

BASELINE_PATH = "logs/no_memory_results.json"
RESULTS_PATH = "logs/with_workflow_results.json"

# Same task configs as baseline
TASK_CONFIGS = [
    {"task_id": "flight_search", "params": {"origin": "Boston", "destination": "Chicago", "date": "2026-04-15", "passengers": "2"}},
    {"task_id": "flight_search", "params": {"origin": "New York", "destination": "Los Angeles", "date": "2026-05-01", "passengers": "1"}},
    {"task_id": "flight_search", "params": {"origin": "Denver", "destination": "Seattle", "date": "2026-06-10", "passengers": "3"}},
    {"task_id": "product_search", "params": {"product": "wireless headphones", "sort_order": "price low to high"}},
    {"task_id": "product_search", "params": {"product": "running shoes", "sort_order": "price high to low"}},
    {"task_id": "product_search", "params": {"product": "coffee maker", "sort_order": "price low to high"}},
    {"task_id": "restaurant_reservation", "params": {"party_size": "4", "city": "New York", "date": "2026-05-01", "time": "7:00 PM"}},
    {"task_id": "restaurant_reservation", "params": {"party_size": "2", "city": "San Francisco", "date": "2026-05-15", "time": "8:00 PM"}},
    {"task_id": "restaurant_reservation", "params": {"party_size": "6", "city": "Chicago", "date": "2026-06-01", "time": "6:30 PM"}},
]


async def main():
    parser = argparse.ArgumentParser(description="Run with-workflow experiment")
    parser.add_argument("--headless", action="store_true", default=True)
    parser.add_argument("--no-headless", action="store_false", dest="headless")
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--skip-induction", action="store_true",
                        help="Skip workflow induction (use existing workflows)")
    args = parser.parse_args()

    # Step 1: Induce workflows from baseline successes
    if not args.skip_induction:
        print("=" * 60)
        print("  STEP 1: Inducing workflows from baseline results")
        print("=" * 60)

        if not os.path.exists(BASELINE_PATH):
            print(f"ERROR: Baseline results not found at {BASELINE_PATH}")
            print("Run `python -m experiments.run_no_memory` first.")
            sys.exit(1)

        baseline_results = load_results(BASELINE_PATH)
        successful = [r for r in baseline_results if r.get("success")]
        print(f"Found {len(successful)} successful trajectories out of {len(baseline_results)}")

        # Induce one workflow per task_type from the first successful trajectory
        seen_types = set()
        for result in successful:
            task_type = result["task_id"]
            if task_type in seen_types:
                continue
            seen_types.add(task_type)

            # Check if workflow already exists
            existing = load_workflows(task_type=task_type)
            if existing:
                print(f"  Workflow already exists for {task_type}, skipping induction")
                continue

            print(f"\n  Inducing workflow for {task_type}...")
            wf = induce_workflow(
                trajectory=result["trajectory"],
                task_instruction=result.get("instruction", ""),
                task_type=task_type,
            )
            path = save_workflow(wf)
            print(f"  Saved: {path}")
            print(f"  Description: {wf.description}")
            print(f"  Steps: {len(wf.steps)}")

    # Step 2: Run experiment with workflow memory
    print()
    print("=" * 60)
    print("  STEP 2: Running tasks WITH workflow memory")
    print(f"  Tasks: {len(TASK_CONFIGS)} configs × {args.runs} run(s)")
    print(f"  Headless: {args.headless}")
    print("=" * 60)

    results = await run_experiment(
        task_configs=TASK_CONFIGS,
        use_workflow=True,
        num_runs=args.runs,
        headless=args.headless,
    )

    save_results(results, RESULTS_PATH)

    metrics = compute_metrics(results)
    print(format_metrics(metrics, label="With Workflow Memory"))


if __name__ == "__main__":
    asyncio.run(main())
