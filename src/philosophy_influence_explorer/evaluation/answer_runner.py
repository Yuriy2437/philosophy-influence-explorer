"""Run fixed-evidence evaluation without configuring external services."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from copy import deepcopy
from dataclasses import asdict
from time import perf_counter

from philosophy_influence_explorer.evaluation.answer_dataset import AnswerSuite
from philosophy_influence_explorer.evaluation.answer_evidence import (
    build_fixed_evidence,
)
from philosophy_influence_explorer.generation.base import AnswerGenerator
from philosophy_influence_explorer.generation.contracts import (
    GroundedAnswer,
    validate_answer_references,
)
from philosophy_influence_explorer.ingestion.models import PassageRecord


def _evidence_hash(snapshot: dict) -> str:
    """Hash the complete ordered packet using a defined JSON encoding."""
    encoded = json.dumps(
        snapshot,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _error(stage: str, error: Exception) -> dict:
    return {
        "stage": stage,
        "type": type(error).__name__,
        "message": str(error),
    }


def run_answer_evaluation(
    suite: AnswerSuite,
    passages: Sequence[PassageRecord],
    generator: AnswerGenerator,
) -> dict:
    """Run once per case and return a JSON-compatible diagnostic report.

    Invalid suite or evidence aborts before any generator call.
    Generation and answer-validation errors are recorded per case.
    No retries, semantic grading, persistence, or provider setup occurs here.

    Duration measures the generator call, including failed calls.
    """
    validated_suite = AnswerSuite.model_validate(suite.model_dump())

    case_ids = [case.id for case in validated_suite.cases]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("Duplicate answer case ID.")

    source_ids = [case.source_case_id for case in validated_suite.cases]
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("Duplicate source case ID.")

    # Prepare every case before making potentially external generator calls.
    prepared = []
    for case in validated_suite.cases:
        evidence = build_fixed_evidence(case, passages)
        prepared.append((case, evidence, asdict(evidence)))

    results = []

    for case, evidence, snapshot in prepared:
        result = {
            "case": case.model_dump(mode="json"),
            "evidence": snapshot,
            "evidence_sha256": _evidence_hash(snapshot),
            "draft_answer": None,
            "answer": None,
            "generation_duration_seconds": 0.0,
            "checks": {
                "structure_valid": None,
                "references_valid": None,
                "status_allowed": None,
            },
            "error": None,
            "manual_review": {
                "verdict": None,
                "notes": None,
            },
        }
        results.append(result)

        started = perf_counter()
        try:
            draft = generator.generate(
                query_text=case.query,
                evidence=evidence,
            )
        except Exception as error:
            result["error"] = _error("generation", error)
            continue
        finally:
            result["generation_duration_seconds"] = perf_counter() - started

        try:
            if not isinstance(draft, GroundedAnswer):
                raise ValueError("Generator must return GroundedAnswer.")

            # Preserve rejected model output separately from an accepted answer.
            result["draft_answer"] = deepcopy(draft.model_dump(mode="json"))

            # Validate a dict, not the existing model instance.
            answer = GroundedAnswer.model_validate(deepcopy(result["draft_answer"]))
        except Exception as error:
            result["checks"]["structure_valid"] = False
            result["error"] = _error("structure", error)
            continue

        result["checks"]["structure_valid"] = True
        result["checks"]["status_allowed"] = answer.status in case.allowed_answer_statuses

        try:
            validate_answer_references(answer, evidence)
        except Exception as error:
            result["checks"]["references_valid"] = False
            result["error"] = _error("references", error)
            continue

        result["checks"]["references_valid"] = True
        result["answer"] = answer.model_dump(mode="json")

    return {
        "schema_version": 1,
        "suite_id": validated_suite.suite_id,
        "mode": validated_suite.mode,
        "suite_description": validated_suite.description,
        "evidence_hash_algorithm": "sha256",
        "evidence_hash_encoding": (
            "UTF-8 JSON; ensure_ascii=false; sort_keys=true; separators=(',', ':'); allow_nan=false"
        ),
        "results": results,
    }
