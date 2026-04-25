"""Prediction adapters for evaluation rounds.

Includes:
- local dry-run modes: oracle / naive
- real model modes:
  - openai_gpt4o_mini (closed-source)
  - anthropic_claude_3_5_haiku (closed-source)
  - together_llama_3_1_70b (open-weight model served by API)
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List

import requests


AVAILABLE_MODES = [
    "oracle",
    "naive",
    "openai_gpt4o_mini",
    "anthropic_claude_3_5_haiku",
    "together_llama_3_1_70b",
]


def _build_prompt(query: str) -> str:
    return f"""You are generating structured query JSON for a Wikidata CLI system.

Task:
- Convert the natural-language query into exactly one JSON object.
- Return JSON only. No markdown fences. No extra text.

Allowed status values:
1) "ok"
Required fields for status=ok:
- status
- normalized_query
- source (must be "wikidata")
- intent
- entity_label
- entity_type
- location_label
- property_name
- limit
- language

2) "needs_disambiguation"
Required fields:
- status
- normalized_query
- source
- intent
- disambiguation_target
- surface_form

3) "unsupported_or_underspecified"
Required fields:
- status
- normalized_query
- reason

4) "contradiction"
Required fields:
- status
- normalized_query
- reason

Natural language query:
{query}
"""


def _extract_json_object(text: str) -> Dict[str, Any]:
    s = text.strip()
    # Fast path: plain JSON
    try:
        obj = json.loads(s)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    # Try fenced markdown cleanup
    s = s.replace("```json", "").replace("```", "").strip()
    try:
        obj = json.loads(s)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    # Last resort: slice from first "{" to last "}"
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = s[start : end + 1]
        obj = json.loads(candidate)
        if isinstance(obj, dict):
            return obj
    raise ValueError("Model output is not valid JSON object")


def _post_json(url: str, headers: Dict[str, str], payload: Dict[str, Any]) -> Dict[str, Any]:
    resp = requests.post(url, headers=headers, json=payload, timeout=90)
    resp.raise_for_status()
    return resp.json()


def _predict_openai(query: str) -> Dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    body = {
        "model": "gpt-4o-mini",
        "temperature": 0,
        "messages": [
            {"role": "system", "content": "Return only valid JSON object."},
            {"role": "user", "content": _build_prompt(query)},
        ],
    }
    data = _post_json(
        "https://api.openai.com/v1/chat/completions",
        {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        body,
    )
    content = data["choices"][0]["message"]["content"]
    return _extract_json_object(content)


def _predict_anthropic(query: str) -> Dict[str, Any]:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    body = {
        "model": "claude-3-5-haiku-latest",
        "max_tokens": 1000,
        "temperature": 0,
        "system": "Return only valid JSON object.",
        "messages": [{"role": "user", "content": _build_prompt(query)}],
    }
    data = _post_json(
        "https://api.anthropic.com/v1/messages",
        {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        body,
    )
    parts: List[Dict[str, Any]] = data.get("content", [])
    text = "".join(p.get("text", "") for p in parts if p.get("type") == "text")
    return _extract_json_object(text)


def _predict_together_open_weight(query: str) -> Dict[str, Any]:
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        raise RuntimeError("TOGETHER_API_KEY is not set")
    body = {
        "model": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        "temperature": 0,
        "messages": [
            {"role": "system", "content": "Return only valid JSON object."},
            {"role": "user", "content": _build_prompt(query)},
        ],
    }
    data = _post_json(
        "https://api.together.xyz/v1/chat/completions",
        {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        body,
    )
    content = data["choices"][0]["message"]["content"]
    return _extract_json_object(content)


def predict_with_mode(mode: str, row: Dict[str, Any]) -> Dict[str, Any]:
    """Return a structured prediction for one query row.

    Modes:
    - oracle: return the exact ground truth (pipeline sanity check).
    - naive: intentionally weak baseline for dry-run testing.
    """
    gt = row["ground_truth_structured_query"]
    query = row["natural_language_query"].lower()

    if mode == "oracle":
        return dict(gt)

    if mode == "naive":
        # A deliberately weak heuristic baseline to test pipeline behavior.
        if "capital" in query:
            return {
                "status": "ok",
                "normalized_query": query,
                "source": "wikidata",
                "intent": "capital_of",
                "entity_label": query.replace("capital of", "").strip(),
                "entity_type": "",
                "location_label": "",
                "property_name": "",
                "limit": 5,
                "language": "en",
            }
        return {
            "status": "unsupported_or_underspecified",
            "normalized_query": query,
            "reason": "naive baseline fallback",
        }

    if mode == "openai_gpt4o_mini":
        return _predict_openai(row["natural_language_query"])

    if mode == "anthropic_claude_3_5_haiku":
        return _predict_anthropic(row["natural_language_query"])

    if mode == "together_llama_3_1_70b":
        return _predict_together_open_weight(row["natural_language_query"])

    raise ValueError(f"Unknown mode: {mode}. Available: {AVAILABLE_MODES}")

