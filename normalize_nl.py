"""將常見 typo 與少量多語片語正規化，再交給規則式 parser。"""

import re
from typing import List, Tuple

try:
    from rapidfuzz import fuzz, process

    _HAS_RAPIDFUZZ = True
except ImportError:
    _HAS_RAPIDFUZZ = False

# (pattern, replacement) 依序套用
_SUBSTITUTIONS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\bpoplation\b", re.I), "population"),
    (re.compile(r"\bjapen\b", re.I), "japan"),
    (re.compile(r"\bjapn\b", re.I), "japan"),
    (re.compile(r"\bcaneda\b", re.I), "canada"),
    (re.compile(r"\bcapitol\b", re.I), "capital"),
    (re.compile(r"\bcapital\s+de\b", re.I), "capital of"),
    (re.compile(r"\bpoblaci[oó]n\b", re.I), "population"),
]

# 常見錯拼 -> 正確 token（用於模糊比對整句中的單字）
_FUZZY_CORRECTIONS = {
    "poplation": "population",
    "japen": "japan",
    "caneda": "canada",
    "capitol": "capital",
}


def _fuzzy_fix_tokens(text: str) -> str:
    """對單字做保守的模糊修正（分數門檻高才替換）。"""
    if not _HAS_RAPIDFUZZ:
        return text
    words = re.findall(r"[A-Za-z]+", text)
    replacements: dict[str, str] = {}
    for w in words:
        lw = w.lower()
        if lw in _FUZZY_CORRECTIONS:
            continue
        extracted = process.extractOne(
            lw,
            list(_FUZZY_CORRECTIONS.keys()),
            scorer=fuzz.ratio,
        )
        match, score, _ = extracted if extracted else (None, 0.0, None)
        if match is None or score < 88:
            continue
        replacements[w] = _FUZZY_CORRECTIONS[match]
    if not replacements:
        return text
    out = text
    for wrong, right in replacements.items():
        out = re.sub(rf"\b{re.escape(wrong)}\b", right, out, flags=re.I)
    return out


def normalize_for_parse(text: str) -> str:
    s = text.strip()
    for pat, rep in _SUBSTITUTIONS:
        s = pat.sub(rep, s)
    s = _fuzzy_fix_tokens(s)
    return s
