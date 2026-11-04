"""Explicitly gated Gemini evaluation of one fixed-evidence case."""

from __future__ import annotations

import argparse
import hashlib
import os
from datetime import UTC, datetime
from pathlib import Path

from philosophy_influence_explorer.evaluation.answer_dataset import (
    AnswerSuite,
    load_answer_evaluation,
)
from philosophy_influence_explorer.evaluation.answer_report import (
    save_answer_report,
)
from philosophy_influence_explorer.evaluation.answer_runner import (
    run_answer_evaluation,
)
from philosophy_influence_explorer.generation.gemini import (
    SYSTEM_INSTRUCTION,
    GeminiAnswerGenerator,
)
from philosophy_influence_explorer.ingestion.validators import (
    validate_curated_corpus,
)


def run_gemini_case(
    *,
    root: Path,
    case_id: str,
    model: str,
    destination: Path,
    allow_network: bool,
    timeout_seconds: float = 60.0,
    max_input_bytes: int = 64_000,
) -> dict:
    """Run one explicitly selected case and save its diagnostic report.

    The key is read only from the process environment.
    No application settings, retrieval, or database services are created.

    Destination checks are preflight checks, not a reservation.
    Exclusive creation during saving remains the overwrite protection.
    """
    if not allow_network:
        raise ValueError("Explicit --allow-network approval is required.")

    if destination.exists() or destination.is_symlink():
        raise FileExistsError("Report destination already exists.")

    if not destination.parent.is_dir():
        raise FileNotFoundError("Report parent directory must already exist.")

    corpus_dir = root / "data" / "curated"
    suite = load_answer_evaluation(
        root / "data" / "evaluation" / "answer-quality-v1.json",
        corpus_dir,
        root / "data" / "evaluation" / "semantic-search-v1.json",
    )

    selected = [case for case in suite.cases if case.id == case_id]
    if len(selected) != 1:
        raise ValueError("Select exactly one existing answer case ID.")

    selection = suite.model_dump()
    selection["cases"] = [selected[0].model_dump()]
    selected_suite = AnswerSuite.model_validate(selection)

    passages = validate_curated_corpus(corpus_dir)["passages"]

    generator = GeminiAnswerGenerator(
        api_key=os.environ.get("GOOGLE_API_KEY", ""),
        model=model,
        timeout_seconds=timeout_seconds,
        max_input_bytes=max_input_bytes,
    )

    started = datetime.now(UTC).isoformat()
    report = run_answer_evaluation(selected_suite, passages, generator)
    finished = datetime.now(UTC).isoformat()

    report["execution"] = {
        "provider": "gemini",
        "requested_model": model,
        "started_at_utc": started,
        "finished_at_utc": finished,
        "selected_case_ids": [case_id],
        "http_timeout_seconds": timeout_seconds,
        "max_input_bytes": max_input_bytes,
        "runner_retries": 0,
        "adapter_retries": 0,
        "system_instruction_sha256": hashlib.sha256(SYSTEM_INSTRUCTION.encode("utf-8")).hexdigest(),
        "answer_validation_location": "adapter_and_runner",
        "rejected_provider_output_retained": False,
    }

    save_answer_report(report, destination)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one fixed-evidence case with Gemini.")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-network", action="store_true")
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument("--max-input-bytes", type=int, default=64_000)
    args = parser.parse_args(argv)

    try:
        report = run_gemini_case(
            root=args.root,
            case_id=args.case_id,
            model=args.model,
            destination=args.output,
            allow_network=args.allow_network,
            timeout_seconds=args.timeout_seconds,
            max_input_bytes=args.max_input_bytes,
        )
    except (ValueError, OSError):
        # Avoid printing configuration values, file contents, or secrets.
        parser.exit(
            2,
            "Evaluation setup or report saving failed. "
            "Check case ID, model, GOOGLE_API_KEY, limits, and output path. "
            "A saving failure may occur after the provider call.\n",
        )

    result = report["results"][0]
    if result["error"] is not None:
        print("Report saved; case execution or validation failed.")
        return 1

    if not all(value is True for value in result["checks"].values()):
        print("Report saved; automatic checks did not all pass.")
        return 1

    print("Report saved; automatic checks passed. Manual review is pending.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
