from pathlib import Path
from app.ingest.chunk_10k import chunk_10k

HTML = Path(__file__).parent / "fixtures" / "sample_10k.html"


def test_splits_item_1_and_1a():
    chunks = {c.section_label: c.text for c in chunk_10k(HTML.read_text())}
    assert "item_1" in chunks and "item_1a" in chunks
    assert "We design and sell smartphones" in chunks["item_1"]
    assert "smartphones" not in chunks["item_1a"]           # 1 didn't swallow 1A
    assert "limited number of customers" in chunks["item_1a"]


def test_item_1a_boundary_does_not_swallow_untracked_items():
    # Item 1B/2/etc. aren't tracked labels, but they must still act as
    # boundaries so item_1a doesn't run all the way to Item 7.
    html = """
    <html><body>
    <p>Item 1A. Risk Factors</p>
    <p>We face risks related to customer concentration among a few large buyers.</p>
    <p>Item 2. Properties</p>
    <p>Properties: we lease office space in Cupertino.</p>
    <p>Item 7. Management's Discussion</p>
    <p>Our results of operations improved this year.</p>
    </body></html>
    """
    chunks = {c.section_label: c.text for c in chunk_10k(html)}
    assert "item_1a" in chunks
    assert "customer concentration" in chunks["item_1a"]
    assert "lease office space" not in chunks["item_1a"]
    assert "Properties" not in chunks["item_1a"]


def test_mid_sentence_item_cross_references_are_not_boundaries():
    # Real 10-Ks (e.g. Costco) put "in Item 7 and ..." inside Item 1A's
    # boilerplate. Those must not truncate the section before the actual
    # risk-factor body.
    html = """
    <html><body>
    <p>Item 1A—Risk Factors</p>
    <p>These Risk Factors should be carefully reviewed in conjunction with
    Management's Discussion and Analysis of Financial Condition and Results
    of Operations in Item 7 and our consolidated financial statements and
    related notes in Item 8 of this Report.</p>
    <p>Business and Operating Risks</p>
    <p>We are highly dependent on our membership renewal rates and fee income.</p>
    <p>Item 1B—Unresolved Staff Comments</p>
    <p>None.</p>
    </body></html>
    """
    chunks = {c.section_label: c.text for c in chunk_10k(html)}
    assert "item_1a" in chunks
    assert "membership renewal rates" in chunks["item_1a"]
    assert "Business and Operating Risks" in chunks["item_1a"]
    assert "Unresolved Staff Comments" not in chunks["item_1a"]
