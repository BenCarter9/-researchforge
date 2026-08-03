from __future__ import annotations

from sqlalchemy import select

from app.finance.engine import build_table, render_table_text
from app.finance.xbrl import extract_facts
from app.ids import new_id
from app.ingest.chunk_10k import chunk_10k
from app.llm.client import ClaudeClient
from app.llm.persist import persist_section
from app.llm.prompts import OBJECTIVES
from app.models import (
    AnalysisRun,
    Claim,
    Document,
    DocumentChunk,
    FinancialFact,
    ResearchProject,
)
from app.pipeline.runner import PipelineContext, PipelineDeps
from app.sec.client import SecClient

# Which chunk section_labels feed each generated section.
_SECTION_ROUTING: dict[str, list[str]] = {
    "snapshot": ["item_1", "prepared_remarks_ceo", "financial_table"],
    "business": ["item_1", "prepared_remarks_ceo", "prepared_remarks_cfo"],
    "financials": ["item_7", "prepared_remarks_cfo", "financial_table"],
    "risks": ["item_1a", "qa"],
}


def chunks_for(session, project_id: str, labels: list[str]) -> list[dict]:
    """Fetch this project's DocumentChunk rows whose section_label is in
    `labels`, across all of the project's documents (10-K + transcript)."""
    rows = session.scalars(
        select(DocumentChunk)
        .join(Document, DocumentChunk.document_id == Document.id)
        .where(
            Document.project_id == project_id,
            DocumentChunk.section_label.in_(labels),
        )
    ).all()
    return [{"id": r.id, "section_label": r.section_label, "text": r.text} for r in rows]


def build_deps(sec: SecClient, claude: ClaudeClient) -> PipelineDeps:
    """Wire the pipeline stages against a concrete SecClient/ClaudeClient.

    Each stage function reads/writes via ctx.session (the DB session for
    this pipeline run) and ctx.data (in-memory scratch space carried
    between stages within a single run).
    """

    async def fetch_filing(ctx: PipelineContext) -> None:
        project = ctx.session.get(ResearchProject, ctx.project_id)
        filing = await sec.latest_10k(project.cik)

        doc = Document(
            id=new_id(),
            project_id=ctx.project_id,
            type="10-K",
            source="edgar",
            source_url=filing.source_url,
            filing_date=filing.filing_date,
            fiscal_period=filing.fiscal_period,
        )
        ctx.session.add(doc)
        ctx.session.commit()

        ctx.data["filing_html"] = filing.html
        ctx.data["tenk_document_id"] = doc.id

    async def fetch_xbrl(ctx: PipelineContext) -> None:
        project = ctx.session.get(ResearchProject, ctx.project_id)
        ctx.data["company_facts"] = await sec.company_facts(project.cik)

    async def chunk(ctx: PipelineContext) -> None:
        document_id = ctx.data["tenk_document_id"]
        for c in chunk_10k(ctx.data["filing_html"]):
            ctx.session.add(
                DocumentChunk(
                    id=new_id(),
                    document_id=document_id,
                    section_label=c.section_label,
                    text=c.text,
                )
            )
        ctx.session.commit()

    async def financials(ctx: PipelineContext) -> None:
        facts = extract_facts(ctx.data["company_facts"])
        for concept, series in facts.items():
            for period, value in series.items():
                ctx.session.add(
                    FinancialFact(
                        id=new_id(),
                        project_id=ctx.project_id,
                        concept=concept,
                        period=period,
                        value=value,
                    )
                )
        table = build_table(facts)
        ctx.data["financial_table"] = table

        # Persist a citeable plain-text rendering so Snapshot/Financials can
        # ground claims on supplied XBRL figures without LLM arithmetic.
        document_id = ctx.data["tenk_document_id"]
        ctx.session.add(
            DocumentChunk(
                id=new_id(),
                document_id=document_id,
                section_label="financial_table",
                text=render_table_text(table),
            )
        )
        ctx.session.commit()

    def _make_generate_section(section: str):
        labels = _SECTION_ROUTING[section]

        async def generate(ctx: PipelineContext) -> None:
            chunk_dicts = chunks_for(ctx.session, ctx.project_id, labels)
            result = claude.generate_section(OBJECTIVES[section], chunk_dicts)

            chunk_ids = [c["id"] for c in chunk_dicts]
            chunk_rows = (
                ctx.session.scalars(
                    select(DocumentChunk).where(DocumentChunk.id.in_(chunk_ids))
                ).all()
                if chunk_ids
                else []
            )
            chunks_by_id = {row.id: row for row in chunk_rows}

            persist_section(ctx.session, ctx.project_id, section, result, chunks_by_id, new_id)

        return generate

    async def validate(ctx: PipelineContext) -> None:
        """Compute the citation-verified rate over this project's material
        claims (i.e. all claims except "assumption") and stash it on the
        validate stage's AnalysisRun.detail.

        This is a deterministic bookkeeping stage only. Layer-2 LLM
        entailment checking is a later task and is NOT invoked here.
        """
        claims = ctx.session.scalars(
            select(Claim).where(Claim.project_id == ctx.project_id)
        ).all()
        material = [c for c in claims if c.claim_type != "assumption"]
        verified = sum(
            1 for c in material if any(cit.verbatim_verified for cit in c.citations)
        )
        rate = verified / len(material) if material else None

        run = ctx.session.scalars(
            select(AnalysisRun).where(
                AnalysisRun.project_id == ctx.project_id,
                AnalysisRun.stage == "validate",
            )
        ).first()
        if run is not None:
            run.detail = {
                "citation_verified_rate": rate,
                "material_claims": len(material),
                "verified_claims": verified,
            }
            ctx.session.commit()

    return PipelineDeps(
        fetch_filing=fetch_filing,
        fetch_xbrl=fetch_xbrl,
        chunk=chunk,
        financials=financials,
        generate_snapshot=_make_generate_section("snapshot"),
        generate_business=_make_generate_section("business"),
        generate_financials=_make_generate_section("financials"),
        generate_risks=_make_generate_section("risks"),
        validate=validate,
    )
