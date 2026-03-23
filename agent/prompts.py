"""
Prompt templates for the web navigation agent.

- SYSTEM_PROMPT: static system message describing the agent's role, action
  format, and available actions.
- build_user_message(): constructs the per-step user message containing the
  task instruction, page state, action history, and optional workflow.
"""


SYSTEM_PROMPT = """\
You are a web navigation agent. Your goal is to complete tasks on websites by \
interacting with page elements.

# What You See
Each turn you receive:
- The task to accomplish
- The current page URL
- An accessibility tree listing every interactive element on the page \
(buttons, links, text fields, selects, etc.) with its role, name, and id

# How You Respond
You MUST respond with exactly two XML blocks — a think block and an action block:

<think>
[Step-by-step reasoning about the current page state, what you have done so \
far, and what you should do next]
</think>
<action>
[Exactly ONE action call from the list below]
</action>

# Available Actions
- click(element_id)              Click the element with the given id
- type(element_id, "value")      Clear the field, then type the value
- select(element_id, "value")    Choose an option in a dropdown
- done("message")                Declare the task finished

Rules:
- Emit exactly ONE action per turn.
- The element_id is the HTML id attribute shown in the accessibility tree.
- Always wrap string arguments in double quotes.
- If the page contains "✅ SUCCESS", the task is complete — call done().
- If you are stuck after several attempts, call done("FAILED: <reason>").
"""


WORKFLOW_INJECTION_TEMPLATE = """\

# Relevant Workflow
The following workflow was extracted from a previously successful execution \
of a similar task. Use it as a guide, but adapt to the current page state.

{workflow_text}
"""


def build_user_message(
    task_instruction: str,
    page_url: str,
    accessibility_tree: str,
    action_history: list[dict] | None = None,
    workflow_text: str | None = None,
) -> str:
    """Build the user message for one agent step.

    Parameters
    ----------
    task_instruction : str
        Natural-language description of the task.
    page_url : str
        Current browser URL.
    accessibility_tree : str
        Flattened text representation of interactive page elements.
    action_history : list[dict], optional
        Previous steps, each with 'think' and 'action' keys.
    workflow_text : str, optional
        A workflow retrieved from memory to guide the agent.

    Returns
    -------
    str
        The fully assembled user message.
    """
    parts: list[str] = []

    # Task instruction
    parts.append(f"# Task\n{task_instruction}")

    # Workflow (if provided)
    if workflow_text:
        parts.append(WORKFLOW_INJECTION_TEMPLATE.format(workflow_text=workflow_text))

    # Action history
    if action_history:
        history_lines = ["# Action History"]
        for i, step in enumerate(action_history, 1):
            history_lines.append(f"\n## Step {i}")
            history_lines.append(f"<think>\n{step['think']}\n</think>")
            history_lines.append(f"<action>\n{step['action']}\n</action>")
        parts.append("\n".join(history_lines))

    # Current page state
    parts.append(f"# Current Page\nURL: {page_url}")
    parts.append(f"# Accessibility Tree\n{accessibility_tree}")

    return "\n\n".join(parts)
