from __future__ import annotations
from sqlalchemy import String, Integer, Boolean, Text, ForeignKey, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base

class ResearchProject(Base):
    __tablename__ = "research_projects"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    company: Mapped[str] = mapped_column(String)
    ticker: Mapped[str] = mapped_column(String)
    cik: Mapped[str | None] = mapped_column(String, nullable=True)
    research_date: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="created")
    documents: Mapped[list["Document"]] = relationship(back_populates="project")

class Document(Base):
    __tablename__ = "documents"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("research_projects.id"))
    type: Mapped[str] = mapped_column(String)         # 10-K | transcript
    source: Mapped[str] = mapped_column(String)       # edgar | upload
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    filing_date: Mapped[str | None] = mapped_column(String, nullable=True)
    fiscal_period: Mapped[str | None] = mapped_column(String, nullable=True)
    checksum: Mapped[str | None] = mapped_column(String, nullable=True)
    storage_ref: Mapped[str | None] = mapped_column(String, nullable=True)
    project: Mapped[ResearchProject] = relationship(back_populates="documents")
    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="document")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"))
    section_label: Mapped[str] = mapped_column(String)   # item_1, item_1a, item_7, item_8, prepared_remarks_ceo, prepared_remarks_cfo, qa
    page_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    speaker: Mapped[str | None] = mapped_column(String, nullable=True)
    text: Mapped[str] = mapped_column(Text)
    document: Mapped[Document] = relationship(back_populates="chunks")

class FinancialFact(Base):
    __tablename__ = "financial_facts"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("research_projects.id"))
    concept: Mapped[str] = mapped_column(String)      # Revenues, NetIncomeLoss, ...
    period: Mapped[str] = mapped_column(String)       # FY2025
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String, default="USD")
    xbrl_tag: Mapped[str | None] = mapped_column(String, nullable=True)
    source_document_id: Mapped[str | None] = mapped_column(String, nullable=True)

class Claim(Base):
    __tablename__ = "claims"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("research_projects.id"))
    section: Mapped[str] = mapped_column(String)      # snapshot | business | financials | risks
    claim_text: Mapped[str] = mapped_column(Text)
    claim_type: Mapped[str] = mapped_column(String)
    evidence_status: Mapped[str] = mapped_column(String, default="gray")
    ordinal: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String, default="needs_review")
    citations: Mapped[list["ClaimCitation"]] = relationship(back_populates="claim")

class ClaimCitation(Base):
    __tablename__ = "claim_citations"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    claim_id: Mapped[str] = mapped_column(ForeignKey("claims.id"))
    chunk_id: Mapped[str] = mapped_column(ForeignKey("document_chunks.id"))
    verbatim_quote: Mapped[str] = mapped_column(Text)
    verbatim_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    entailment: Mapped[str | None] = mapped_column(String, nullable=True)  # supports|partial|inference|contradicts
    claim: Mapped[Claim] = relationship(back_populates="citations")
    chunk: Mapped[DocumentChunk] = relationship()

class AnalysisRun(Base):
    __tablename__ = "analysis_runs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("research_projects.id"))
    stage: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="pending")  # pending|running|done|error
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)
