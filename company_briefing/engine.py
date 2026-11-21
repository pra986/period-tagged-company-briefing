"""Core engine for period-tagged company briefings."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from company_briefing.models import (
    BriefingStatement,
    CompanyBriefingReport,
    CompanyEntity,
    PeriodTaggedMetric,
)


class DisambiguationError(ValueError):
    """Raised when a company query is ambiguous without a legal ticker or ID."""


class MetricValidationError(ValueError):
    """Raised when a numerical metric is missing a unit or fiscal-period tag."""


class AuditParityError(ValueError):
    """Raised when report figures do not match validated input research metrics."""


DEFAULT_ENTITIES: tuple[CompanyEntity, ...] = (
    CompanyEntity(
        legal_name="Apple Inc.",
        ticker="AAPL",
        exchange="NASDAQ",
        legal_id="CIK:0000320193",
        reporting_currency="USD",
        aliases=("Apple", "Apple Computer"),
    ),
    CompanyEntity(
        legal_name="Microsoft Corporation",
        ticker="MSFT",
        exchange="NASDAQ",
        legal_id="CIK:0000789019",
        reporting_currency="USD",
        aliases=("Microsoft",),
    ),
    CompanyEntity(
        legal_name="NVIDIA Corporation",
        ticker="NVDA",
        exchange="NASDAQ",
        legal_id="CIK:0001045810",
        reporting_currency="USD",
        aliases=("Nvidia", "NVIDIA"),
    ),
)


class PeriodTaggedCompanyBriefingEngine:
    """Enforces entity disambiguation, period/unit tagging, fact/interpretation separation, and numeric parity."""

    def __init__(self, entities: Iterable[CompanyEntity] = DEFAULT_ENTITIES) -> None:
        self._by_ticker: dict[str, CompanyEntity] = {}
        self._by_legal_id: dict[str, CompanyEntity] = {}
        for entity in entities:
            self._by_ticker[entity.ticker.upper()] = entity
            self._by_legal_id[entity.legal_id.upper()] = entity

    def disambiguate_entity(
        self,
        query: str,
        ticker: str | None = None,
        legal_id: str | None = None,
    ) -> CompanyEntity:
        """Resolve a company entity strictly via legal ticker or legal ID."""
        clean_ticker = (ticker or "").strip().upper()
        clean_legal_id = (legal_id or "").strip().upper()

        if not clean_ticker and not clean_legal_id:
            raise DisambiguationError(
                f"Ambiguous company reference '{query}': provide a canonical ticker or legal_id."
            )

        matched_by_ticker = self._by_ticker.get(clean_ticker) if clean_ticker else None
        matched_by_id = self._by_legal_id.get(clean_legal_id) if clean_legal_id else None

        if clean_ticker and matched_by_ticker is None:
            raise DisambiguationError(f"Unknown ticker '{ticker}' for query '{query}'.")
        if clean_legal_id and matched_by_id is None:
            raise DisambiguationError(f"Unknown legal_id '{legal_id}' for query '{query}'.")
        if matched_by_ticker and matched_by_id and matched_by_ticker != matched_by_id:
            raise DisambiguationError(
                f"Ticker '{ticker}' and legal_id '{legal_id}' refer to different entities."
            )

        entity = matched_by_ticker or matched_by_id
        assert entity is not None
        return entity

    def validate_metric(
        self,
        metric: PeriodTaggedMetric | dict,
        entity_id: str = "",
    ) -> PeriodTaggedMetric:
        """Validate that a numerical metric has an explicit unit and fiscal-period tag."""
        if isinstance(metric, dict):
            metric_name = str(metric.get("metric_name", "")).strip()
            raw_value = metric.get("value")
            unit = str(metric.get("unit") or "").strip()
            fiscal_period = str(metric.get("fiscal_period") or "").strip()
            source_url = str(metric.get("source_url") or "").strip()
            resolved_entity_id = str(metric.get("entity_id") or entity_id).strip()
        else:
            metric_name = metric.metric_name.strip()
            raw_value = metric.value
            unit = metric.unit.strip()
            fiscal_period = metric.fiscal_period.strip()
            source_url = metric.source_url.strip()
            resolved_entity_id = (metric.entity_id or entity_id).strip()

        if not metric_name:
            raise MetricValidationError("Metric is missing 'metric_name'.")
        if isinstance(raw_value, bool) or not isinstance(raw_value, (int, float)):
            raise MetricValidationError(f"Metric '{metric_name}' must have a numerical value.")
        if not unit:
            raise MetricValidationError(
                f"Metric '{metric_name}' rejected: missing currency or unit."
            )
        if not fiscal_period:
            raise MetricValidationError(
                f"Metric '{metric_name}' rejected: missing fiscal-period tag."
            )

        return PeriodTaggedMetric(
            metric_name=metric_name,
            value=float(raw_value),
            unit=unit,
            fiscal_period=fiscal_period,
            source_url=source_url,
            entity_id=resolved_entity_id,
        )

    def separate_statements(
        self,
        statements: Iterable[BriefingStatement | dict],
        entity_id: str = "",
    ) -> tuple[list[BriefingStatement], list[BriefingStatement]]:
        """Separate observed [FACT] citations from [INTERPRETATION] commentary."""
        facts: list[BriefingStatement] = []
        interpretations: list[BriefingStatement] = []

        for item in statements:
            if isinstance(item, dict):
                stmt_type = str(item.get("statement_type", "")).strip().upper()
                text = str(item.get("text", "")).strip()
                source_url = str(item.get("source_url") or "").strip()
                resolved_entity_id = str(item.get("entity_id") or entity_id).strip()
                refs = tuple(item.get("referenced_metrics") or ())
            else:
                stmt_type = item.statement_type.strip().upper()
                text = item.text.strip()
                source_url = item.source_url.strip()
                resolved_entity_id = (item.entity_id or entity_id).strip()
                refs = item.referenced_metrics

            if stmt_type == "FACT":
                facts.append(
                    BriefingStatement(
                        statement_type="FACT",
                        text=text,
                        source_url=source_url,
                        entity_id=resolved_entity_id,
                        referenced_metrics=refs,
                    )
                )
            elif stmt_type == "INTERPRETATION":
                interpretations.append(
                    BriefingStatement(
                        statement_type="INTERPRETATION",
                        text=text,
                        source_url=source_url,
                        entity_id=resolved_entity_id,
                        referenced_metrics=refs,
                    )
                )
            else:
                raise ValueError(f"Unsupported statement_type '{stmt_type}'.")

        return facts, interpretations

    def render_markdown(
        self,
        entity: CompanyEntity,
        metrics: list[PeriodTaggedMetric],
        facts: list[BriefingStatement],
        interpretations: list[BriefingStatement],
    ) -> str:
        """Render output/report.md with strict [FACT] and [INTERPRETATION] sections."""
        lines: list[str] = [
            f"# Period-Tagged Company Briefing: {entity.legal_name} ({entity.ticker})",
            "",
            f"- **Exchange**: {entity.exchange}",
            f"- **Legal ID**: {entity.legal_id}",
            f"- **Reporting Currency**: {entity.reporting_currency}",
            "",
            "## Period-Tagged Metrics",
            "",
        ]

        for m in metrics:
            source_suffix = f" ([source]({m.source_url}))" if m.source_url else ""
            lines.append(
                f"- **{m.metric_name}**: {m.value} {m.unit} ({m.fiscal_period}){source_suffix}"
            )

        lines.extend(["", "## [FACT] Verified Financial Citations", ""])
        for fact in facts:
            source_suffix = f" ([source]({fact.source_url}))" if fact.source_url else ""
            lines.append(f"- [FACT] {fact.text}{source_suffix}")

        lines.extend(["", "## [INTERPRETATION] Analytical Commentary", ""])
        for interp in interpretations:
            lines.append(f"- [INTERPRETATION] {interp.text}")

        lines.append("")
        return "\n".join(lines)

    def audit_report_parity(
        self,
        markdown_content: str,
        entity: CompanyEntity,
        metrics: list[PeriodTaggedMetric],
    ) -> list[str]:
        """Audit every numerical figure in the report against validated input metrics."""
        sanitized = re.sub(r"https?://\S+", "", markdown_content)
        sanitized = sanitized.replace(entity.legal_id, "")
        sanitized = re.sub(r"\b(?:Q[1-4]\s+)?FY\d{4}\b", "", sanitized)
        for m in metrics:
            sanitized = sanitized.replace(m.fiscal_period, "")

        report_numbers = [float(tok) for tok in re.findall(r"\b\d+(?:\.\d+)?\b", sanitized)]
        expected_values = {float(m.value) for m in metrics}

        unbacked = [num for num in report_numbers if num not in expected_values]
        if unbacked:
            raise AuditParityError(
                f"Report contains numerical figures not backed by input research metrics: {unbacked}"
            )

        missing = [m.value for m in metrics if float(m.value) not in report_numbers]
        if missing:
            raise AuditParityError(
                f"Report is missing validated input research figures: {missing}"
            )

        return [
            f"Verified {len(report_numbers)} report numeric occurrences against {len(metrics)} input metrics."
        ]

    def generate_briefing(
        self,
        entity_query: str,
        raw_metrics: Iterable[PeriodTaggedMetric | dict],
        raw_statements: Iterable[BriefingStatement | dict],
        ticker: str | None = None,
        legal_id: str | None = None,
        output_path: str | Path = "output/report.md",
    ) -> CompanyBriefingReport:
        """Run the full briefing pipeline and write the audited Markdown report."""
        entity = self.disambiguate_entity(entity_query, ticker=ticker, legal_id=legal_id)
        validated_metrics = [
            self.validate_metric(m, entity_id=entity.legal_id) for m in raw_metrics
        ]
        facts, interpretations = self.separate_statements(
            raw_statements, entity_id=entity.legal_id
        )
        markdown_content = self.render_markdown(
            entity=entity,
            metrics=validated_metrics,
            facts=facts,
            interpretations=interpretations,
        )
        audit_notes = self.audit_report_parity(
            markdown_content=markdown_content,
            entity=entity,
            metrics=validated_metrics,
        )

        target_path = Path(output_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(markdown_content, encoding="utf-8")

        return CompanyBriefingReport(
            entity=entity,
            metrics=validated_metrics,
            facts=facts,
            interpretations=interpretations,
            rejected_metrics=[],
            audit_passed=True,
            audit_notes=audit_notes,
            markdown_content=markdown_content,
            output_path=str(target_path),
        )
