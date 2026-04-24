"""主流程與 CLI 參數解析，串接 parser、resolver、SPARQL 與輸出格式化。"""

import argparse
import json
import sys
from typing import Any, Dict

import requests

from contradictions import check_contradictions
from formatter import print_contradiction, print_disambiguation, print_payload
from logging_utils import log_event, setup_logger
from normalize_nl import normalize_for_parse
from parser import parse_nl_query
from resolver import resolve_entity
from scope_checks import check_scope
from sparql_builder import build_sparql
from wikidata_client import normalize_bindings, run_sparql_query


def main() -> int:
    parser = argparse.ArgumentParser(description="Natural-language CLI query tool for Wikidata.")
    parser.add_argument("query", type=str, help="Natural language question")
    parser.add_argument("--language", default="en", help="Wikidata label language")
    parser.add_argument("--show-intent", action="store_true", help="Print parsed intent object")
    parser.add_argument("--show-sparql", action="store_true", help="Print generated SPARQL")
    parser.add_argument("--json", action="store_true", help="Print full structured output as JSON")
    parser.add_argument("--log-file", default="wdq.log", help="Path to JSON-lines execution log")
    args = parser.parse_args()

    logger = setup_logger(args.log_file)
    normalized = normalize_for_parse(args.query)
    log_event(
        logger,
        "raw_input",
        {"query": args.query, "normalized_query": normalized, "language": args.language},
    )

    try:
        contradiction = check_contradictions(normalized)
        if contradiction:
            log_event(logger, "contradiction", {"message": contradiction})
            print_contradiction(contradiction, args.json, structured_request=None)
            return 4

        parsed = parse_nl_query(normalized, args.language)
        log_event(logger, "parsed_intent", {"intent": parsed.to_structured_request()})

        scope_msg = check_scope(normalized, parsed)
        if scope_msg:
            log_event(logger, "scope_rejected", {"message": scope_msg})
            if args.json:
                print(
                    json.dumps(
                        {
                            "status": "unsupported_or_underspecified",
                            "message": scope_msg,
                            "structured_request": parsed.to_structured_request(),
                            "normalized_query": normalized,
                        },
                        indent=2,
                        ensure_ascii=False,
                    )
                )
            else:
                print(scope_msg, file=sys.stderr)
            return 2

        resolved: Dict[str, Dict[str, Any]] = {}
        structured = parsed.to_structured_request()

        if parsed.entity_label:
            resolved["entity"] = resolve_entity(parsed.entity_label, args.language, intent=parsed.intent)
            if resolved["entity"].get("needs_disambiguation"):
                log_event(logger, "disambiguation_required", {"field": "entity", "label": parsed.entity_label})
                print_disambiguation(
                    field="entity",
                    label=parsed.entity_label,
                    resolution=resolved["entity"],
                    structured_request=structured,
                    as_json=args.json,
                )
                return 3
            if not resolved["entity"]["qid"]:
                print(f'No Wikidata entity found for "{parsed.entity_label}".')
                return 2

        if parsed.location_label:
            resolved["location"] = resolve_entity(parsed.location_label, args.language, intent=parsed.intent)
            if resolved["location"].get("needs_disambiguation"):
                log_event(logger, "disambiguation_required", {"field": "location", "label": parsed.location_label})
                print_disambiguation(
                    field="location",
                    label=parsed.location_label,
                    resolution=resolved["location"],
                    structured_request=structured,
                    as_json=args.json,
                )
                return 3
            if not resolved["location"]["qid"]:
                print(f'No Wikidata location found for "{parsed.location_label}".')
                return 2

        log_event(logger, "resolved_entities", resolved)

        sparql = build_sparql(parsed, resolved)
        log_event(logger, "generated_query", {"sparql_query": sparql})

        raw_result = run_sparql_query(sparql)
        rows = normalize_bindings(raw_result)
        log_event(logger, "execution_result", {"row_count": len(rows)})

        payload = {
            "normalized_query": normalized,
            "structured_request": structured,
            "resolved_entities": resolved,
            "sparql_query": sparql,
            "result_count": len(rows),
            "results": rows,
        }
        log_event(logger, "final_output", {"result_count": len(rows)})
        print_payload(payload, as_json=args.json, show_intent=args.show_intent, show_sparql=args.show_sparql)
        return 0
    except requests.RequestException as exc:
        print(f"Network/API error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
