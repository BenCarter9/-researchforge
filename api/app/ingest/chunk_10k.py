from __future__ import annotations

import re
from dataclasses import dataclass

from selectolax.parser import HTMLParser


@dataclass
class Chunk:
    section_label: str
    text: str


_ITEM_LABELS = {"1": "item_1", "1A": "item_1a", "7": "item_7", "8": "item_8"}
# Matches ANY item header (1, 1A, 1B, 2, ..., 7A, 8, ...) so that untracked
# items still act as boundaries that terminate the preceding tracked section.
# Only the tracked labels above are kept in the output.
#
# Anchored at line start so mid-sentence cross-references
# ("...Results of Operations in Item 7 and our consolidated...") are not
# treated as section boundaries. Real 10-K body/TOC headers are line-leading
# after HTML→text extraction.
_ITEM_RE = re.compile(r"(?m)^\s*Item\s+(\d+[A-Z]?)\b\.?", re.IGNORECASE)


def chunk_10k(html: str) -> list[Chunk]:
    text = HTMLParser(html).text(separator="\n")
    text = re.sub(r"[ \t]+", " ", text)
    matches = list(_ITEM_RE.finditer(text))
    out: dict[str, str] = {}
    for i, m in enumerate(matches):
        num = m.group(1).upper()
        label = _ITEM_LABELS.get(num)
        if not label:
            continue
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        # keep the longest capture if an item header appears twice (TOC + body)
        if len(body) > len(out.get(label, "")):
            out[label] = body
    return [Chunk(section_label=k, text=v) for k, v in out.items()]
