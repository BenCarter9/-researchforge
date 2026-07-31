from app.ingest.chunk_transcript import chunk_transcript

TRANSCRIPT = """\
Operator: Good morning and welcome to the earnings call.

Jane Smith — Chief Executive Officer
Thank you all for joining. Our revenue grew twenty percent this quarter driven by strong cloud demand.

John Doe — Chief Financial Officer
Turning to the numbers, our gross margin expanded to sixty percent this quarter.

Question-and-Answer Session

Analyst: Can you comment on the margin trajectory for next quarter?
John Doe: We expect margins to remain stable as cloud mix continues to increase.
"""

NO_QA_TRANSCRIPT = """\
Operator: Good morning and welcome to the earnings call.

Jane Smith — Chief Executive Officer
Thank you all for joining. Our revenue grew twenty percent this quarter driven by strong cloud demand.

John Doe — Chief Financial Officer
Turning to the numbers, our gross margin expanded to sixty percent this quarter.
"""


def test_splits_prepared_remarks_and_qa():
    chunks = {c.section_label: c.text for c in chunk_transcript(TRANSCRIPT)}

    assert "prepared_remarks_ceo" in chunks
    assert "prepared_remarks_cfo" in chunks
    assert "qa" in chunks

    # CEO sentence lands only in the CEO chunk.
    assert "revenue grew twenty percent" in chunks["prepared_remarks_ceo"]
    assert "revenue grew twenty percent" not in chunks["prepared_remarks_cfo"]
    assert "revenue grew twenty percent" not in chunks["qa"]

    # CFO sentence lands only in the CFO chunk.
    assert "gross margin expanded to sixty percent" in chunks["prepared_remarks_cfo"]
    assert "gross margin expanded to sixty percent" not in chunks["prepared_remarks_ceo"]
    assert "gross margin expanded to sixty percent" not in chunks["qa"]

    # Analyst Q&A text lands only under qa.
    assert "margin trajectory for next quarter" in chunks["qa"]
    assert "margin trajectory for next quarter" not in chunks["prepared_remarks_ceo"]
    assert "margin trajectory for next quarter" not in chunks["prepared_remarks_cfo"]
    assert "margins to remain stable" in chunks["qa"]
    assert "margins to remain stable" not in chunks["prepared_remarks_ceo"]
    assert "margins to remain stable" not in chunks["prepared_remarks_cfo"]


def test_speaker_stored_on_chunk():
    chunks = {c.section_label: c for c in chunk_transcript(TRANSCRIPT)}
    assert chunks["prepared_remarks_ceo"].speaker is not None
    assert chunks["prepared_remarks_cfo"].speaker is not None
    assert chunks["qa"].speaker is None


def test_no_qa_marker_yields_no_qa_chunk():
    chunks = {c.section_label: c.text for c in chunk_transcript(NO_QA_TRANSCRIPT)}
    assert "qa" not in chunks
    assert "prepared_remarks_ceo" in chunks
    assert "prepared_remarks_cfo" in chunks
    assert "revenue grew twenty percent" in chunks["prepared_remarks_ceo"]
    assert "gross margin expanded to sixty percent" in chunks["prepared_remarks_cfo"]
