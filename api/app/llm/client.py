from __future__ import annotations

from app.llm.prompts import SYSTEM_PROMPT
from app.llm.schema import SectionResult


class ClaudeClient:
    """Thin wrapper around the Anthropic SDK for structured section generation.

    The underlying `anthropic.Anthropic` client is injected via the
    constructor so this class can be unit tested with a fake client and
    no network access or API key.
    """

    def __init__(self, anthropic_client, model: str = "claude-opus-5"):
        self._client = anthropic_client
        self._model = model

    def generate_section(self, objective: str, chunks: list[dict]) -> SectionResult:
        user_content = self._render(objective, chunks)
        resp = self._client.messages.parse(
            model=self._model,
            max_tokens=16000,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            output_format=SectionResult,
            messages=[{"role": "user", "content": user_content}],
        )
        return resp.parsed_output

    @staticmethod
    def _render(objective: str, chunks: list[dict]) -> str:
        parts = [objective]
        for chunk in chunks:
            chunk_id = chunk["id"]
            section_label = chunk.get("section_label") or chunk.get("label")
            text = chunk["text"]
            parts.append(
                f"\n--- chunk_id: {chunk_id} (section {section_label}) ---\n{text}\n"
            )
        return "".join(parts)
