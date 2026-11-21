# Period-Tagged Company Briefing (Project 36)

CrewAI financial company briefing agent enforcing entity disambiguation, mandatory unit and fiscal-period tags on every figure, and strict fact vs. interpretation separation.

## Architecture

The system is structured around a deterministic verification pipeline wrapped around CrewAI-style research and briefing roles:

- **Entity Disambiguation Layer**: Resolves ambiguous company names, tickers, and subsidiaries (e.g., parent vs. operating unit, share classes, exchanges) before any retrieval or synthesis begins.
- **Period & Unit Tagging Engine**: Requires every quantitative metric to carry an explicit currency/unit (`USD millions`, `%`, `bps`) and fiscal-period tag (`FY2025`, `Q3 FY2026`, `TTM ending 2026-09-30`). Untagged numbers are rejected or quarantined.
- **Fact vs. Interpretation Separator**: Enforces two distinct output sections—verified, source-attributed factual statements and clearly labeled analytical commentary—preventing speculative or forward-looking opinions from blending into reported financials.

## 6-Stage Workflow

1. **Entity Resolution & Disambiguation**: Confirm canonical legal name, primary ticker, exchange, and reporting currency.
2. **Scoped Source Retrieval**: Gather filings, earnings releases, and market data (with explicit offline/mock-mode disclosure when live search tools are absent).
3. **Metric Extraction & Normalization**: Extract financial figures and attach mandatory `(value, unit, fiscal_period, source_url)` metadata.
4. **Tag & Consistency Validation**: Reject figures missing units, fiscal periods, or provenance; flag period mismatches (e.g., comparing Q3 vs. FY without normalization).
5. **Fact vs. Interpretation Partitioning**: Separate audited/reported facts from analyst commentary, valuation views, and forward-looking risks.
6. **Briefing Assembly & Audit**: Render the final company briefing with an audit summary of rejected/untagged claims and active mode disclosures.

## Data Contract

Every extracted financial claim adheres to a strict structured contract:

- `entity_id`: Canonical ticker and legal entity identifier.
- `metric_name`: Standardized financial metric (e.g., `Revenue`, `Operating Income`, `Free Cash Flow`).
- `value`: Numeric value.
- `unit`: Mandatory unit or currency scale (e.g., `USD_M`, `PCT`, `EPS_USD`).
- `fiscal_period`: Mandatory fiscal period tag (e.g., `FY2025`, `Q2 FY2026`).
- `statement_type`: `fact` or `interpretation`.
- `source_url`: Verifiable provenance URL or filing reference.

## Production Controls

- **Zero Untagged Numbers**: Any quantitative claim lacking both a unit and a fiscal-period tag is automatically stripped before final briefing emission.
- **Entity Boundary Guardrails**: Cross-entity contamination (e.g., mixing subsidiary revenue with consolidated parent figures) is blocked during validation.
- **Fact/Interpretation Isolation**: Interpretation blocks cannot cite unverified numbers or masquerade as reported GAAP/IFRS facts.
- **Offline Mode Transparency**: When live search or filing APIs are unavailable, the briefing explicitly discloses offline execution mode.

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
pytest
```

## Attribution

Adapted and hardened from the CrewAI financial researcher reference implementation in [ed-donner/agents](https://github.com/ed-donner/agents) (`3_crewai/reference/financial_researcher`).
