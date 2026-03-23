"""
Baseline experiment — run all tasks WITHOUT workflow memory.

Usage:
    python -m experiments.run_no_memory [--headless] [--runs N]

Make sure the FastAPI environment is running on localhost:3000 first.
"""

import argparse
import asyncio
import logging
import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.runner import run_experiment, save_results
from evaluation.metrics import compute_metrics, format_metrics

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)

# Task configs: 3 variations per task type = 9 total
TASK_CONFIGS = [
    # Flight search variations
    {"task_id": "flight_search", "params": {"origin": "Boston", "destination": "Chicago", "date": "2026-04-15", "passengers": "2"}},
    {"task_id": "flight_search", "params": {"origin": "New York", "destination": "Los Angeles", "date": "2026-05-01", "passengers": "1"}},
    {"task_id": "flight_search", "params": {"origin": "Denver", "destination": "Seattle", "date": "2026-06-10", "passengers": "3"}},

    # Product search variations
    {"task_id": "product_search", "params": {"product": "wireless headphones", "sort_order": "price low to high"}},
    {"task_id": "product_search", "params": {"product": "running shoes", "sort_order": "price high to low"}},
    {"task_id": "product_search", "params": {"product": "coffee maker", "sort_order": "price low to high"}},

    # Restaurant reservation variations
    {"task_id": "restaurant_reservation", "params": {"party_size": "4", "city": "New York", "date": "2026-05-01", "time": "7:00 PM"}},
    {"task_id": "restaurant_reservation", "params": {"party_size": "2", "city": "San Francisco", "date": "2026-05-15", "time": "8:00 PM"}},
    {"task_id": "restaurant_reservation", "params": {"party_size": "6", "city": "Chicago", "date": "2026-06-01", "time": "6:30 PM"}},
]

RESULTS_PATH = "logs/no_memory_results.json"


async def main():
    parser = argparse.ArgumentParser(description="Run baseline (no memory) experiment")
    parser.add_argument("--headless", action="store_true", default=True,
                        help="Run browser headlessly (default: True)")
    parser.add_argument("--no-headless", action="store_false", dest="headless",
                        help="Show the browser window")
    parser.add_argument("--runs", type=int, default=1,
                        help="Number of runs per task config (default: 1)")
    args = parser.parse_args()

    print("=" * 60)
    print("  BASELINE EXPERIMENT — No Workflow Memory")
    print(f"  Tasks: {len(TASK_CONFIGS)} configs × {args.runs} run(s)")
    print(f"  Headless: {args.headless}")
    print("=" * 60)

    results = await run_experiment(
        task_configs=TASK_CONFIGS,
        use_workflow=False,
        num_runs=args.runs,
        headless=args.headless,
    )

    save_results(results, RESULTS_PATH)

    metrics = compute_metrics(results)
    print(format_metrics(metrics, label="Baseline — No Workflow Memory"))


if __name__ == "__main__":
    asyncio.run(main())
