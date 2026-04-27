"""utils/json_parser.py — Safely extracts JSON from LLM outputs."""
import json
import re


def extract_json(text: str) -> dict:
    """Attempts to find and parse a JSON object within a text string.

    Handles three common LLM output formats:
      1. JSON wrapped in markdown fences: ```json { ... } ```
      2. A raw JSON object anywhere in the text: { ... }
      3. The entire text is already valid JSON.

    Raises:
        ValueError: if no valid JSON object can be found or parsed.
    """
    if not text or not text.strip():
        raise ValueError("Empty response from model.")

    # 1. Try to extract from markdown code fences first
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        candidate = match.group(1)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass  # fall through to next strategy

    # 2. Find the outermost {...} block in the raw text
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass  # fall through to next strategy

    # 3. Try parsing the whole string as-is
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    raise ValueError(
        f"Could not extract valid JSON from model response. "
        f"Response preview: {text[:200]!r}"
    )
