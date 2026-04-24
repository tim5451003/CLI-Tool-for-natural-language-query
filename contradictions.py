"""在產生查詢前做簡單矛盾偵測（避免產生明顯無意義的 SPARQL）。"""

import re
from typing import Optional


def check_contradictions(text: str) -> Optional[str]:
    t = text.lower()
    if "smallest" in t and "highest" in t and "population" in t:
        return "Ranking is contradictory: 'smallest' and 'highest population' cannot both apply as stated."
    if re.search(r"\bcapital\s+of\s+japan\b", t) and re.search(r"\bin\s+europe\b", t):
        return "Constraint contradicts geography: Japan is not in Europe."
    return None
