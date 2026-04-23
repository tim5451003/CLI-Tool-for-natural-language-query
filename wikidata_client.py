"""執行 Wikidata SPARQL 查詢並正規化回傳結果。"""

from typing import Any, Dict, List

import requests

from resolver import DEFAULT_HEADERS


WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"


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
