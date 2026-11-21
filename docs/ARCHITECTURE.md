# Architecture: Period-Tagged Company Briefing (Project 36)

## Overview

`period-tagged-company-briefing` enforces deterministic financial research hygiene before any executive briefing is emitted to `output/report.md`. It prevents four common failure modes in automated equity research:

1. **Entity Ambiguity** — Rejects ambiguous company names (e.g., `"Apple"`, `"Alphabet"`, `"Meta"`) unless disambiguated by a canonical stock ticker and legal identifier (e.g., CIK / LEI).
2. **Untagged Figures** — Rejects any numerical metric lacking an explicit currency/unit (`USD billions`, `%`, `USD/share`) or fiscal-period tag (`FY2025`, `Q4 FY2025`).
3. **Fact vs. Interpretation Bleed** — Separates `[FACT]` citations (source-backed, period-tagged) from `[INTERPRETATION]` commentary in distinct report sections.
4. **Hallucinated Numbers** — Audits every numerical token in the final Markdown report against the validated input research metrics to guarantee exact figure parity.

## Pipeline Stages

1. **Entity Disambiguation (`disambiguate_entity`)**: Resolves input queries against a canonical `CompanyEntity` registry using `ticker` and `legal_id`.
2. **Metric Validation (`validate_metric`)**: Converts raw research figures into `PeriodTaggedMetric` records, raising `MetricValidationError` if `unit` or `fiscal_period` is missing.
3. **Statement Classification**: Groups `BriefingStatement` entries strictly into `FACT` and `INTERPRETATION` buckets.
4. **Report Rendering**: Generates `output/report.md` with explicit `[FACT]` and `[INTERPRETATION]` prefixes and dedicated sections.
5. **Numeric Parity Audit (`audit_report_parity`)**: Extracts numerical tokens from the rendered report and verifies each figure matches the entity metadata or validated input metrics, raising `AuditParityError` on any unbacked number.
