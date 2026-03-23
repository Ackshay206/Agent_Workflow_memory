# Project Context and Next Steps

## What This Project Is

This is a capstone project called "Workflow Memory for Tool-Using Web Agents." The core idea comes from the Agent Workflow Memory (AWM) paper: a web agent attempts tasks, and when it succeeds, the system extracts a reusable workflow from the trajectory. When a similar task comes later, the agent retrieves the relevant workflow and uses it as guidance, leading to higher success rates and fewer steps.

The novel contribution beyond AWM is that we plan to add execution guards (condition checks and fallback actions from the ReUseIt paper) to make workflows more robust — but that is a LATER step. For now, we are building the foundation: agent loop + workflow extraction + workflow retrieval.

## What Already Exists

The `environment/` folder contains a working simulated web environment:

- `environment/app.py` — FastAPI server serving real HTML pages on localhost:3000
- `environment/pages.py` — HTML templates for all pages (with proper CSS/format separation)
- `environment/tasks.py` — Task definitions with instruction templates and default params
- `environment/__init__.py` — Empty init

The environment has 3 task types, each with multiple pages forming a flow:
1. **Flight Search**: home form → results page → confirmation page
2. **Product Search**: home search → results (with sort) → product detail → cart confirmation  
3. **Restaurant Reservation**: home form → results → confirm → done

Each page has semantic HTML with IDs, labels, forms, links, and buttons. Pages use standard HTML form submissions (GET/POST) for navigation. Success is indicated by a page containing the text "✅ SUCCESS" in an element with id="done_message".

The server runs with: `python -m environment.app` (or `python environment/app.py`)

## Target Project Structure

```
workflow-memory-agent/
├── environment/              # ✅ DONE - simulated web environment
│   ├── __init__.py
│   ├── app.py
│   ├── pages.py
│   └── tasks.py
│
├── agent/                    # 🔨 BUILD THIS - Playwright-based web agent
│   ├── __init__.py
│   ├── base_agent.py         # Core agent loop: observe → LLM → act → repeat
│   ├── prompts.py            # System prompt, action format instructions
│   └── action_parser.py      # Parse LLM text output into executable actions
│
├── memory/                   # 🔨 BUILD THIS - Workflow memory system
│   ├── __init__.py
│   ├── workflow.py           # Workflow data class
│   ├── inducer.py            # Extract workflow from successful trajectory
│   ├── retriever.py          # Retrieve relevant workflow for new task
│   └── store.py              # Save/load workflows (JSON files)
│
├── evaluation/               # 🔨 BUILD THIS - Run experiments and measure
│   ├── __init__.py
│   ├── runner.py             # Run N tasks, collect results
│   └── metrics.py            # Success rate, avg steps
│
├── experiments/              # 🔨 BUILD THIS - Experiment scripts
│   ├── run_no_memory.py      # Baseline: agent without workflow memory
│   ├── run_with_workflow.py  # Agent with workflow retrieval
│   └── compare.py            # Compare conditions, print results table
│
├── workflows/                # Auto-generated at runtime
│   └── .gitkeep
│
├── logs/                     # Trajectory logs per run
│   └── .gitkeep
│
├── .env                      # OPENAI_API_KEY=sk-...
└── requirements.txt          # playwright, openai, fastapi, uvicorn, numpy
```

## What To Build — In This Exact Order

### Phase 1: The Agent Loop (agent/)

Build a Playwright-based web agent that can navigate the FastAPI environment.

**agent/prompts.py**

Create the system prompt and action format. The system prompt should tell the LLM:
- You are a web navigation agent
- You see an accessibility tree of the current page
- You must output ONE action per turn in a specific format
- Available actions: `click(element_id)`, `type(element_id, "value")`, `select(element_id, "value")`, `done(message)`
- You should think step by step before acting

The action format should be:
```
<think>
[Your reasoning about what to do next based on the page state and task]
</think>
<action>
click(search_btn)
</action>
```

This matches AWM's format. Also create a function that builds the user message for each step, containing:
- The task instruction
- The current page URL
- The accessibility tree of the current page
- The action history so far (previous think/action pairs)
- Optionally: a workflow if one was retrieved (for Phase 2)

**agent/action_parser.py**

Parse the LLM's text response to extract:
- The think block (text between `<think>` and `</think>`)
- The action block (text between `<action>` and `</action>`)
- From the action block, parse into: action_type, element_id, and optional value
- Handle these formats: `click(element_id)`, `type(element_id, "value")`, `select(element_id, "value")`, `done("message")`
- Return a structured dict like: `{"action_type": "type", "element_id": "origin", "value": "Boston"}`
- Handle parsing errors gracefully — if the LLM outputs something unparseable, return an error dict

**agent/base_agent.py**

This is the core agent loop. It should:

