"""Data models for period-tagged company briefings."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class CompanyEntity:
    """Canonical company identity disambiguated by legal ticker and legal ID."""

    legal_name: str
    ticker: str
    exchange: str
    legal_id: str
    reporting_currency: str = "USD"
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class PeriodTaggedMetric:
    """A numerical financial figure tagged with an explicit unit and fiscal period."""

    metric_name: str
    value: float
    unit: str
    fiscal_period: str
    source_url: str = ""
    entity_id: str = ""


@dataclass(frozen=True)
class BriefingStatement:
    """An individual briefing statement classified as FACT or INTERPRETATION."""

    statement_type: Literal["FACT", "INTERPRETATION"]
    text: str
    source_url: str = ""
    entity_id: str = ""
    referenced_metrics: tuple[str, ...] = ()


@dataclass
class CompanyBriefingReport:
    """Audited executive briefing report with strict fact/interpretation separation."""

    entity: CompanyEntity
    metrics: list[PeriodTaggedMetric]
    facts: list[BriefingStatement]
    interpretations: list[BriefingStatement]
    rejected_metrics: list[dict] = field(default_factory=list)
    audit_passed: bool = False
    audit_notes: list[str] = field(default_factory=list)
    markdown_content: str = ""
    output_path: str = "output/report.md"
