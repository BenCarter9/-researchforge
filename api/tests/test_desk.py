from __future__ import annotations

from fastapi.testclient import TestClient

from app.desk.calls import MEMO_PROMPT, MODEL_ID, PRECOMPUTED_DRAFT
from app.desk.glm import GlmClient, GlmEndpoint, resolve_glm_endpoint
from app.main import app
from app.routes.desk import get_glm_client


def test_desk_returns_sourced_calls_and_glm_model_id(monkeypatch):
    monkeypatch.delenv("GLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("ZAI_API_KEY", raising=False)
    client = TestClient(app)
    resp = client.get("/api/desk")
    assert resp.status_code == 200
    body = resp.json()
    assert body["model_id"] == "zai-org/GLM-5.2"
    assert body["model_license"] == "MIT"
    assert body["human_owns_call"] is True
    assert MODEL_ID in body["model_id"]
    assert "GLM-5.2" in body["prompt"] or "Rogo" in body["prompt"]
    assert body["prompt"] == MEMO_PROMPT

    by_id = {c["id"]: c for c in body["calls"]}
    assert by_id["rogo"]["proposed"] == "TAKE"
    assert by_id["fiscal-ai"]["proposed"] == "PASS"
    assert "$160 million" in by_id["rogo"]["facts"][0]["text"]
    assert "Rothschild & Co" in by_id["rogo"]["facts"][2]["text"]
    assert "$10 million" in by_id["fiscal-ai"]["facts"][0]["text"]
    assert "350,000" in by_id["fiscal-ai"]["facts"][1]["text"]
    assert "FinChat" in by_id["fiscal-ai"]["company"]

    # $2B valuation must stay labeled unverified, never a fact.
    rogo_fact_blob = " ".join(f["text"] for f in by_id["rogo"]["facts"])
    assert "$2B" not in rogo_fact_blob
    assert "$2B" not in by_id["rogo"]["summary"]
    assert any("unverified" in note.lower() for note in by_id["rogo"]["unverified"])

    for call in body["calls"]:
        for fact in call["facts"]:
            src = fact["source"]
            assert src["url"].startswith("http")
            assert src["verbatim_quote"]
            assert src["publisher"]
            assert src["date"]


def test_desk_memo_without_key_returns_labeled_precomputed_draft(monkeypatch):
    monkeypatch.delenv("GLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("ZAI_API_KEY", raising=False)
    app.dependency_overrides[get_glm_client] = lambda: None
    try:
        client = TestClient(app)
        resp = client.post("/api/desk/memo")
        assert resp.status_code == 200
        body = resp.json()
        assert body["source"] == "precomputed"
        assert body["model_id"] == "zai-org/GLM-5.2"
        assert body["prompt"] == MEMO_PROMPT
        assert body["draft"] == PRECOMPUTED_DRAFT
        assert "Precomputed draft" in body["label"]
        assert "Not a live GLM-5.2 call" in body["label"]
        assert "Human confirms TAKE/PASS" in body["draft"]
        assert "$2B" not in body["draft"] or "unverified" in body["draft"].lower()
    finally:
        app.dependency_overrides.pop(get_glm_client, None)


def test_desk_memo_with_injected_client_returns_live_draft():
    class _FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "content": "Live TAKE Rogo / PASS Fiscal.ai. Human confirms TAKE/PASS."
                        }
                    }
                ]
            }

    class _FakeHttp:
        def __init__(self):
            self.last = None

        def post(self, url, headers=None, json=None, timeout=None):
            self.last = {
                "url": url,
                "headers": headers,
                "json": json,
                "timeout": timeout,
            }
            return _FakeResponse()

    fake_http = _FakeHttp()
    endpoint = GlmEndpoint(
        api_key="test-key",
        base_url="https://openrouter.ai/api/v1",
        request_model="z-ai/glm-5.2",
        key_name="OPENROUTER_API_KEY",
    )
    live = GlmClient(fake_http, endpoint)
    app.dependency_overrides[get_glm_client] = lambda: live
    try:
        client = TestClient(app)
        resp = client.post("/api/desk/memo")
        assert resp.status_code == 200
        body = resp.json()
        assert body["source"] == "live"
        assert body["model_id"] == "zai-org/GLM-5.2"
        assert "Live GLM-5.2" in body["label"]
        assert "TAKE Rogo" in body["draft"]
        assert fake_http.last["json"]["model"] == "z-ai/glm-5.2"
        assert fake_http.last["json"]["messages"][1]["content"] == MEMO_PROMPT
        assert fake_http.last["headers"]["Authorization"] == "Bearer test-key"
    finally:
        app.dependency_overrides.pop(get_glm_client, None)


def test_resolve_glm_endpoint_prefers_glm_then_openrouter_then_zai():
    assert resolve_glm_endpoint({}) is None
    glm = resolve_glm_endpoint({"GLM_API_KEY": "g", "OPENROUTER_API_KEY": "o"})
    assert glm is not None
    assert glm.key_name == "GLM_API_KEY"
    openrouter = resolve_glm_endpoint({"OPENROUTER_API_KEY": "o", "ZAI_API_KEY": "z"})
    assert openrouter is not None
    assert openrouter.key_name == "OPENROUTER_API_KEY"
    assert openrouter.request_model == "z-ai/glm-5.2"
    zai = resolve_glm_endpoint({"ZAI_API_KEY": "z"})
    assert zai is not None
    assert zai.key_name == "ZAI_API_KEY"
    assert zai.request_model == "glm-5.2"
