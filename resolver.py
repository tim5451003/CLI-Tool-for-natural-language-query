"""Wikidata entity resolution：alias 正規化、候選查詢、過濾雜訊結果與歧義偵測。"""

import re
from typing import Any, Dict, List, Optional

import requests

from intents import ALIAS_MAP


WIKIDATA_API = "https://www.wikidata.org/w/api.php"
DEFAULT_HEADERS = {
    "User-Agent": "CMI-Tool-Baseline/0.3 (educational take-home; contact: local-cli)",
}

# 搜尋結果常見的「非地理實體」描述，用於降低誤選（仍保留真正的地理歧義）
_NOISE_DESCRIPTION = re.compile(
    r"\b(moth|butterfly|beetle|genus|species|taxon|subclass|family name|given name|surname|"
    r"album|song|film|television|video game|fictional)\b|disambiguation",
    re.I,
)


def search_entity_candidates(label: str, language: str = "en", limit: int = 10) -> List[Dict[str, Any]]:
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


def _is_noise(candidate: Dict[str, Any]) -> bool:
    desc = candidate.get("description") or ""
    return bool(_NOISE_DESCRIPTION.search(desc))


def resolve_entity(
    label: str,
    language: str = "en",
    *,
    intent: Optional[str] = None,
) -> Dict[str, Any]:
    """
    回傳 dict 包含：
    - qid: 選定的 Wikidata id，若需釐清則為 None
    - ambiguous / needs_disambiguation: 是否必須由使用者選擇
    - candidates: 候選列表（歧義時為同標籤的候選）
    """
    _ = intent  # 保留供未來依 intent 加權（例如優先 country）
    candidates = search_entity_candidates(label, language=language, limit=10)
    if not candidates:
        return {
            "qid": None,
            "chosen_label": "",
            "candidates": [],
            "ambiguous": False,
            "needs_disambiguation": False,
            "reason": "",
        }

    pool = [c for c in candidates if not _is_noise(c)]
    if not pool:
        pool = list(candidates)

    query_norm = label.strip().lower()
    alias_norm = ALIAS_MAP.get(query_norm, "").lower()

    def label_matches(c: Dict[str, Any]) -> bool:
        cand_label = (c.get("label") or "").strip().lower()
        return cand_label == query_norm or (bool(alias_norm) and cand_label == alias_norm)

    same_label = [c for c in pool if label_matches(c)]
    if len(same_label) >= 2:

        def _geo_score(c: Dict[str, Any]) -> int:
            d = (c.get("description") or "").lower()
            score = 0
            if re.search(r"\bcountry in\b", d) or "island country" in d or "sovereign state" in d:
                score += 10
            if re.search(r"\bstate of the united states\b", d) or "u.s. state" in d:
                score += 9
            if "federal district" in d or "district of columbia" in d:
                score += 8
            if "village" in d or "regency" in d or "human settlement" in d:
                score -= 15
            if "disambiguation" in d:
                score -= 5
            return score

        ranked = sorted(same_label, key=_geo_score, reverse=True)
        top, second = ranked[0], ranked[1]
        top_s, second_s = _geo_score(top), _geo_score(second)
        # 分數非常接近時代表兩種解讀都合理（例如 Georgia 州 vs Georgia 國）
        if top_s - second_s <= 1:
            return {
                "qid": None,
                "chosen_label": "",
                "ambiguous": True,
                "needs_disambiguation": True,
                "reason": "multiple_distinct_items_share_same_label",
                "candidates": [
                    {
                        "id": c.get("id"),
                        "label": c.get("label"),
                        "description": c.get("description", ""),
                    }
                    for c in same_label[:8]
                ],
            }
        chosen = top
        return {
            "qid": chosen.get("id"),
            "chosen_label": chosen.get("label", ""),
            "ambiguous": False,
            "needs_disambiguation": False,
            "reason": "ranked_among_same_label_matches",
            "candidates": [
                {"id": c.get("id"), "label": c.get("label"), "description": c.get("description", "")}
                for c in pool[:5]
            ],
        }

    exact_idx = None
    for i, candidate in enumerate(pool):
        cand_label = (candidate.get("label") or "").lower()
        if cand_label == query_norm or (alias_norm and cand_label == alias_norm):
            exact_idx = i
            break

    chosen = pool[exact_idx] if exact_idx is not None else pool[0]
    fuzzy_ambiguous = exact_idx is None and len(pool) > 1
    if fuzzy_ambiguous:
        return {
            "qid": None,
            "chosen_label": "",
            "ambiguous": True,
            "needs_disambiguation": True,
            "reason": "no_exact_label_match_multiple_results",
            "candidates": [
                {"id": c.get("id"), "label": c.get("label"), "description": c.get("description", "")}
                for c in pool[:8]
            ],
        }

    return {
        "qid": chosen.get("id"),
        "chosen_label": chosen.get("label", ""),
        "ambiguous": False,
        "needs_disambiguation": False,
        "reason": "",
        "candidates": [
            {"id": c.get("id"), "label": c.get("label"), "description": c.get("description", "")}
            for c in pool[:5]
        ],
    }
