"""Field-level scoring for structured query predictions."""

from __future__ import annotations

from typing import Any, Dict, List

from .schema import validate_prediction_schema


SCORABLE_FIELDS = {
    "ok": [
        "status",
        "normalized_query",
        "source",
        "intent",
        "entity_label",
        "entity_type",
        "location_label",
        "property_name",
        "limit",
        "language",
    ],
    "needs_disambiguation": [
        "status",
        "normalized_query",
        "source",
        "intent",
        "disambiguation_target",
        "surface_form",
    ],
    "unsupported_or_underspecified": ["status", "normalized_query", "reason"],
    "contradiction": ["status", "normalized_query", "reason"],
}


def _norm(v: Any) -> Any:
    if isinstance(v, str):
        return v.strip().lower()
    return v


def score_single_prediction(
    ground_truth: Dict[str, Any],
    prediction: Dict[str, Any],
) -> Dict[str, Any]:
    valid, schema_errors = validate_prediction_schema(prediction)
    gt_status = ground_truth["status"]
    fields: List[str] = SCORABLE_FIELDS[gt_status]

    field_scores: Dict[str, int] = {}
    for f in fields:
        gt_v = _norm(ground_truth.get(f, ""))
        pred_v = _norm(prediction.get(f, ""))
        field_scores[f] = int(gt_v == pred_v)

    matched = sum(field_scores.values())
    total = len(fields)
    semantic_score = matched / total if total else 0.0
    exact_correct = int(semantic_score == 1.0 and valid)

    return {
        "exact_correct": exact_correct,
        "semantic_score": round(semantic_score, 4),
        "field_scores": field_scores,
        "schema_valid": valid,
        "schema_errors": schema_errors,
    }

