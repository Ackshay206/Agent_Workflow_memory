"""
Experiment runner — execute multiple tasks and collect results.

Handles running batches of tasks with the WebAgent, optionally injecting
workflow memory, and collecting structured results for analysis.
"""

import asyncio
import json
import logging
import os
from datetime import datetime

from agent.base_agent import WebAgent
from memory.retriever import retrieve_workflow

logger = logging.getLogger(__name__)


async def run_experiment(
    task_configs: list[dict],
    use_workflow: bool = False,
    num_runs: int = 1,
    headless: bool = True,
    model: str = "gpt-4o-mini",
    max_steps: int = 15,
) -> list[dict]:
    """Run a batch of tasks and collect results.

    Parameters
    ----------
    task_configs : list[dict]
        Each dict has "task_id" and optionally "params".
        Example: [{"task_id": "flight_search", "params": {"origin": "NYC"}}]
    use_workflow : bool
        If True, retrieve and inject workflow memory for each task.
    num_runs : int
        Number of runs per task config (for statistical robustness).
    headless : bool
        Whether to run the browser headlessly.
    model : str
        OpenAI model to use.
    max_steps : int
        Maximum steps per task.

    Returns
    -------
    list[dict]
        List of result dicts from each run.
    """
    agent = WebAgent(model=model, max_steps=max_steps)
    results = []

    total = len(task_configs) * num_runs
    completed = 0

    for config in task_configs:
        task_id = config["task_id"]
        params = config.get("params", None)

        # Retrieve workflow if requested
        workflow_text = None
        if use_workflow:
            workflow_text = retrieve_workflow(task_type=task_id)
            if workflow_text:
                logger.info("Using workflow for %s", task_id)
            else:
                logger.info("No workflow available for %s", task_id)

        for run_num in range(1, num_runs + 1):
            completed += 1
            logger.info(
                "[%d/%d] Running %s (run %d/%d)%s",
                completed, total, task_id, run_num, num_runs,
                " WITH workflow" if workflow_text else "",
            )

            try:
                result = await agent.run(
                    task_id=task_id,
                    params=params,
                    workflow_text=workflow_text,
                    headless=headless,
                )
                result["run_num"] = run_num
                result["used_workflow"] = workflow_text is not None
                results.append(result)

                status = "✅" if result["success"] else "❌"
                logger.info(
                    "  %s %s — %d steps",
                    status, task_id, result["steps"],
                )
            except Exception as e:
                logger.error("  💥 %s failed: %s", task_id, e)
                results.append({
                    "task_id": task_id,
                    "params": params,
                    "success": False,
                    "steps": 0,
                    "trajectory": [],
                    "had_workflow": workflow_text is not None,
                    "used_workflow": workflow_text is not None,
                    "run_num": run_num,
                    "error": str(e),
                })

    return results


def save_results(results: list[dict], path: str) -> None:
    """Save experiment results to a JSON file."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    logger.info("Saved %d results to %s", len(results), path)


def load_results(path: str) -> list[dict]:
    """Load experiment results from a JSON file."""
    with open(path) as f:
        return json.load(f)
