from pathlib import Path
from app.ingest.chunk_10k import chunk_10k

HTML = Path(__file__).parent / "fixtures" / "sample_10k.html"


def test_splits_item_1_and_1a():
    chunks = {c.section_label: c.text for c in chunk_10k(HTML.read_text())}
    assert "item_1" in chunks and "item_1a" in chunks
    assert "We design and sell smartphones" in chunks["item_1"]
    assert "smartphones" not in chunks["item_1a"]           # 1 didn't swallow 1A
    assert "limited number of customers" in chunks["item_1a"]
