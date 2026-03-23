"""
Workflow retriever — find and format relevant workflows for a new task.

For now uses simple task_type matching.  Can be extended later with
embedding-based similarity search.
"""

import logging
from typing import Optional

from .store import load_workflows
from .workflow import Workflow

logger = logging.getLogger(__name__)


def retrieve_workflow(
    task_type: str,
    task_instruction: Optional[str] = None,
) -> Optional[str]:
    """Retrieve the most relevant workflow for a task and return it as
    prompt-ready text.

    Parameters
    ----------
    task_type : str
        The type of task (e.g., "flight_search").
    task_instruction : str, optional
        The specific task instruction (reserved for future embedding-based
        retrieval).

    Returns
    -------
    str or None
        Formatted workflow text ready for injection into the agent system
        prompt, or None if no relevant workflow exists.
    """
    workflows = load_workflows(task_type=task_type)

    if not workflows:
        logger.info("No workflows found for task_type=%s", task_type)
        return None

    # For now, use the most recent workflow (last in sorted file list)
    best = workflows[-1]
    logger.info(
        "Retrieved workflow id=%s for task_type=%s: %s",
        best.id, task_type, best.description,
    )
    return best.to_prompt_text()


def retrieve_all_workflows_text(task_type: str) -> Optional[str]:
    """Retrieve ALL workflows for a task type and concatenate them.

    Useful when there are multiple complementary workflows for the same
    task type.
    """
    workflows = load_workflows(task_type=task_type)

    if not workflows:
        return None

    texts = [w.to_prompt_text() for w in workflows]
    return "\n\n---\n\n".join(texts)
