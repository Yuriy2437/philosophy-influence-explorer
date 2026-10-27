"""Run historical semantic-search cases against configured services."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from philosophy_influence_explorer.config import Settings
from philosophy_influence_explorer.embeddings.factory import (
    create_embedding_provider,
)
from philosophy_influence_explorer.evaluation.dataset import load_evaluation
from philosophy_influence_explorer.evaluation.report import build_case_report
from philosophy_influence_explorer.graph.neo4j_client import Neo4jClient
from philosophy_influence_explorer.retrieval.passage_indexer import DATASET_ID
from philosophy_influence_explorer.retrieval.passage_retriever import (
    PassageRetriever,
    PassageSearchFilters,
)

ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    """Parse input paths and a required output destination."""
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate semantic retrieval using historical judgments. "
            "Calls configured embedding and Neo4j services."
        )
    )
    parser.add_argument(
        "--suite",
        type=Path,
        default=ROOT / "data/evaluation/semantic-search-v1.json",
    )
    parser.add_argument(
        "--judgments",
        type=Path,
        default=ROOT / "data/evaluation/semantic-search-judgments-v1.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="New JSON report path. Existing files are not overwritten.",
    )
    return parser.parse_args()


def main() -> int:
    """Run cases sequentially and preserve query failures in the report."""
    args = parse_args()
    suite, judgments = load_evaluation(args.suite, args.judgments)

    if args.output.exists():
        raise FileExistsError("Output already exists; choose a new report path.")

    settings = Settings()
    if not settings.neo4j_enabled:
        raise ValueError("Evaluation requires NEO4J_ENABLED=true.")

    provider = create_embedding_provider(settings)
    model_info = provider.model_info
    historical = suite.historical_context
    embedding_configuration_matches = (
        model_info.provider == historical.embedding_provider
        and model_info.model == historical.embedding_model
        and model_info.dimensions == historical.embedding_dimensions
    )

    started_at = datetime.now(UTC).isoformat()
    judgments_by_id = {item.case_id: item for item in judgments.cases}
    case_reports = []
    client = Neo4jClient(settings)

    try:
        client.verify_connectivity()
        retriever = PassageRetriever(client=client, provider=provider)

        for case in suite.cases:
            try:
                passages = retriever.search(
                    case.query,
                    limit=case.limit,
                    filters=PassageSearchFilters(**case.filters.model_dump()),
                )
            except Exception as error:
                report = build_case_report(
                    case,
                    judgments_by_id[case.id],
                    None,
                    error_type=type(error).__name__,
                )
            else:
                report = build_case_report(
                    case,
                    judgments_by_id[case.id],
                    passages,
                )

            case_reports.append(report)
            print(f"{case.id}: {report['status']}")
    finally:
        client.close()

    error_count = sum(item["status"] == "error" for item in case_reports)
    filter_failure_count = sum(item["all_results_match_filters"] is False for item in case_reports)
    report = {
        "report_schema_version": 1,
        "suite_id": suite.suite_id,
        "started_at": started_at,
        "finished_at": datetime.now(UTC).isoformat(),
        "dataset_id": DATASET_ID,
        "embedding_configuration": {
            "provider": model_info.provider,
            "model": model_info.model,
            "dimensions": model_info.dimensions,
        },
        "historical_context": historical.model_dump(),
        "embedding_configuration_matches_historical": (embedding_configuration_matches),
        "dataset_id_matches_historical": DATASET_ID == historical.dataset_id,
        "current_corpus_snapshot_verified": False,
        "summary": {
            "case_count": len(case_reports),
            "query_error_count": error_count,
            "filter_failure_case_count": filter_failure_count,
        },
        "cases": case_reports,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(report, output, ensure_ascii=False, indent=2)
        output.write("\n")

    print(f"Completed: {len(case_reports)} cases, {error_count} query errors.")
    return 1 if error_count or filter_failure_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
