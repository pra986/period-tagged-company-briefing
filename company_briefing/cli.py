"""Runnable CLI demo entrypoint for period-tagged company briefings."""

from __future__ import annotations

import argparse
from pathlib import Path

from company_briefing.engine import PeriodTaggedCompanyBriefingEngine


def build_demo_payload() -> tuple[list[dict], list[dict]]:
    """Return a deterministic sample payload for Apple Inc. (AAPL)."""
    metrics = [
        {
            "metric_name": "Total Net Sales",
            "value": 391.04,
            "unit": "USD billions",
            "fiscal_period": "FY2024",
            "source_url": "https://www.sec.gov/edgar/browse/?CIK=0000320193",
        },
        {
            "metric_name": "Diluted EPS",
            "value": 6.08,
            "unit": "USD/share",
            "fiscal_period": "FY2024",
            "source_url": "https://www.sec.gov/edgar/browse/?CIK=0000320193",
        },
    ]
    statements = [
        {
            "statement_type": "FACT",
            "text": "Total Net Sales reached 391.04 USD billions in FY2024.",
            "source_url": "https://www.sec.gov/edgar/browse/?CIK=0000320193",
        },
        {
            "statement_type": "FACT",
            "text": "Diluted EPS was 6.08 USD/share in FY2024.",
            "source_url": "https://www.sec.gov/edgar/browse/?CIK=0000320193",
        },
        {
            "statement_type": "INTERPRETATION",
            "text": "Recurring Services revenue continues to support margin stability.",
        },
    ]
    return metrics, statements


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate an audited, period-tagged company briefing."
    )
    parser.add_argument("--company", default="Apple Inc.", help="Company query name")
    parser.add_argument("--ticker", default="AAPL", help="Canonical stock ticker")
    parser.add_argument("--legal-id", default="CIK:0000320193", help="Canonical legal ID")
    parser.add_argument("--output", default="output/report.md", help="Output Markdown path")
    args = parser.parse_args(argv)

    engine = PeriodTaggedCompanyBriefingEngine()
    metrics, statements = build_demo_payload()
    report = engine.generate_briefing(
        entity_query=args.company,
        raw_metrics=metrics,
        raw_statements=statements,
        ticker=args.ticker,
        legal_id=args.legal_id,
        output_path=Path(args.output),
    )
    print(f"Generated audited briefing for {report.entity.legal_name} ({report.entity.ticker})")
    print(f"Output written to: {report.output_path}")
    for note in report.audit_notes:
        print(f"Audit: {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
