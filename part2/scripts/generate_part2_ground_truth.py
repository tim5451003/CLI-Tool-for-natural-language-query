"""Generate manually-defined ground truth structured outputs for Part 2."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List


def load_queries(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def gt_ok(
    *,
    normalized_query: str,
    intent: str,
    entity_label: str = "",
    entity_type: str = "",
    location_label: str = "",
    property_name: str = "",
    limit: int = 5,
    language: str = "en",
) -> Dict[str, Any]:
    return {
        "status": "ok",
        "normalized_query": normalized_query,
        "source": "wikidata",
        "intent": intent,
        "entity_label": entity_label,
        "entity_type": entity_type,
        "location_label": location_label,
        "property_name": property_name,
        "limit": limit,
        "language": language,
    }


def build_ground_truth_map() -> Dict[str, Dict[str, Any]]:
    return {
        "C01": gt_ok(normalized_query="capital of japan", intent="capital_of", entity_label="japan"),
        "C02": gt_ok(
            normalized_query="population of france",
            intent="population_of",
            entity_label="france",
        ),
        "C03": gt_ok(
            normalized_query="who is the head of state of canada",
            intent="head_of_state",
            entity_label="canada",
        ),
        "C04": gt_ok(normalized_query="capital of germany", intent="capital_of", entity_label="germany"),
        "C05": gt_ok(
            normalized_query="top 10 cities in germany by population",
            intent="top_entities_by_property",
            entity_type="cities",
            location_label="germany",
            property_name="population",
            limit=10,
        ),
        "C06": gt_ok(
            normalized_query="top 5 cities in japan by population",
            intent="top_entities_by_property",
            entity_type="cities",
            location_label="japan",
            property_name="population",
            limit=5,
        ),
        "T01": gt_ok(
            normalized_query="population of japan",
            intent="population_of",
            entity_label="japan",
        ),
        "T02": gt_ok(normalized_query="capital of canada", intent="capital_of", entity_label="canada"),
        "T03": gt_ok(normalized_query="capital of france", intent="capital_of", entity_label="france"),
        "T04": gt_ok(
            normalized_query="top 5 cities in germany by population",
            intent="top_entities_by_property",
            entity_type="cities",
            location_label="germany",
            property_name="population",
            limit=5,
        ),
        "T05": gt_ok(
            normalized_query="who is the head of state of brazil",
            intent="head_of_state",
            entity_label="brazil",
        ),
        "T06": gt_ok(
            normalized_query="population of taiwan",
            intent="population_of",
            entity_label="taiwan",
        ),
        "A01": {
            "status": "needs_disambiguation",
            "normalized_query": "capital of georgia",
            "source": "wikidata",
            "intent": "capital_of",
            "disambiguation_target": "entity",
            "surface_form": "georgia",
            "candidate_hints": ["Georgia (country)", "Georgia (U.S. state)"],
        },
        "A02": {
            "status": "needs_disambiguation",
            "normalized_query": "population of washington",
            "source": "wikidata",
            "intent": "population_of",
            "disambiguation_target": "entity",
            "surface_form": "washington",
            "candidate_hints": ["Washington (state)", "Washington, D.C."],
        },
        "A03": {
            "status": "needs_disambiguation",
            "normalized_query": "head of state of congo",
            "source": "wikidata",
            "intent": "head_of_state",
            "disambiguation_target": "entity",
            "surface_form": "congo",
            "candidate_hints": ["Republic of the Congo", "Democratic Republic of the Congo"],
        },
        "A04": {
            "status": "needs_disambiguation",
            "normalized_query": "population of jersey",
            "source": "wikidata",
            "intent": "population_of",
            "disambiguation_target": "entity",
            "surface_form": "jersey",
            "candidate_hints": ["Jersey (island)", "New Jersey (U.S. state)"],
        },
        "A05": {
            "status": "needs_disambiguation",
            "normalized_query": "capital of guinea",
            "source": "wikidata",
            "intent": "capital_of",
            "disambiguation_target": "entity",
            "surface_form": "guinea",
            "candidate_hints": ["Guinea", "Papua New Guinea", "Equatorial Guinea"],
        },
        "A06": {
            "status": "needs_disambiguation",
            "normalized_query": "cities in victoria",
            "source": "wikidata",
            "intent": "list_by_type_and_location",
            "disambiguation_target": "location",
            "surface_form": "victoria",
            "candidate_hints": ["Victoria (Australia)", "Victoria (British Columbia)", "Victoria (Seychelles)"],
        },
        "M01": gt_ok(normalized_query="capital of canada", intent="capital_of", entity_label="canada"),
        "M02": gt_ok(
            normalized_query="population of japan",
            intent="population_of",
            entity_label="japan",
        ),
        "M03": gt_ok(
            normalized_query="capital of germany",
            intent="capital_of",
            entity_label="germany",
        ),
        "M04": gt_ok(normalized_query="capital of brazil", intent="capital_of", entity_label="brazil"),
        "M05": gt_ok(
            normalized_query="top 5 cities in japan by population",
            intent="top_entities_by_property",
            entity_type="cities",
            location_label="japan",
            property_name="population",
            limit=5,
        ),
        "M06": gt_ok(
            normalized_query="population of france",
            intent="population_of",
            entity_label="france",
        ),
        "X01": {
            "status": "unsupported_or_underspecified",
            "normalized_query": "biggest cities",
            "reason": "missing scope (country/region) and ranking property definition",
        },
        "X02": {
            "status": "unsupported_or_underspecified",
            "normalized_query": "countries with high gdp",
            "reason": "missing explicit threshold/ranking definition for 'high'",
        },
        "X03": {
            "status": "unsupported_or_underspecified",
            "normalized_query": "top cities",
            "reason": "missing scope and ranking property/limit details",
        },
        "X04": {
            "status": "contradiction",
            "normalized_query": "smallest cities by highest population",
            "reason": "ranking intent is internally contradictory",
        },
        "X05": {
            "status": "contradiction",
            "normalized_query": "capital of japan in europe",
            "reason": "geographic constraint contradicts known world facts",
        },
        "X06": {
            "status": "unsupported_or_underspecified",
            "normalized_query": "countries with higher population than france but lower gdp than japan",
            "reason": "complex comparative query not supported in baseline target schema",
        },
    }


def build_labeled_rows(queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    gt_map = build_ground_truth_map()
    rows: List[Dict[str, Any]] = []
    for q in queries:
        qid = q["id"]
        if qid not in gt_map:
            raise KeyError(f"Missing ground truth for query id: {qid}")
        rows.append(
            {
                "id": qid,
                "natural_language_query": q["natural_language_query"],
                "difficulty": q["difficulty"],
                "category": q["category"],
                "ground_truth_structured_query": gt_map[qid],
                "notes": q["notes"],
            }
        )
    return rows


def write_outputs(rows: List[Dict[str, Any]], root: Path) -> None:
    out_dir = root / "part2" / "data"
    out_path = out_dir / "benchmark_ground_truth_v1.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    counts = Counter(r["ground_truth_structured_query"]["status"] for r in rows)
    summary = {
        "total_examples": len(rows),
        "ground_truth_status_counts": dict(sorted(counts.items())),
    }
    (out_dir / "benchmark_ground_truth_v1_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print("Wrote ground truth JSONL and summary.")


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    query_file = project_root / "part2" / "data" / "benchmark_queries_v1.jsonl"
    queries = load_queries(query_file)
    labeled = build_labeled_rows(queries)
    if len(labeled) != 30:
        raise RuntimeError(f"Expected 30 labeled rows, got {len(labeled)}")
    write_outputs(labeled, project_root)
