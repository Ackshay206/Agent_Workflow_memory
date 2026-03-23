"""
Workflow data class.

A Workflow captures a reusable, generalised sequence of steps extracted from
a successful agent trajectory.  Specific values (city names, dates, product
names) are replaced with descriptive variable placeholders so the workflow
can be applied to new task instances of the same type.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import json
import uuid


@dataclass
class Workflow:
    id: str                          # unique identifier
    task_type: str                   # "flight_search", "product_search", etc.
    description: str                 # one-line summary of what this workflow does
    steps: list[dict] = field(default_factory=list)
    # Each step: {"observation": str, "reasoning": str, "action": str}
    source_task: str = ""            # the original task instruction
    created_at: str = ""             # ISO timestamp

    def __post_init__(self):
        if not self.id:
            self.id = uuid.uuid4().hex[:8]
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    # -- Serialisation helpers --

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, d: dict) -> "Workflow":
        return cls(**d)

    @classmethod
    def from_json(cls, s: str) -> "Workflow":
        return cls.from_dict(json.loads(s))

    # -- Prompt-ready text representation --

    def to_prompt_text(self) -> str:
        """Format this workflow as text suitable for injection into the agent
        system prompt."""
        lines = [f"Workflow: {self.description}"]
        for i, step in enumerate(self.steps, 1):
            obs = step.get("observation", "")
            reason = step.get("reasoning", "")
            action = step.get("action", "")
            lines.append(f"\nStep {i}:")
            if obs:
                lines.append(f"  [page state] {obs}")
            if reason:
                lines.append(f"  [reasoning]  {reason}")
            if action:
                lines.append(f"  [action]     {action}")
        return "\n".join(lines)
