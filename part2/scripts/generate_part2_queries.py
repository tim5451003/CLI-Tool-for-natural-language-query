"""Generate the Part 2 evaluation query set (Requirement 1: Data Generation).

This script programmatically generates 30 realistic/diverse NL queries for the
Wikidata domain used in Part 1.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from random import Random
from typing import List


@dataclass
class QueryExample:
    id: str
    natural_language_query: str
    difficulty: str
    category: str
    notes: str


def _clean_queries(rng: Random) -> List[QueryExample]:
    countries = ["japan", "france", "canada", "germany"]
    templates = [
        ("capital_of", "capital of {country}", "simple clean fact lookup"),
        ("population_of", "population of {country}", "simple clean numeric fact"),
        ("head_of_state", "who is the head of state of {country}", "clean relation lookup"),
    ]
    out: List[QueryExample] = []
    for i, country in enumerate(countries, start=1):
        t = templates[(i - 1) % len(templates)]
        out.append(
            QueryExample(
                id=f"C{i:02d}",
                natural_language_query=t[1].format(country=country),
                difficulty="easy",
                category="clean",
                notes=t[2],
            )
        )

    ranking_pool = [
        "top 10 cities in germany by population",
        "top 5 cities in japan by population",
    ]
    for j, q in enumerate(ranking_pool, start=5):
        out.append(
            QueryExample(
                id=f"C{j:02d}",
                natural_language_query=q,
                difficulty="medium",
                category="clean",
                notes="clean top-N ranking query",
            )
        )
    rng.shuffle(out)
    return out


def _typo_noisy_queries() -> List[QueryExample]:
    raw = [
        "poplation of japen",
        "capitol of caneda",
        "can u tell me the captial of frnace",
        "top 5 citiies in germny by population",
        "who is the hed of state of braziil",
        "pls show me poplation of taiwn thx",
    ]
    return [
        QueryExample(
            id=f"T{i:02d}",
            natural_language_query=q,
            difficulty="medium",
            category="typo_noisy",
            notes="intentionally typo/noisy wording",
        )
        for i, q in enumerate(raw, start=1)
    ]


def _ambiguous_queries() -> List[QueryExample]:
    raw = [
        "capital of georgia",
        "population of washington",
        "head of state of congo",
        "population of jersey",
        "capital of guinea",
        "cities in victoria",
    ]
    return [
        QueryExample(
            id=f"A{i:02d}",
            natural_language_query=q,
            difficulty="hard",
            category="ambiguous",
            notes="surface form has multiple valid entities",
        )
        for i, q in enumerate(raw, start=1)
    ]


def _multilingual_queries() -> List[QueryExample]:
    raw = [
        "capital de canada",
        "poblacion of japan",
        "quelle est la capitale of germany",
        "capital de brasil",
        "ciudades in japan by population top 5",
        "population de france",
    ]
    return [
        QueryExample(
            id=f"M{i:02d}",
            natural_language_query=q,
            difficulty="hard",
            category="multilingual_mixed",
            notes="mixed-language phrase or token",
        )
        for i, q in enumerate(raw, start=1)
    ]


def _underspecified_and_complex() -> List[QueryExample]:
    raw = [
        ("biggest cities", "underspecified"),
        ("countries with high gdp", "underspecified"),
        ("top cities", "underspecified"),
        ("smallest cities by highest population", "complex_constraints"),
        ("capital of japan in europe", "complex_constraints"),
        (
            "countries with higher population than france but lower gdp than japan",
            "complex_constraints",
        ),
    ]
    out: List[QueryExample] = []
    for i, (q, cat) in enumerate(raw, start=1):
        out.append(
            QueryExample(
                id=f"X{i:02d}",
                natural_language_query=q,
                difficulty="hard",
                category=cat,
                notes="adversarial edge-case input",
            )
        )
    return out


def generate_dataset() -> List[QueryExample]:
    rng = Random(42)
    rows: List[QueryExample] = []
    rows.extend(_clean_queries(rng))
    rows.extend(_typo_noisy_queries())
    rows.extend(_ambiguous_queries())
    rows.extend(_multilingual_queries())
    rows.extend(_underspecified_and_complex())
    if len(rows) != 30:
        raise RuntimeError(f"Expected 30 queries, got {len(rows)}")
    return rows


def write_outputs(rows: List[QueryExample], root: Path) -> None:
    data_dir = root / "part2" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    jsonl_path = data_dir / "benchmark_queries_v1.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(asdict(row), ensure_ascii=False) + "\n")

    summary_path = data_dir / "benchmark_queries_v1_summary.json"
    counts = Counter(r.category for r in rows)
    summary = {
        "total_queries": len(rows),
        "category_counts": dict(sorted(counts.items())),
        "difficulty_counts": dict(sorted(Counter(r.difficulty for r in rows).items())),
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Wrote {len(rows)} queries (JSONL)")
    print("Wrote summary JSON")


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    dataset = generate_dataset()
    write_outputs(dataset, project_root)
