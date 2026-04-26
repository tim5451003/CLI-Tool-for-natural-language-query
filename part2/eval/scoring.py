"""Field-level scoring for structured query predictions."""

from __future__ import annotations

import re
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


def _intent_family(intent: str) -> str:
    alias = {
        "find_capital": "capital_of",
        "find_capital_city": "capital_of",
        "capital_of": "capital_of",
        "find_population": "population_of",
        "query_population": "population_of",
        "get_population": "population_of",
        "population_of": "population_of",
        "find_head_of_state": "head_of_state",
        "head_of_state": "head_of_state",
        "ranked_list": "top_entities_by_property",
        "list_cities_by_population": "top_entities_by_property",
        "top_entities_by_property": "top_entities_by_property",
    }
    return alias.get(_norm(intent), _norm(intent))


def _token_overlap(a: str, b: str) -> float:
    ta = set(re.findall(r"[a-z0-9]+", _norm(a)))
    tb = set(re.findall(r"[a-z0-9]+", _norm(b)))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _tolerant_score(
    ground_truth: Dict[str, Any],
    prediction: Dict[str, Any],
    schema_valid: bool,
) -> tuple[float, int]:
    """A softer metric for practical utility over strict exact match."""
    gt_status = _norm(ground_truth.get("status", ""))
    pred_status = _norm(prediction.get("status", ""))

    # Keep status as primary signal, but allow partial credit for nearby classes.
    compatible_status = {
        ("unsupported_or_underspecified", "contradiction"),
        ("contradiction", "unsupported_or_underspecified"),
    }
    if gt_status != pred_status and (gt_status, pred_status) not in compatible_status:
        return (0.0, 0)

    if gt_status == "ok":
        checks = []
        checks.append(
            int(_intent_family(ground_truth.get("intent", "")) == _intent_family(prediction.get("intent", "")))
        )
        gt_entity = _norm(ground_truth.get("entity_label", ""))
        pred_entity = _norm(prediction.get("entity_label", ""))
        gt_location = _norm(ground_truth.get("location_label", ""))
        pred_location = _norm(prediction.get("location_label", ""))
        gt_property = _norm(ground_truth.get("property_name", ""))
        pred_property = _norm(prediction.get("property_name", ""))
        checks.append(int((not gt_entity) or (gt_entity == pred_entity)))
        checks.append(int((not gt_location) or (gt_location == pred_location)))
        checks.append(int((not gt_property) or (gt_property == pred_property)))
        # Treat near limit as acceptable for ranking intent.
        gt_limit = ground_truth.get("limit", 5)
        pred_limit = prediction.get("limit", 5)
        try:
            limit_ok = int(abs(int(gt_limit) - int(pred_limit)) <= 5)
        except Exception:
            limit_ok = 0
        checks.append(limit_ok)
        # Ignore source/language/casing noise in tolerant metric.
        score = sum(checks) / len(checks)
        # Consider practically-correct if core semantics mostly aligned.
        correct = int(score >= 0.5 and schema_valid)
        return (round(score, 4), correct)

    if gt_status == "needs_disambiguation":
        checks = []
        checks.append(int(_norm(ground_truth.get("intent", "")) == _norm(prediction.get("intent", ""))))
        checks.append(
            int(
                _norm(ground_truth.get("disambiguation_target", "")) == _norm(prediction.get("disambiguation_target", ""))
            )
        )
        gt_surface = _norm(ground_truth.get("surface_form", ""))
        pred_surface = _norm(prediction.get("surface_form", ""))
        checks.append(int(gt_surface == pred_surface or _token_overlap(gt_surface, pred_surface) >= 0.5))
        score = sum(checks) / len(checks)
        correct = int(score >= 0.5 and schema_valid)
        return (round(score, 4), correct)

    # For unsupported/contradiction, status match is the major signal.
    if gt_status in {"unsupported_or_underspecified", "contradiction"}:
        gt_reason = _norm(ground_truth.get("reason", ""))
        pred_reason = _norm(prediction.get("reason", ""))
        overlap = _token_overlap(gt_reason, pred_reason)
        reason_match = int(gt_reason == pred_reason or overlap >= 0.3)
        status_soft_match = int(gt_status == pred_status)
        score = 0.5 * status_soft_match + 0.5 * max(overlap, reason_match)
        correct = int(score >= 0.5 and schema_valid)
        return (round(score, 4), correct)

    return (0.0, 0)


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
    tolerant_score, tolerant_correct = _tolerant_score(ground_truth, prediction, valid)

    return {
        "exact_correct": exact_correct,
        "semantic_score": round(semantic_score, 4),
        "tolerant_correct": tolerant_correct,
        "tolerant_score": tolerant_score,
        "field_scores": field_scores,
        "schema_valid": valid,
        "schema_errors": schema_errors,
    }

