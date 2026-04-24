"""偵測明顯超出 baseline 範圍或資訊不足的輸入，並回傳可讀訊息。"""

import re
from typing import Optional

from intents import ParsedQuery


def check_scope(normalized_text: str, parsed: ParsedQuery) -> Optional[str]:
    t = normalized_text.lower()
    if parsed.intent != "instance_of":
        return None
    # 仍為 instance_of 但句子顯然在要排名 / 篩選 / 比較
    if re.search(r"\b(biggest|largest|smallest|top\s+\d+)\b", t) and "cities" in t:
        return (
            "This question looks like a ranking or top-N query, but it is missing scope "
            "(for example: 'top 10 cities in Germany by population')."
        )
    if "countries" in t and re.search(r"\b(high|higher|lower|gdp|population than)\b", t):
        return (
            "Comparative or threshold queries across countries are not supported in this baseline. "
            "Try a simpler fact query (for example: 'population of France')."
        )
    return None
