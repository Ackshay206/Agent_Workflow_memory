"""
Core web navigation agent.

Uses Playwright to browse the FastAPI environment and an LLM (GPT-4o-mini)
to decide which actions to take.  The main entry point is:

    agent = WebAgent()
    result = await agent.run("flight_search", params={...})
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from openai import AsyncOpenAI
from playwright.async_api import async_playwright

from .action_parser import parse_response
from .prompts import SYSTEM_PROMPT, WORKFLOW_INJECTION_TEMPLATE, build_user_message

load_dotenv()

logger = logging.getLogger(__name__)

# Base URL for the simulated environment
BASE_URL = os.getenv("BASE_URL", "http://localhost:3000")

# Task definitions
# Add the project root so we can import 'environment' as a top-level package
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from environment.tasks import TASKS

# Map task_id → start URL path
TASK_START_URLS = {
    "flight_search": "/flights",
    "product_search": "/shop",
    "restaurant_reservation": "/restaurant",
}


class WebAgent:
    """Playwright + LLM web navigation agent."""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        max_steps: int = 15,
    ):
        self.model = model
        self.max_steps = max_steps
        self.client = AsyncOpenAI()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run(
        self,
        task_id: str,
        params: dict | None = None,
        workflow_text: str | None = None,
        headless: bool = True,
    ) -> dict:
        """Run a single task end-to-end.

        Returns
        -------
        dict
            task_id, params, success, steps, trajectory, had_workflow
        """
        # Resolve task config
        task_cfg = TASKS[task_id]
        merged_params = {**task_cfg["default_params"], **(params or {})}
        instruction = task_cfg["instruction"].format(**merged_params)
        start_url = BASE_URL + TASK_START_URLS[task_id]

        # Build system prompt (with optional workflow)
        sys_prompt = SYSTEM_PROMPT
        if workflow_text:
            sys_prompt += WORKFLOW_INJECTION_TEMPLATE.format(workflow_text=workflow_text)

        trajectory: list[dict] = []
        success = False

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=headless)
            page = await browser.new_page()

            try:
                await page.goto(start_url, wait_until="networkidle")

                for step_num in range(1, self.max_steps + 1):
                    # 1. Observe
                    page_url = page.url
                    ax_tree = await self._get_accessibility_tree(page)

                    # 2. Build prompt
                    user_msg = build_user_message(
                        task_instruction=instruction,
                        page_url=page_url,
                        accessibility_tree=ax_tree,
                        action_history=trajectory,
                        workflow_text=None,  # already in sys prompt
                    )

                    # 3. Call LLM
                    llm_response = await self._call_llm(sys_prompt, user_msg)

                    # 4. Parse
                    parsed = parse_response(llm_response)
                    logger.info(
                        "Step %d | action=%s id=%s val=%s",
                        step_num,
                        parsed["action_type"],
                        parsed["element_id"],
                        parsed.get("value", ""),
                    )

                    # 5. Record trajectory step
                    step_record = {
                        "step": step_num,
                        "url": page_url,
                        "accessibility_tree": ax_tree,
                        "think": parsed["think"],
                        "action": parsed["action"],
                        "action_type": parsed["action_type"],
                        "element_id": parsed["element_id"],
                        "value": parsed.get("value"),
                        "error": parsed.get("error"),
                    }
                    trajectory.append(step_record)

                    # 6. Handle parse errors
                    if parsed["error"]:
                        logger.warning("Parse error: %s", parsed["error"])
                        continue

                    # 7. Execute action
                    if parsed["action_type"] == "done":
                        # Check if we actually reached a success page
                        content = await page.content()
                        if "SUCCESS" in content:
                            success = True
                        break

                    exec_error = await self._execute_action(page, parsed)
                    if exec_error:
                        step_record["exec_error"] = exec_error
                        logger.warning("Exec error: %s", exec_error)

                    # 8. Wait for page to settle
                    try:
                        await page.wait_for_load_state("networkidle", timeout=5000)
                    except Exception:
                        await asyncio.sleep(1)

                    # 9. Check for success after navigation
                    content = await page.content()
                    if "SUCCESS" in content:
                        success = True
                        # Record the final observation
                        trajectory.append({
                            "step": step_num + 0.5,
                            "url": page.url,
                            "think": "Page shows SUCCESS message.",
                            "action": 'done("Task completed successfully")',
                            "action_type": "done",
                            "element_id": None,
                            "value": "Task completed successfully",
                        })
                        break

            finally:
                await browser.close()

        result = {
            "task_id": task_id,
            "params": merged_params,
            "instruction": instruction,
            "success": success,
            "steps": len(trajectory),
            "trajectory": trajectory,
            "had_workflow": workflow_text is not None,
            "model": self.model,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Save trajectory to logs
        self._save_log(result)

        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _call_llm(self, system_prompt: str, user_message: str) -> str:
        """Call the OpenAI API and return the assistant's text."""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.2,
            max_tokens=1024,
        )
        return response.choices[0].message.content

    async def _get_accessibility_tree(self, page) -> str:
        """Extract interactive elements from the DOM with their HTML ids.

        Uses JavaScript to walk the DOM and collect every interactive element
        that the agent might need to interact with, including its tag, type,
        id, name/label text, and current value.
        """
        try:
            elements = await page.evaluate("""() => {
                const results = [];
                const interactiveTags = new Set([
                    'A', 'BUTTON', 'INPUT', 'SELECT', 'TEXTAREA', 'OPTION'
                ]);
                const all = document.querySelectorAll('*');
                for (const el of all) {
                    const tag = el.tagName;
                    // Include interactive elements and headings
                    const isInteractive = interactiveTags.has(tag);
                    const isHeading = /^H[1-6]$/.test(tag);
                    const isLabel = tag === 'LABEL';
                    if (!isInteractive && !isHeading && !isLabel) continue;

                    const info = { tag: tag.toLowerCase() };
                    if (el.id) info.id = el.id;
                    if (el.type) info.type = el.type;

                    // Get visible text or label
                    if (isHeading || isLabel) {
                        info.text = el.textContent.trim().substring(0, 100);
                    } else if (tag === 'A') {
                        info.text = el.textContent.trim().substring(0, 100);
                        info.href = el.getAttribute('href') || '';
                    } else if (tag === 'BUTTON') {
                        info.text = el.textContent.trim().substring(0, 100);
                    } else if (tag === 'INPUT') {
                        info.value = el.value || '';
                        info.placeholder = el.placeholder || '';
                    } else if (tag === 'SELECT') {
                        info.value = el.value || '';
                        // List options
                        const opts = Array.from(el.options).map(o => o.value);
                        info.options = opts.slice(0, 20);
                    } else if (tag === 'TEXTAREA') {
                        info.value = el.value || '';
                        info.placeholder = el.placeholder || '';
                    } else if (tag === 'OPTION') {
                        // Skip individual options; they are listed in SELECT
                        continue;
                    }

                    results.push(info);
                }
                return results;
            }""")
        except Exception as e:
            logger.warning("DOM extraction failed: %s", e)
            return "(accessibility tree unavailable)"

        if not elements:
            return "(no interactive elements found)"

        lines: list[str] = []
        for el in elements:
            tag = el.get("tag", "")
            el_id = el.get("id", "")
            text = el.get("text", "")
            value = el.get("value", "")
            placeholder = el.get("placeholder", "")
            el_type = el.get("type", "")
            href = el.get("href", "")
            options = el.get("options", [])

            # Format based on element type
            if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
                lines.append(f"[{tag}] {text}")
            elif tag == "label":
                lines.append(f"[label] {text}")
            elif tag == "a":
                id_str = f" id={el_id}" if el_id else ""
                lines.append(f"[link{id_str}] {text} → {href}")
            elif tag == "button":
                id_str = f" id={el_id}" if el_id else ""
                lines.append(f"[button{id_str}] {text}")
            elif tag == "input":
                id_str = f" id={el_id}" if el_id else ""
                val_info = f" value=\"{value}\"" if value else ""
                ph_info = f" placeholder=\"{placeholder}\"" if placeholder else ""
                lines.append(f"[input type={el_type}{id_str}{val_info}{ph_info}]")
            elif tag == "select":
                id_str = f" id={el_id}" if el_id else ""
                opts_str = ", ".join(options[:10])
                lines.append(f"[select{id_str} value=\"{value}\"] options: [{opts_str}]")
            elif tag == "textarea":
                id_str = f" id={el_id}" if el_id else ""
                lines.append(f"[textarea{id_str}] {value or placeholder}")

        return "\n".join(lines)

    async def _execute_action(self, page, parsed: dict) -> str | None:
        """Execute a parsed action on the page. Returns error string or None."""
        action_type = parsed["action_type"]
        element_id = parsed["element_id"]
        value = parsed.get("value", "")

        try:
            if action_type == "click":
                locator = page.locator(f"#{element_id}")
                await locator.click(timeout=5000)

            elif action_type == "type":
                locator = page.locator(f"#{element_id}")
                await locator.fill(value, timeout=5000)

            elif action_type == "select":
                locator = page.locator(f"#{element_id}")
                await locator.select_option(value=value, timeout=5000)

            elif action_type == "done":
                pass  # handled by caller

            else:
                return f"Unknown action type: {action_type}"

        except Exception as e:
            return f"{action_type}({element_id}): {e}"

        return None

    def _save_log(self, result: dict) -> None:
        """Save the run result to a JSON log file."""
        os.makedirs("logs", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        task_id = result["task_id"]
        path = f"logs/{task_id}_{timestamp}.json"
        with open(path, "w") as f:
            json.dump(result, f, indent=2, default=str)
        logger.info("Saved log to %s", path)
