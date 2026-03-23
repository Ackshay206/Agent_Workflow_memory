"""
Workflow store — save and load workflows as JSON files.

Workflows are stored in the `workflows/` directory, one file per workflow,
named  {task_type}_{id}.json .
"""

import json
import logging
import os
from typing import Optional

from .workflow import Workflow

logger = logging.getLogger(__name__)

DEFAULT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "workflows",
)


def save_workflow(workflow: Workflow, directory: str = DEFAULT_DIR) -> str:
    """Save a workflow to a JSON file.

    Returns the path of the saved file.
    """
    os.makedirs(directory, exist_ok=True)
    filename = f"{workflow.task_type}_{workflow.id}.json"
    path = os.path.join(directory, filename)

    with open(path, "w") as f:
        f.write(workflow.to_json())

    logger.info("Saved workflow to %s", path)
    return path


def load_workflows(
    task_type: Optional[str] = None,
    directory: str = DEFAULT_DIR,
) -> list[Workflow]:
    """Load workflows from the store.

    Parameters
    ----------
    task_type : str, optional
        If given, only load workflows matching this task type.
    directory : str
        Path to the workflows directory.

    Returns
    -------
    list[Workflow]
    """
    if not os.path.isdir(directory):
        return []

    workflows = []
    for filename in sorted(os.listdir(directory)):
        if not filename.endswith(".json"):
            continue

        # Optional task_type filter (filename starts with task_type_)
        if task_type and not filename.startswith(f"{task_type}_"):
            continue

        path = os.path.join(directory, filename)
        try:
            with open(path) as f:
                data = json.load(f)
            workflows.append(Workflow.from_dict(data))
        except Exception as e:
            logger.warning("Failed to load %s: %s", path, e)

    logger.info(
        "Loaded %d workflow(s)%s",
        len(workflows),
        f" for task_type={task_type}" if task_type else "",
    )
    return workflows


def load_all_workflows(directory: str = DEFAULT_DIR) -> list[Workflow]:
    """Load every workflow in the store."""
    return load_workflows(task_type=None, directory=directory)
