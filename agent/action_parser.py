"""
Parse the LLM's text response into structured think/action data.

Expected LLM output format:
    <think>
    ... reasoning ...
    </think>
    <action>
    click(search_btn)
    </action>

The action line is further parsed into:
    {"action_type": "click", "element_id": "search_btn", "value": None}
"""

import re


def parse_response(text: str) -> dict:
    """Parse an LLM response containing <think> and <action> blocks.

    Returns
    -------
    dict
        {
            "think": str,           # reasoning text
            "action": str,          # raw action string, e.g. 'click("btn")'
            "action_type": str,     # click | type | select | done
            "element_id": str|None, # HTML id of target element
            "value": str|None,      # value for type/select/done
            "error": str|None,      # non-None if parsing failed
        }
    """
    result = {
        "think": "",
        "action": "",
        "action_type": "",
        "element_id": None,
        "value": None,
        "error": None,
    }

    # --- Extract <think> block ---
    think_match = re.search(r"<think>(.*?)</think>", text, re.DOTALL)
    if think_match:
        result["think"] = think_match.group(1).strip()

    # --- Extract <action> block ---
    action_match = re.search(r"<action>(.*?)</action>", text, re.DOTALL)
    if not action_match:
        result["error"] = "No <action> block found in LLM response."
        return result

    raw_action = action_match.group(1).strip()
    result["action"] = raw_action

    # --- Parse the action call ---
    try:
        parsed = _parse_action_call(raw_action)
        result.update(parsed)
    except ValueError as e:
        result["error"] = str(e)

    return result


def _parse_action_call(raw: str) -> dict:
    """Parse a single action call like  click("search_btn")  or
    type("origin", "Boston")  into its components.

    Supports these forms:
        click(element_id)
        click("element_id")
        type(element_id, "value")
        type("element_id", "value")
        select(element_id, "value")
        select("element_id", "value")
        done("message")

    Returns dict with action_type, element_id, value.
    """
    # Normalise: strip outer whitespace and any trailing newlines
    raw = raw.strip()

    # Match:  action_name(  ...args...  )
    m = re.match(r"^(\w+)\((.*)\)$", raw, re.DOTALL)
    if not m:
        raise ValueError(f"Cannot parse action call: {raw!r}")

    action_type = m.group(1).lower()
    args_str = m.group(2).strip()

    if action_type == "click":
        element_id = _unquote(args_str)
        return {"action_type": "click", "element_id": element_id, "value": None}

    elif action_type in ("type", "fill"):
        parts = _split_args(args_str)
        if len(parts) < 2:
            raise ValueError(f"type() requires 2 arguments, got: {args_str!r}")
        element_id = _unquote(parts[0])
        value = _unquote(parts[1])
        return {"action_type": "type", "element_id": element_id, "value": value}

    elif action_type in ("select", "select_option"):
        parts = _split_args(args_str)
        if len(parts) < 2:
            raise ValueError(f"select() requires 2 arguments, got: {args_str!r}")
        element_id = _unquote(parts[0])
        value = _unquote(parts[1])
        return {"action_type": "select", "element_id": element_id, "value": value}

    elif action_type == "done":
        message = _unquote(args_str) if args_str else ""
        return {"action_type": "done", "element_id": None, "value": message}

    else:
        raise ValueError(f"Unknown action type: {action_type!r}")


def _unquote(s: str) -> str:
    """Remove surrounding quotes (single or double) from a string."""
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
        return s[1:-1]
    return s


def _split_args(args_str: str) -> list[str]:
    """Split a comma-separated argument string, respecting quoted values.

    Example: 'origin, "Boston"'  →  ['origin', '"Boston"']
    """
    parts = []
    current = []
    in_quote = None
    for ch in args_str:
        if ch in ('"', "'") and in_quote is None:
            in_quote = ch
            current.append(ch)
        elif ch == in_quote:
            in_quote = None
            current.append(ch)
        elif ch == "," and in_quote is None:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current).strip())
    return parts
