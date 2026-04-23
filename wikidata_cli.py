import argparse
import json
import logging
import re
import sys
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple

import requests


WIKIDATA_API = "https://www.wikidata.org/w/api.php"
WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
DEFAULT_HEADERS = {
    "User-Agent": "CMI-Tool-Baseline/0.2 (educational take-home; contact: local-cli)",
}
ALIAS_MAP = {
    "uk": "united kingdom",
    "usa": "united states of america",
    "us": "united states of america",
}
ENTITY_TYPE_QIDS = {
    "city": "Q515",
    "cities": "Q515",
    "mountain": "Q8502",
    "mountains": "Q8502",
    "river": "Q4022",
    "rivers": "Q4022",
    "country": "Q6256",
    "countries": "Q6256",
}
PROPERTY_PIDS = {
    "population": "P1082",
    "area": "P2046",
    "elevation": "P2044",
}


@dataclass
class ParsedQuery:
    intent: str
    entity_label: str = ""
    entity_type: str = ""
    location_label: str = ""
    property_name: str = ""
    limit: int = 5
    language: str = "en"

    def to_structured_request(self) -> Dict[str, Any]:
        return {
            "source": "wikidata",
            **asdict(self),
        }


def setup_logger(log_file: str) -> logging.Logger:
    logger = logging.getLogger("wdq")
    logger.handlers = []
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(file_handler)
    return logger


def log_event(logger: logging.Logger, stage: str, data: Dict[str, Any]) -> None:
    logger.info(json.dumps({"stage": stage, **data}, ensure_ascii=False))


def parse_nl_query(text: str, language: str) -> ParsedQuery:
    raw = text.strip()
    lowered = raw.lower().strip("?")

    patterns: List[Tuple[str, str]] = [
        ("capital_of", r"(?:what(?:'s| is) the capital of|capital of)\s+(.+)$"),
        ("population_of", r"(?:what(?:'s| is) the population of|population of)\s+(.+)$"),
        ("head_of_state", r"(?:who is the head of state of|head of state of)\s+(.+)$"),
        ("top_entities_by_property", r"top\s+(\d+)\s+(.+)\s+in\s+(.+)\s+by\s+(.+)$"),
        ("list_by_type_and_location", r"(?:list|show|find)\s+(.+)\s+in\s+(.+)$"),
        ("list_by_type_and_location", r"(.+)\s+in\s+(.+)$"),
        ("instance_of", r"(?:what is|define)\s+(.+)$"),
    ]

    for intent, pattern in patterns:
        match = re.search(pattern, lowered, flags=re.IGNORECASE)
        if not match:
            continue
        if intent in {"capital_of", "population_of", "head_of_state", "instance_of"}:
            return ParsedQuery(intent=intent, entity_label=match.group(1).strip(), language=language)
        if intent == "list_by_type_and_location":
            return ParsedQuery(
                intent=intent,
                entity_type=match.group(1).strip(),
                location_label=match.group(2).strip(),
                language=language,
            )
        if intent == "top_entities_by_property":
            return ParsedQuery(
                intent=intent,
                limit=int(match.group(1)),
                entity_type=match.group(2).strip(),
                location_label=match.group(3).strip(),
                property_name=match.group(4).strip(),
                language=language,
            )

    return ParsedQuery(intent="instance_of", entity_label=raw.strip(" ?"), language=language)


def search_entity_candidates(label: str, language: str = "en", limit: int = 5) -> List[Dict[str, Any]]:
    normalized = ALIAS_MAP.get(label.lower(), label)
    params = {
        "action": "wbsearchentities",
        "format": "json",
        "language": language,
        "search": normalized,
        "type": "item",
        "limit": limit,
    }
    response = requests.get(
        WIKIDATA_API,
        params=params,
        headers=DEFAULT_HEADERS,
        timeout=20,
    )
    response.raise_for_status()
    return response.json().get("search", [])


def resolve_entity(label: str, language: str = "en") -> Dict[str, Any]:
    candidates = search_entity_candidates(label, language=language, limit=5)
    if not candidates:
        return {"qid": None, "candidates": [], "ambiguous": False}

    exact_idx = None
    for i, candidate in enumerate(candidates):
        cand_label = candidate.get("label", "").lower()
        if cand_label == label.lower() or cand_label == ALIAS_MAP.get(label.lower(), "").lower():
            exact_idx = i
            break
    chosen = candidates[exact_idx] if exact_idx is not None else candidates[0]
    ambiguous = exact_idx is None and len(candidates) > 1
    return {
        "qid": chosen.get("id"),
        "chosen_label": chosen.get("label", ""),
        "candidates": [
            {"id": c.get("id"), "label": c.get("label"), "description": c.get("description", "")}
            for c in candidates[:3]
        ],
        "ambiguous": ambiguous,
    }


