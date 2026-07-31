from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.db import Base
from app.models import ResearchProject, Document, DocumentChunk, Claim, ClaimCitation

def _session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return Session(engine)

def test_claim_links_to_citation_and_chunk():
    s = _session()
    proj = ResearchProject(id="p1", company="Acme", ticker="ACME")
    doc = Document(id="d1", project_id="p1", type="10-K", source="edgar")
    chunk = DocumentChunk(id="c1", document_id="d1", section_label="item_1a",
                          text="A limited number of customers account for a substantial portion of revenue.")
    claim = Claim(id="cl1", project_id="p1", section="risks",
                  claim_text="Management flags customer concentration as a principal risk.",
                  claim_type="management_claim", evidence_status="green", ordinal=0)
    cite = ClaimCitation(id="ci1", claim_id="cl1", chunk_id="c1",
                         verbatim_quote="A limited number of customers account for a substantial portion of revenue.",
                         verbatim_verified=True)
    s.add_all([proj, doc, chunk, claim, cite]); s.commit()
    got = s.get(Claim, "cl1")
    assert got.section == "risks"
    assert got.citations[0].chunk.section_label == "item_1a"
