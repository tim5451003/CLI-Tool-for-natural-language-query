"""格式化 CLI 結果輸出（文字模式或 JSON 模式）。"""

import json
import sys
from typing import Any, Dict, Optional


def print_payload(payload: Dict[str, Any], as_json: bool, show_intent: bool, show_sparql: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    if show_intent:
        print("Parsed intent:")
        print(json.dumps(payload["structured_request"], indent=2, ensure_ascii=False))
    print("Resolved entities:")
    print(json.dumps(payload["resolved_entities"], indent=2, ensure_ascii=False))
    if show_sparql:
        print("\nSPARQL:")
        print(payload["sparql_query"])
    print("\nResults:")
    if not payload["results"]:
        print("(no rows)")
    else:
        for i, row in enumerate(payload["results"], start=1):
            print(f"{i}. {row}")


def print_disambiguation(
    *,
    field: str,
    label: str,
    resolution: Dict[str, Any],
    structured_request: Dict[str, Any],
    as_json: bool,
) -> None:
    """當實體無法唯一解析時，輸出候選清單（不執行 SPARQL）。"""
    payload = {
        "status": "needs_disambiguation",
        "field": field,
        "surface_form": label,
        "structured_request": structured_request,
        "resolution": resolution,
    }
    if as_json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    print("Ambiguous entity — please disambiguate before running a query.", file=sys.stderr)
    print(f"Surface form: {label!r} (role: {field})", file=sys.stderr)
    print("Candidates:", file=sys.stderr)
    for i, c in enumerate(resolution.get("candidates") or [], start=1):
        desc = c.get("description") or ""
        print(f"  {i}. {c.get('id')} — {c.get('label')} — {desc}", file=sys.stderr)


def print_contradiction(message: str, as_json: bool, structured_request: Optional[Dict[str, Any]] = None) -> None:
    if as_json:
        print(
            json.dumps(
                {"status": "contradiction", "message": message, "structured_request": structured_request},
                indent=2,
                ensure_ascii=False,
            )
        )
        return
    print(f"Contradiction: {message}", file=sys.stderr)
