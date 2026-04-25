"""Schema validation and required fields for scoring."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


REQUIRED_TOP_FIELDS = {"status", "normalized_query"}

REQUIRED_BY_STATUS = {
    "ok": {"source", "intent", "limit", "language"},
    "needs_disambiguation": {"source", "intent", "disambiguation_target", "surface_form"},
    "unsupported_or_underspecified": {"reason"},
    "contradiction": {"reason"},
}


def validate_prediction_schema(pred: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    for f in REQUIRED_TOP_FIELDS:
        if f not in pred:
            errors.append(f"missing top-level field: {f}")

    status = pred.get("status")
    if status not in REQUIRED_BY_STATUS:
        errors.append(f"invalid status: {status!r}")
        return (len(errors) == 0, errors)

    for f in REQUIRED_BY_STATUS[status]:
        if f not in pred:
            errors.append(f"missing field for status={status}: {f}")

    return (len(errors) == 0, errors)

