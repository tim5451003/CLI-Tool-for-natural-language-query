"""格式化 CLI 結果輸出（文字模式或 JSON 模式）。"""

import json
from typing import Any, Dict


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