def build_sparql(parsed: ParsedQuery, resolved: Dict[str, Dict[str, Any]]) -> str:
    language = parsed.language
    if parsed.intent == "capital_of":
        return f"""
SELECT ?capital ?capitalLabel WHERE {{
  wd:{resolved["entity"]["qid"]} wdt:P36 ?capital .
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{language}". }}
}}
LIMIT 5
""".strip()
    if parsed.intent == "population_of":
        return f"""
SELECT ?population WHERE {{
  wd:{resolved["entity"]["qid"]} wdt:P1082 ?population .
}}
LIMIT 5
""".strip()
    if parsed.intent == "head_of_state":
        return f"""
SELECT ?head ?headLabel WHERE {{
  wd:{resolved["entity"]["qid"]} wdt:P35 ?head .
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{language}". }}
}}
LIMIT 5
""".strip()
    if parsed.intent == "list_by_type_and_location":
        type_qid = ENTITY_TYPE_QIDS.get(parsed.entity_type.lower(), "Q35120")
        return f"""
SELECT DISTINCT ?item ?itemLabel WHERE {{
  ?item wdt:P31/wdt:P279* wd:{type_qid} .
  ?item wdt:P17 wd:{resolved["location"]["qid"]} .
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{language}". }}
}}
LIMIT {parsed.limit}
""".strip()
    if parsed.intent == "top_entities_by_property":
        type_qid = ENTITY_TYPE_QIDS.get(parsed.entity_type.lower(), "Q35120")
        pid = PROPERTY_PIDS.get(parsed.property_name.lower(), "P1082")
        return f"""
SELECT DISTINCT ?item ?itemLabel ?metric WHERE {{
  ?item wdt:P31/wdt:P279* wd:{type_qid} .
  ?item wdt:P17 wd:{resolved["location"]["qid"]} .
  ?item wdt:{pid} ?metric .
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{language}". }}
}}
ORDER BY DESC(?metric)
LIMIT {parsed.limit}
""".strip()
    return f"""
SELECT ?type ?typeLabel WHERE {{
  wd:{resolved["entity"]["qid"]} wdt:P31 ?type .
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{language}". }}
}}
LIMIT 5
""".strip()


def run_sparql_query(sparql: str) -> Dict[str, Any]:
    headers = {**DEFAULT_HEADERS, "Accept": "application/sparql-results+json"}
    params = {"query": sparql, "format": "json"}
    response = requests.get(WIKIDATA_SPARQL, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def normalize_bindings(result_json: Dict[str, Any]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for row in result_json.get("results", {}).get("bindings", []):
        rows.append({key: value.get("value", "") for key, value in row.items()})
    return rows


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
    log_event(logger, "raw_input", {"query": args.query, "language": args.language})

    try:
        parsed = parse_nl_query(args.query, args.language)
        log_event(logger, "parsed_intent", {"intent": parsed.to_structured_request()})

        resolved: Dict[str, Dict[str, Any]] = {}
        if parsed.entity_label:
            resolved["entity"] = resolve_entity(parsed.entity_label, args.language)
            if not resolved["entity"]["qid"]:
                print(f'No Wikidata entity found for "{parsed.entity_label}".')
                return 2
        if parsed.location_label:
            resolved["location"] = resolve_entity(parsed.location_label, args.language)
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
            "structured_request": parsed.to_structured_request(),
            "resolved_entities": resolved,
            "sparql_query": sparql,
            "result_count": len(rows),
            "results": rows,
        }
        log_event(logger, "final_output", {"result_count": len(rows)})

        if args.json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            return 0

        if args.show_intent:
            print("Parsed intent:")
            print(json.dumps(payload["structured_request"], indent=2, ensure_ascii=False))
        print("Resolved entities:")
        print(json.dumps(payload["resolved_entities"], indent=2, ensure_ascii=False))
        if args.show_sparql:
            print("\nSPARQL:")
            print(payload["sparql_query"])
        print("\nResults:")
        if not rows:
            print("(no rows)")
        else:
            for i, row in enumerate(rows, start=1):
                print(f"{i}. {row}")
        return 0
    except requests.RequestException as exc:
        print(f"Network/API error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
