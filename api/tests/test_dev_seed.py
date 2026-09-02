from __future__ import annotations

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.models import Claim, FinancialFact
from app.routes.dev import PROJECT_ID, TICKER, seed_demo_project


def test_seed_demo_project_is_googl_with_cited_10k_quotes():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    db = Session()
    result = seed_demo_project(db)
    assert result["ticker"] == "GOOGL"
    assert result["project_id"] == PROJECT_ID
    assert TICKER == "GOOGL"

    claims = db.scalars(select(Claim).where(Claim.project_id == PROJECT_ID)).all()
    quotes = " ".join(
        c.citations[0].verbatim_quote for c in claims if c.citations
    )
    assert "Google Services generates revenues primarily" in quotes
    assert "We face intense competition" in quotes
    assert "18%" not in quotes
    facts = db.scalars(
        select(FinancialFact).where(FinancialFact.project_id == PROJECT_ID)
    ).all()
    revenue = {f.period: f.value for f in facts if f.concept == "revenue"}
    assert revenue["FY2024"] == 350_018.0
    assert revenue["FY2023"] == 307_394.0
    assert not any(f.concept == "gross_profit" for f in facts)
    db.close()
