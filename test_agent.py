"""Quick test: run the agent on a single flight_search task with visible browser."""

import asyncio
import logging
from agent.base_agent import WebAgent

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")


async def main():
    agent = WebAgent(model="gpt-4o-mini", max_steps=15)
    print("=" * 60)
    print("Testing: flight_search (Boston → Chicago)")
    print("=" * 60)

    result = await agent.run(
        task_id="flight_search",
        headless=False,  # visible browser
    )

    print()
    print("=" * 60)
    print(f"Success: {result['success']}")
    print(f"Steps:   {result['steps']}")
    print("=" * 60)

    # Print trajectory summary
    for step in result["trajectory"]:
        s = step.get("step", "?")
        act = step.get("action", "")
        think = step.get("think", "")[:80]
        print(f"\n--- Step {s} ---")
        print(f"Think: {think}...")
        print(f"Action: {act}")
        if step.get("error"):
            print(f"ERROR: {step['error']}")
        if step.get("exec_error"):
            print(f"EXEC ERROR: {step['exec_error']}")


if __name__ == "__main__":
    asyncio.run(main())
