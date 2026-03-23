"""
Evaluation metrics — compute success rates, step counts, and breakdowns.
"""

from collections import defaultdict


def compute_metrics(results: list[dict]) -> dict:
    """Compute aggregate metrics from experiment results.

    Returns
    -------
    dict
        {
            "total_runs": int,
            "successes": int,
            "failures": int,
            "success_rate": float,      # 0.0 – 1.0
            "avg_steps_all": float,
            "avg_steps_success": float,
            "avg_steps_failure": float,
            "per_task": { task_id: { same structure } },
        }
    """
    if not results:
        return {"total_runs": 0, "success_rate": 0.0}

    total = len(results)
    successes = [r for r in results if r.get("success")]
    failures = [r for r in results if not r.get("success")]

    all_steps = [r["steps"] for r in results if r.get("steps", 0) > 0]
    success_steps = [r["steps"] for r in successes if r.get("steps", 0) > 0]
    failure_steps = [r["steps"] for r in failures if r.get("steps", 0) > 0]

    metrics = {
        "total_runs": total,
        "successes": len(successes),
        "failures": len(failures),
        "success_rate": len(successes) / total if total else 0.0,
        "avg_steps_all": _avg(all_steps),
        "avg_steps_success": _avg(success_steps),
        "avg_steps_failure": _avg(failure_steps),
    }

    # Per-task breakdown
    by_task = defaultdict(list)
    for r in results:
        by_task[r["task_id"]].append(r)

    metrics["per_task"] = {}
    for task_id, task_results in sorted(by_task.items()):
        t_total = len(task_results)
        t_succ = [r for r in task_results if r.get("success")]
        t_s_steps = [r["steps"] for r in t_succ if r.get("steps", 0) > 0]
        t_all_steps = [r["steps"] for r in task_results if r.get("steps", 0) > 0]

        metrics["per_task"][task_id] = {
            "total_runs": t_total,
            "successes": len(t_succ),
            "success_rate": len(t_succ) / t_total if t_total else 0.0,
            "avg_steps_all": _avg(t_all_steps),
            "avg_steps_success": _avg(t_s_steps),
        }

    return metrics


def format_metrics(metrics: dict, label: str = "Results") -> str:
    """Format metrics into a human-readable table string."""
    lines = []
    lines.append(f"\n{'=' * 65}")
    lines.append(f"  {label}")
    lines.append(f"{'=' * 65}")
    lines.append(
        f"  Total runs: {metrics['total_runs']}  |  "
        f"Success: {metrics['successes']}  |  "
        f"Failure: {metrics['failures']}"
    )
    lines.append(
        f"  Success rate: {metrics['success_rate']:.1%}"
    )
    lines.append(
        f"  Avg steps (all): {metrics['avg_steps_all']:.1f}  |  "
        f"Avg steps (success): {metrics['avg_steps_success']:.1f}  |  "
        f"Avg steps (failure): {metrics['avg_steps_failure']:.1f}"
    )

    if "per_task" in metrics and metrics["per_task"]:
        lines.append(f"\n  {'Task Type':<25} {'Success Rate':>12} {'Avg Steps':>10} {'Runs':>6}")
        lines.append(f"  {'-' * 55}")
        for task_id, tm in metrics["per_task"].items():
            lines.append(
                f"  {task_id:<25} {tm['success_rate']:>11.1%} "
                f"{tm['avg_steps_all']:>10.1f} {tm['total_runs']:>6}"
            )

    lines.append(f"{'=' * 65}\n")
    return "\n".join(lines)


def format_comparison(
    metrics_a: dict, label_a: str,
    metrics_b: dict, label_b: str,
) -> str:
    """Format a side-by-side comparison of two experiment conditions."""
    lines = []
    lines.append(f"\n{'=' * 70}")
    lines.append("  COMPARISON")
    lines.append(f"{'=' * 70}")
    lines.append(
        f"  {'Condition':<20} {'Success Rate':>12} {'Steps (success)':>16} {'Steps (all)':>12}"
    )
    lines.append(f"  {'-' * 62}")

    for label, m in [(label_a, metrics_a), (label_b, metrics_b)]:
        lines.append(
            f"  {label:<20} {m['success_rate']:>11.1%} "
            f"{m['avg_steps_success']:>16.1f} "
            f"{m['avg_steps_all']:>12.1f}"
        )

    lines.append(f"\n  Per-Task Breakdown:")
    all_tasks = sorted(
        set(list(metrics_a.get("per_task", {}).keys()) +
            list(metrics_b.get("per_task", {}).keys()))
    )
    for task_id in all_tasks:
        lines.append(f"\n  {task_id}:")
        for label, m in [(label_a, metrics_a), (label_b, metrics_b)]:
            tm = m.get("per_task", {}).get(task_id, {})
            sr = tm.get("success_rate", 0)
            avs = tm.get("avg_steps_all", 0)
            lines.append(f"    {label:<18} {sr:>11.1%} {avs:>10.1f} steps")

    lines.append(f"{'=' * 70}\n")
    return "\n".join(lines)


def _avg(values: list) -> float:
    return sum(values) / len(values) if values else 0.0
