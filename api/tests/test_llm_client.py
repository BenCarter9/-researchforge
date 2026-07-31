from __future__ import annotations

from app.llm.client import ClaudeClient
from app.llm.prompts import SYSTEM_PROMPT
from app.llm.schema import GeneratedClaim, SectionResult


class _FakeMessages:
    def __init__(self, parsed):
        self._parsed = parsed
        self.last_kwargs = None

    def parse(self, **kwargs):
        self.last_kwargs = kwargs

        class R:
            pass

        r = R()
        r.parsed_output = self._parsed
        return r


class _FakeClient:
    def __init__(self, parsed):
        self.messages = _FakeMessages(parsed)


def _canned_result() -> SectionResult:
    return SectionResult(
        claims=[
            GeneratedClaim(
                claim_text="Revenue grew 12% year over year.",
                claim_type="reported_fact",
                verbatim_quote="Total revenue increased 12% compared to the prior year.",
                chunk_id="c1",
            )
        ]
    )


def test_generate_section_returns_fake_parsed_output():
    parsed = _canned_result()
    fake_client = _FakeClient(parsed)
    client = ClaudeClient(fake_client)

    objective = "Produce a concise company snapshot."
    chunks = [
        {"id": "c1", "section_label": "Item 1", "text": "Total revenue increased 12%."},
        {"id": "c2", "label": "Item 1A", "text": "We face significant competition."},
    ]

    result = client.generate_section(objective, chunks)

    assert result is parsed


def test_generate_section_uses_configured_model():
    fake_client = _FakeClient(_canned_result())
    client = ClaudeClient(fake_client, model="claude-opus-5")

    client.generate_section("objective text", [{"id": "c1", "label": "Item 1", "text": "some text"}])

    assert fake_client.messages.last_kwargs["model"] == "claude-opus-5"


def test_generate_section_passes_output_format_as_section_result_class():
    fake_client = _FakeClient(_canned_result())
    client = ClaudeClient(fake_client)

    client.generate_section("objective text", [{"id": "c1", "label": "Item 1", "text": "some text"}])

    assert fake_client.messages.last_kwargs["output_format"] is SectionResult


def test_generate_section_system_prompt_carries_ephemeral_cache_control():
    fake_client = _FakeClient(_canned_result())
    client = ClaudeClient(fake_client)

    client.generate_section("objective text", [{"id": "c1", "label": "Item 1", "text": "some text"}])

    system = fake_client.messages.last_kwargs["system"]
    assert isinstance(system, list)
    assert len(system) == 1
    assert system[0]["cache_control"] == {"type": "ephemeral"}
    assert system[0]["text"] == SYSTEM_PROMPT
    assert system[0]["type"] == "text"


def test_generate_section_renders_objective_and_all_chunk_ids_in_user_message():
    fake_client = _FakeClient(_canned_result())
    client = ClaudeClient(fake_client)

    objective = "Summarize the company's risk factors."
    chunks = [
        {"id": "chunk-aaa", "section_label": "Item 1A", "text": "Risk factor one text."},
        {"id": "chunk-bbb", "label": "Earnings Call Q&A", "text": "Risk factor two text."},
        {"id": "chunk-ccc", "text": "Risk factor three with no label."},
    ]

    client.generate_section(objective, chunks)

    messages = fake_client.messages.last_kwargs["messages"]
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    content = messages[0]["content"]

    assert objective in content
    for chunk in chunks:
        assert chunk["id"] in content
        assert chunk["text"] in content


def test_generate_section_does_not_set_thinking_or_temperature():
    fake_client = _FakeClient(_canned_result())
    client = ClaudeClient(fake_client)

    client.generate_section("objective text", [{"id": "c1", "label": "Item 1", "text": "some text"}])

    kwargs = fake_client.messages.last_kwargs
    assert "thinking" not in kwargs
    assert "temperature" not in kwargs
    assert kwargs["max_tokens"] == 16000
