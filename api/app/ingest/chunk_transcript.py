from __future__ import annotations

import re
from dataclasses import dataclass

_QA_MARKER_RE = re.compile(r"question-and-answer|\bq&a\b", re.IGNORECASE)
_CEO_RE = re.compile(r"chief executive officer", re.IGNORECASE)
_CFO_RE = re.compile(r"chief financial officer", re.IGNORECASE)


@dataclass
class Chunk:
    section_label: str
    text: str
    speaker: str | None = None


def _speaker_name(line: str) -> str:
    # Speaker lines look like "Jane Smith — Chief Executive Officer"; take
    # whatever precedes the role-indicating separator/title as the name.
    name = re.split(r"[—\-:]", line, maxsplit=1)[0].strip()
    return name or line.strip()


def chunk_transcript(text: str) -> list[Chunk]:
    qa_match = _QA_MARKER_RE.search(text)
    if qa_match:
        prepared_text = text[: qa_match.start()]
        qa_text = text[qa_match.start() :]
    else:
        prepared_text = text
        qa_text = None

    lines = prepared_text.splitlines(keepends=True)

    ceo_segments: list[str] = []
    cfo_segments: list[str] = []
    ceo_speaker: str | None = None
    cfo_speaker: str | None = None

    current_role: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        if current_role == "ceo" and current_lines:
            ceo_segments.append("".join(current_lines))
        elif current_role == "cfo" and current_lines:
            cfo_segments.append("".join(current_lines))

    for line in lines:
        if _CEO_RE.search(line):
            flush()
            current_role = "ceo"
            current_lines = [line]
            if ceo_speaker is None:
                ceo_speaker = _speaker_name(line) or "Chief Executive Officer"
        elif _CFO_RE.search(line):
            flush()
            current_role = "cfo"
            current_lines = [line]
            if cfo_speaker is None:
                cfo_speaker = _speaker_name(line) or "Chief Financial Officer"
        elif current_role is not None:
            current_lines.append(line)
    flush()

    out: list[Chunk] = []
    if ceo_segments:
        out.append(
            Chunk(
                section_label="prepared_remarks_ceo",
                text="".join(ceo_segments),
                speaker=ceo_speaker or "Chief Executive Officer",
            )
        )
    if cfo_segments:
        out.append(
            Chunk(
                section_label="prepared_remarks_cfo",
                text="".join(cfo_segments),
                speaker=cfo_speaker or "Chief Financial Officer",
            )
        )
    if qa_text is not None:
        out.append(Chunk(section_label="qa", text=qa_text, speaker=None))

    return out
