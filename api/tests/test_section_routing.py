from app.pipeline.stages import _SECTION_ROUTING


def test_section_routing_covers_grounding_labels():
    assert "item_1" in _SECTION_ROUTING["snapshot"]
    assert "prepared_remarks_ceo" in _SECTION_ROUTING["snapshot"]
    assert "financial_table" in _SECTION_ROUTING["snapshot"]

    assert "item_1" in _SECTION_ROUTING["business"]
    assert "prepared_remarks_cfo" in _SECTION_ROUTING["business"]

    assert "item_7" in _SECTION_ROUTING["financials"]
    assert "prepared_remarks_cfo" in _SECTION_ROUTING["financials"]
    assert "financial_table" in _SECTION_ROUTING["financials"]
    assert "item_8" not in _SECTION_ROUTING["financials"]

    assert _SECTION_ROUTING["risks"] == ["item_1a", "qa"]