1. Launch Playwright (chromium, headless=False for debugging, headless=True for batch runs)
2. Navigate to the task's start URL
3. Extract the accessibility tree from the current page using Playwright's `page.accessibility.snapshot()` 
4. Format the accessibility tree into a readable text representation (filter to interactive elements: buttons, links, textboxes, selects, etc. Include their role, name, and id attributes)
5. Build the prompt with the task instruction + current page state + action history
6. Call the LLM (use OpenAI's API with gpt-4o-mini for cost efficiency)
7. Parse the response to get the action
8. Execute the action via Playwright:
   - `click(id)` → find element by id attribute, then click it
   - `type(id, value)` → find element by id, clear it, then type the value
   - `select(id, value)` → find the select element by id, select the option with matching value
   - `done(message)` → stop the loop
9. Log the step: {page_url, accessibility_tree, think, action, result}
10. Check if we've reached a success page (page contains "✅ SUCCESS") or hit max steps (15)
11. Repeat from step 3

Important implementation details:
- Use `page.locator(f"#{element_id}")` to find elements by their HTML id attribute
- After each action, wait for page to stabilize: `page.wait_for_load_state("networkidle")` or a short sleep
- The accessibility tree from Playwright returns a nested dict — flatten it into a text list showing each interactive element
- Store the full trajectory as a list of step dicts for later workflow extraction
- The agent should accept an optional `workflow_text` parameter that gets injected into the system prompt (for Phase 2)
- Use python-dotenv to load the API key from .env

The agent's run method signature should look like:
```python
async def run(self, task_id: str, params: dict = None, workflow_text: str = None, headless: bool = True) -> dict:
    """
    Returns: {
        "task_id": str,
        "params": dict,
        "success": bool,
        "steps": int,
        "trajectory": list[dict],  # each step's observation + think + action
        "had_workflow": bool,
    }
    """
```

### Phase 2: Workflow Memory (memory/)

**memory/workflow.py**

Define a simple Workflow dataclass:
```python
@dataclass
class Workflow:
    id: str                    # unique identifier
    task_type: str             # "flight_search", "product_search", etc.
    description: str           # what this workflow does (natural language)
    steps: list[dict]          # list of {observation_summary, reasoning, action}
    source_task: str           # the task instruction it was extracted from
    created_at: str            # timestamp
```

**memory/inducer.py**

This takes a successful trajectory and produces a Workflow. It should:

1. Accept a trajectory (list of step dicts from the agent run) and the task instruction
2. Send the trajectory to the LLM with this prompt (adapted from AWM's Appendix A):

```
Given this successful web navigation trajectory, extract a reusable workflow.

Rules:
- Replace specific values (city names, dates, product names) with descriptive variable names like {origin_city}, {departure_date}, {product_name}
- Each step should describe: what the page looks like, why you take this action, and what action to take
- The workflow should be a commonly reusable sub-routine, not tied to one specific task instance
- Keep the workflow at the right granularity — each step should be one meaningful action

Task instruction: [the original task]

Trajectory:
[formatted trajectory with observation + think + action for each step]

Output a workflow with:
1. A one-line description of what this workflow does
2. A series of steps, each formatted as:
   [page state] Description of what the current page shows
   [reasoning] Why you take this action
   [action] The action to take, with variable placeholders
```

3. Parse the LLM's response into a Workflow object
4. Return the Workflow

**memory/store.py**

Simple JSON-based storage:
- `save_workflow(workflow: Workflow)` → saves to `workflows/{task_type}_{id}.json`
- `load_workflows(task_type: str = None)` → loads all workflows, optionally filtered by task type
- `load_all_workflows()` → loads everything

**memory/retriever.py**

For now, keep retrieval simple (you can make it fancier later):
- Given a task instruction and task_type, load all workflows for that task_type
- If workflows exist, format them as text to inject into the agent's prompt
- The format should match AWM's approach: just concatenate the workflow descriptions and steps as text
- Later you can add embedding-based retrieval, but task_type matching is fine for the midterm

The retriever should output a string that gets passed to `base_agent.run(workflow_text=...)`.

### Phase 3: Experiments and Evaluation (experiments/, evaluation/)

**evaluation/runner.py**

A function that runs multiple tasks and collects results:
```python
async def run_experiment(
    agent,
    task_configs: list[dict],   # list of {"task_id": ..., "params": ...}
    workflow_text: str = None,   # optional workflow to inject
    num_runs: int = 3,           # runs per task config
    headless: bool = True,
) -> list[dict]:
    """Run all tasks, return list of result dicts."""
```

**evaluation/metrics.py**

Compute from a list of results:
- Success rate (% of runs where success=True)
- Average steps on successful runs
- Average steps on all runs
- Per-task-type breakdown

**experiments/run_no_memory.py**

1. Start the Flask server (or assume it's running)
2. Define task configs — use default params AND varied params for each task type:
   - flight_search with (Boston→Chicago), (NYC→LA), (Denver→Seattle)  
   - product_search with (wireless headphones), (running shoes), (coffee maker)
   - restaurant_reservation with (New York), (San Francisco), (Chicago)
3. Run all tasks with NO workflow memory (workflow_text=None)
4. Save results to logs/no_memory_results.json
5. Print success rate and avg steps

**experiments/run_with_workflow.py**

1. Load results from the no-memory run
2. For each successful trajectory, run the inducer to extract a workflow
3. Save the workflows
4. Run the SAME task configs again, but this time retrieve and inject workflows
5. Save results to logs/with_workflow_results.json
6. Print success rate and avg steps

**experiments/compare.py**

Load both result files and print a comparison table:
```
Condition         | Success Rate | Avg Steps (success) | Avg Steps (all)
No Memory         |    66.7%     |       8.2           |     11.4
With Workflow     |    88.9%     |       5.1           |      6.3
```

Also break down by task type.

## Technical Notes

- Use `openai` Python package with `AsyncOpenAI` client for the LLM calls
- Use `playwright.async_api` for browser automation
- Model: `gpt-4o-mini` (cheap, fast, good enough for this)
- The Flask/FastAPI server must be running separately when you run experiments
- All async code should use `asyncio.run()` at the entry point
- Add proper error handling — LLM calls can fail, Playwright can timeout, elements might not be found
- Log everything to files in the logs/ directory for debugging

## What NOT To Build Yet

- Execution guards (condition checks, fallback actions) — that's the next phase
- Embedding-based retrieval — simple task_type matching is fine
- A frontend/UI for the agent — terminal output is fine
- Integration with real websites or BrowserGym — stay on local Flask
- Workflow composition (chaining simple workflows into complex ones)

## Requirements File

```
fastapi
uvicorn
playwright
openai
python-dotenv
numpy
```

After installing, run `playwright install chromium` to get the browser.