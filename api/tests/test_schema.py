import pytest
from pydantic import ValidationError

from app.llm.schema import GeneratedClaim, SectionResult
from app.llm.prompts import SYSTEM_PROMPT


def test_section_result_accepts_valid_payload_with_contradictory_evidence():
    payload = {
        "claims": [
            {
                "claim_text": "Revenue grew 12% year over year.",
                "claim_type": "reported_fact",
                "verbatim_quote": "Total revenue increased 12% compared to the prior year.",
                "chunk_id": "c1",
                "contradictory_evidence": "Management noted a slowdown in Q4 order volume.",
            }
        ]
    }
    result = SectionResult.model_validate(payload)
    assert len(result.claims) == 1
    claim = result.claims[0]
    assert isinstance(claim, GeneratedClaim)
    assert claim.claim_text == "Revenue grew 12% year over year."
    assert claim.claim_type == "reported_fact"
    assert claim.verbatim_quote == "Total revenue increased 12% compared to the prior year."
    assert claim.chunk_id == "c1"
    assert claim.contradictory_evidence == "Management noted a slowdown in Q4 order volume."

    # Round-trip through dict form.
    round_tripped = SectionResult.model_validate(result.model_dump())
    assert round_tripped == result


def test_generated_claim_defaults_contradictory_evidence_to_none():
    claim = GeneratedClaim(
        claim_text="Management targets 20% margins by FY2027.",
        claim_type="management_claim",
        verbatim_quote="We are targeting 20% operating margins by fiscal 2027.",
        chunk_id="c2",
    )
    assert claim.contradictory_evidence is None

    round_tripped = GeneratedClaim.model_validate(claim.model_dump())
    assert round_tripped == claim


def test_section_result_rejects_out_of_enum_claim_type():
    payload = {
        "claims": [
            {
                "claim_text": "The company will definitely beat estimates.",
                "claim_type": "guess",
                "verbatim_quote": "some quote",
                "chunk_id": "c3",
            }
        ]
    }
    with pytest.raises(ValidationError):
        SectionResult.model_validate(payload)


def test_system_prompt_contains_adversarial_instruction():
    assert (
        "Before finalizing, identify the strongest evidence against your conclusion."
        in SYSTEM_PROMPT
    )


def test_system_prompt_contains_adjusted_ebitda_rule():
    assert "adjusted EBITDA" in SYSTEM_PROMPT
