"""自然語言解析：將輸入句子轉為 ParsedQuery 中介意圖物件。"""

import re
from typing import List, Tuple

from intents import ENTITY_TYPE_QIDS, ParsedQuery


KNOWN_ENTITY_TYPES = sorted(set(ENTITY_TYPE_QIDS.keys()), key=len, reverse=True)
ENTITY_TYPE_PATTERN = "|".join(re.escape(t) for t in KNOWN_ENTITY_TYPES)


def parse_nl_query(text: str, language: str) -> ParsedQuery:
    raw = text.strip()
    lowered = raw.lower().strip("?")

    patterns: List[Tuple[str, str]] = [
        ("capital_of", r"(?:what(?:'s| is) the capital of|capital of)\s+(.+)$"),
        ("population_of", r"(?:what(?:'s| is) the population of|population of)\s+(.+)$"),
        ("head_of_state", r"(?:who is the head of state of|head of state of)\s+(.+)$"),
        ("top_entities_by_property", r"top\s+(\d+)\s+(.+)\s+in\s+(.+)\s+by\s+(.+)$"),
        ("list_by_type_and_location", r"(?:list|show|find)\s+(.+)\s+in\s+(.+)$"),
        (
            "list_by_type_and_location",
            rf"({ENTITY_TYPE_PATTERN})\s+in\s+(.+)$",
        ),
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
