"""將 ParsedQuery 轉換為對應 intent 的 SPARQL 模板查詢。"""

from typing import Dict

from intents import ENTITY_TYPE_QIDS, PROPERTY_PIDS, ParsedQuery


def build_sparql(parsed: ParsedQuery, resolved: Dict[str, Dict[str, str]]) -> str:
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
