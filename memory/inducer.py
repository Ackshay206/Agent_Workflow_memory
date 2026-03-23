"""
Workflow inducer — extracts a reusable Workflow from a successful trajectory.

Takes the raw trajectory (list of step dicts from the agent run) and the task
instruction, sends them to an LLM, and parses the response into a Workflow
object with generalised variable placeholders.
"""

import json
import logging
import os
import re

from dotenv import load_dotenv
from openai import OpenAI

from .workflow import Workflow

load_dotenv()
logger = logging.getLogger(__name__)

INDUCTION_PROMPT = """\
You are an expert at extracting reusable workflows from web navigation traces.

Given a successful web navigation trajectory, extract a reusable workflow.

Rules:
- Replace specific values (city names, dates, product names, party sizes) \
with descriptive variable names like {{origin_city}}, {{departure_date}}, \
{{product_name}}, {{party_size}}.
- Keep element IDs as-is (e.g., "search_btn", "origin") since they are \
fixed in the website.
- Each step should describe: what the page looks like, why you take this \
action, and what action to take.
- The workflow should be generic enough to handle any instance of this task type.
- Keep the workflow at the right granularity — each step should be one \
meaningful action.

Task instruction: {task_instruction}

Trajectory:
{trajectory_text}

Respond in EXACTLY this JSON format (no other text):
{{
  "description": "One-line description of what this workflow does",
  "steps": [
    {{
      "observation": "What the current page shows",
      "reasoning": "Why you take this action",
      "action": "The action to take, with variable placeholders"
    }}
  ]
}}
"""


def format_trajectory_for_induction(trajectory: list[dict]) -> str:
    """Format a trajectory into readable text for the induction prompt."""
    lines = []
    for step in trajectory:
        step_num = step.get("step", "?")
        url = step.get("url", "")
        think = step.get("think", "")
        action = step.get("action", "")

        lines.append(f"--- Step {step_num} ---")
        lines.append(f"URL: {url}")
        if think:
            lines.append(f"Think: {think}")
        if action:
            lines.append(f"Action: {action}")
        lines.append("")

    return "\n".join(lines)


def induce_workflow(
    trajectory: list[dict],
    task_instruction: str,
    task_type: str,
    model: str = "gpt-4o-mini",
) -> Workflow:
    """Extract a Workflow from a successful trajectory using an LLM.

    Parameters
    ----------
    trajectory : list[dict]
        The step-by-step trajectory from a successful agent run.
    task_instruction : str
        The original task instruction (e.g., "Search for a flight from
        Boston to Chicago ...").
    task_type : str
        The task type key (e.g., "flight_search").
    model : str
        OpenAI model to use for induction.

    Returns
    -------
    Workflow
        A generalised, reusable workflow.
    """
    client = OpenAI()

    trajectory_text = format_trajectory_for_induction(trajectory)
    prompt = INDUCTION_PROMPT.format(
        task_instruction=task_instruction,
        trajectory_text=trajectory_text,
    )

    logger.info("Inducing workflow for task_type=%s ...", task_type)

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=2048,
    )

    raw_text = response.choices[0].message.content.strip()
    logger.info("LLM induction response received (%d chars)", len(raw_text))

    # Parse JSON from response (handle markdown code fences)
    json_str = raw_text
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", raw_text, re.DOTALL)
    if fence_match:
        json_str = fence_match.group(1).strip()

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse induction response as JSON: %s", e)
        logger.error("Raw response:\n%s", raw_text)
        # Fallback: create workflow from raw trajectory
        data = {
            "description": f"Workflow for {task_type} (auto-extracted)",
            "steps": [
                {
                    "observation": step.get("url", ""),
                    "reasoning": step.get("think", ""),
                    "action": step.get("action", ""),
                }
                for step in trajectory
                if step.get("action_type") != "done"
            ],
        }

    workflow = Workflow(
        id="",  # auto-generated
        task_type=task_type,
        description=data.get("description", ""),
        steps=data.get("steps", []),
        source_task=task_instruction,
    )

    logger.info(
        "Induced workflow id=%s: %s (%d steps)",
        workflow.id, workflow.description, len(workflow.steps),
    )
    return workflow
