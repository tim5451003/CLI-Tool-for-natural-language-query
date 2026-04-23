"""定義 ParsedQuery schema 與 entity/property 映射常數。"""

from dataclasses import asdict, dataclass
from typing import Any, Dict


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
