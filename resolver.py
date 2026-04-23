"""Wikidata entity resolution：alias 正規化、候選查詢與簡單挑選。"""

from typing import Any, Dict, List

import requests

from intents import ALIAS_MAP


WIKIDATA_API = "https://www.wikidata.org/w/api.php"
DEFAULT_HEADERS = {
    "User-Agent": "CMI-Tool-Baseline/0.2 (educational take-home; contact: local-cli)",
}


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
        alias_label = ALIAS_MAP.get(label.lower(), "").lower()
        if cand_label == label.lower() or (alias_label and cand_label == alias_label):
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
