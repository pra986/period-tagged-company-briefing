"""Pytest suite for PeriodTaggedCompanyBriefingEngine."""

from pathlib import Path

import pytest

from company_briefing import (
    AuditParityError,
    DisambiguationError,
    MetricValidationError,
    PeriodTaggedCompanyBriefingEngine,
)


def test_rejects_metric_missing_unit(tmp_path: Path) -> None:
    engine = PeriodTaggedCompanyBriefingEngine()
    with pytest.raises(MetricValidationError, match="unit"):
        engine.generate_briefing(
            entity_query="Apple Inc.",
            ticker="AAPL",
            legal_id="CIK:0000320193",
            raw_metrics=[
                {
                    "metric_name": "Total Revenue",
                    "value": 391.04,
                    "unit": "",
                    "fiscal_period": "FY2024",
                }
            ],
            raw_statements=[],
            output_path=tmp_path / "report.md",
        )


def test_rejects_metric_missing_fiscal_period(tmp_path: Path) -> None:
    engine = PeriodTaggedCompanyBriefingEngine()
    with pytest.raises(MetricValidationError, match="fiscal-period"):
        engine.generate_briefing(
            entity_query="Apple Inc.",
            ticker="AAPL",
            legal_id="CIK:0000320193",
            raw_metrics=[
                {
                    "metric_name": "Total Revenue",
                    "value": 391.04,
                    "unit": "USD billions",
                    "fiscal_period": "",
                }
            ],
            raw_statements=[],
            output_path=tmp_path / "report.md",
        )


def test_requires_entity_disambiguation_for_ambiguous_name(tmp_path: Path) -> None:
    engine = PeriodTaggedCompanyBriefingEngine()
    with pytest.raises(DisambiguationError):
        engine.generate_briefing(
            entity_query="Apple",
            raw_metrics=[],
            raw_statements=[],
            output_path=tmp_path / "report.md",
        )

    entity = engine.disambiguate_entity("Apple", ticker="AAPL", legal_id="CIK:0000320193")
    assert entity.legal_name == "Apple Inc."
    assert entity.ticker == "AAPL"


def test_strict_fact_vs_interpretation_separation_and_parity(tmp_path: Path) -> None:
    engine = PeriodTaggedCompanyBriefingEngine()
    report_file = tmp_path / "output" / "report.md"
    metrics = [
        {
            "metric_name": "Total Net Sales",
            "value": 391.04,
            "unit": "USD billions",
            "fiscal_period": "FY2024",
            "source_url": "https://www.sec.gov/edgar/browse/?CIK=0000320193",
        }
    ]
    statements = [
        {
            "statement_type": "FACT",
            "text": "Total Net Sales reached 391.04 USD billions in FY2024.",
            "source_url": "https://www.sec.gov/edgar/browse/?CIK=0000320193",
        },
        {
            "statement_type": "INTERPRETATION",
            "text": "Services mix continues to anchor top-line resilience.",
        },
    ]

    report = engine.generate_briefing(
        entity_query="Apple",
        ticker="AAPL",
        legal_id="CIK:0000320193",
        raw_metrics=metrics,
        raw_statements=statements,
        output_path=report_file,
    )

    assert report.audit_passed is True
    content = report_file.read_text(encoding="utf-8")
    fact_section, interp_section = content.split("## [INTERPRETATION] Analytical Commentary")
    assert "## [FACT] Verified Financial Citations" in fact_section
    assert "- [FACT] Total Net Sales reached 391.04 USD billions in FY2024." in fact_section
    assert "[INTERPRETATION]" not in fact_section
    assert "- [INTERPRETATION] Services mix continues to anchor top-line resilience." in interp_section
    assert "[FACT]" not in interp_section


def test_audit_rejects_unbacked_report_numbers(tmp_path: Path) -> None:
    engine = PeriodTaggedCompanyBriefingEngine()
    with pytest.raises(AuditParityError):
        engine.generate_briefing(
            entity_query="Apple Inc.",
            ticker="AAPL",
            legal_id="CIK:0000320193",
            raw_metrics=[
                {
                    "metric_name": "Total Net Sales",
                    "value": 391.04,
                    "unit": "USD billions",
                    "fiscal_period": "FY2024",
                }
            ],
            raw_statements=[
                {
                    "statement_type": "INTERPRETATION",
                    "text": "Revenue could reach 999.99 USD billions next year.",
                }
            ],
            output_path=tmp_path / "report.md",
        )
