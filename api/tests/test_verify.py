from app.llm.verify import verbatim_verify, evidence_status


def test_verbatim_true_ignores_whitespace():
    assert verbatim_verify("customers account for a substantial",
                           "A limited number of  customers   account for a substantial portion.")


def test_verbatim_false_for_fabricated_quote():
    assert not verbatim_verify("revenue tripled overnight", "Revenue grew 12% year over year.")


def test_status_rules():
    assert evidence_status("reported_fact", True, "supports") == "green"
    assert evidence_status("analyst_inference", True, "partial") == "yellow"
    assert evidence_status("management_claim", False, None) == "red"
    assert evidence_status("assumption", False, None) == "gray"


def test_status_assumption_precedence_over_contradicts():
    assert evidence_status("assumption", True, "contradicts") == "gray"


def test_status_verified_contradicts_is_red():
    assert evidence_status("reported_fact", True, "contradicts") == "red"


def test_status_verified_inference_is_yellow():
    assert evidence_status("analyst_inference", True, "inference") == "yellow"


def test_status_unknown_entailment_defaults_to_conservative_yellow():
    # Regression guard: a malformed/unrecognized entailment value must never
    # render as the most-trusting "green" status.
    assert evidence_status("reported_fact", True, "bogus_value") == "yellow"
