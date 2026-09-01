from __future__ import annotations

# Canonical open-weight id shown in the UI even when the HTTP request
# model string differs by provider (OpenRouter vs Z.ai).
MODEL_ID = "zai-org/GLM-5.2"
MODEL_LICENSE = "MIT"
MODEL_WEIGHTS_URL = "https://huggingface.co/zai-org/GLM-5.2"

# Sourced, private-company workflow-tool calls. Every dollar figure and
# customer name below is copied from a cited company or wire source.
# Unverified items stay labeled and are never used as facts.

CALLS: list[dict] = [
    {
        "id": "rogo",
        "company": "Rogo",
        "proposed": "TAKE",
        "headline": "Finance-native agents with named IB distribution",
        "summary": (
            "Company-announced $160 million Series D (April 2026) for an "
            "agentic platform purpose-built for finance. Named investment-bank "
            "users include Rothschild & Co, Jefferies, Lazard, Moelis, and "
            "Nomura. Draft TAKE is about workflow-tool fit, not a public "
            "security. A human must confirm."
        ),
        "facts": [
            {
                "id": "rogo-series-d",
                "text": (
                    "Rogo announced $160 million in Series D funding on "
                    "April 29, 2026."
                ),
                "kind": "reported_fact",
                "source": {
                    "publisher": "PR Newswire (Rogo company announcement)",
                    "date": "2026-04-29",
                    "url": (
                        "https://www.prnewswire.com/news-releases/"
                        "rogo-raises-160m-series-d-to-scale-the-agentic-platform-"
                        "for-finance-302756546.html"
                    ),
                    "verbatim_quote": (
                        "Rogo, the AI platform purpose-built for finance, today "
                        "announced it has raised $160 million in Series D funding "
                        "led by Kleiner Perkins"
                    ),
                },
            },
            {
                "id": "rogo-felix",
                "text": (
                    "Rogo describes Felix as agentic AI that executes complex, "
                    "multi-step financial processes autonomously."
                ),
                "kind": "management_claim",
                "source": {
                    "publisher": "PR Newswire (Rogo company announcement)",
                    "date": "2026-04-29",
                    "url": (
                        "https://www.prnewswire.com/news-releases/"
                        "rogo-raises-160m-series-d-to-scale-the-agentic-platform-"
                        "for-finance-302756546.html"
                    ),
                    "verbatim_quote": (
                        "The company recently introduced Felix, its agentic AI "
                        "that executes complex, multi-step financial processes "
                        "autonomously"
                    ),
                },
            },
            {
                "id": "rogo-ibs",
                "text": (
                    "Named institutional users include Rothschild & Co, "
                    "Jefferies, Lazard, Moelis, and Nomura."
                ),
                "kind": "management_claim",
                "source": {
                    "publisher": "PR Newswire (Rogo company announcement)",
                    "date": "2026-04-29",
                    "url": (
                        "https://www.prnewswire.com/news-releases/"
                        "rogo-raises-160m-series-d-to-scale-the-agentic-platform-"
                        "for-finance-302756546.html"
                    ),
                    "verbatim_quote": (
                        "More than 35,000 financial professionals at over 250 "
                        "institutions, including Rothschild & Co, Jefferies, "
                        "Lazard, Moelis, Nomura, and others, leverage Rogo in "
                        "their daily workflows"
                    ),
                },
            },
        ],
        "unverified": [
            (
                "Secondary coverage has circulated a ~$2B valuation. That "
                "figure is unverified here and is not treated as fact."
            )
        ],
    },
    {
        "id": "fiscal-ai",
        "company": "Fiscal.ai (formerly FinChat)",
        "proposed": "PASS",
        "headline": "Public-data chat wrapper; $10M Series A; 350k users",
        "summary": (
            "Company-announced rebrand from FinChat with a $10 million Series A "
            "and more than 350,000 registered users. Origin is querying public "
            "financial data at scale via chat; the company now also sells a "
            "terminal and APIs. Draft PASS is about workflow-tool fit versus "
            "finance-native agents with named IB distribution. A human must "
            "confirm."
        ),
        "facts": [
            {
                "id": "fiscal-rebrand-series-a",
                "text": (
                    "FinChat rebranded to Fiscal.ai and announced a $10 million "
                    "USD Series A."
                ),
                "kind": "reported_fact",
                "source": {
                    "publisher": "Fiscal.ai (company blog)",
                    "date": "2025-06",
                    "url": "https://fiscal.ai/blog/series-a-announcement/",
                    "verbatim_quote": (
                        "We have officially rebranded to Fiscal.ai to build the "
                        "future of financial data and AI. With this, we are "
                        "excited to announce our $10M USD Series A funding led "
                        "by Portage"
                    ),
                },
            },
            {
                "id": "fiscal-users",
                "text": (
                    "Fiscal.ai reported already over 350,000 registered users "
                    "at the Series A announcement."
                ),
                "kind": "management_claim",
                "source": {
                    "publisher": "Fiscal.ai (company blog)",
                    "date": "2025-06",
                    "url": "https://fiscal.ai/blog/series-a-announcement/",
                    "verbatim_quote": (
                        "With already over 350,000 registered users and top "
                        "fintech platforms worldwide leveraging Fiscal.ai’s APIs "
                        "to serve millions of end users"
                    ),
                },
            },
            {
                "id": "fiscal-chat-origin",
                "text": (
                    "Fiscal.ai launched as FinChat in 2023 to query financial "
                    "data at scale; the company later described the chat "
                    "interface as a feature rather than the core product."
                ),
                "kind": "management_claim",
                "source": {
                    "publisher": "Fiscal.ai (company blog)",
                    "date": "2025-06",
                    "url": "https://fiscal.ai/blog/series-a-announcement/",
                    "verbatim_quote": (
                        "When we launched FinChat in 2023, our mission was to "
                        "empower everyone to query financial data at scale. As "
                        "we’ve grown, so have our ambitions — beyond the Chat "
                        "interface."
                    ),
                },
            },
        ],
        "unverified": [],
    },
]


SYSTEM_PROMPT = """\
You are drafting a short desk memo for an equity-research workflow-tools screen.
Use ONLY the sourced facts in the user message. Do not invent funding, customers, \
revenue, valuation, or other financials. If a figure is labeled unverified, say \
so and do not treat it as fact. Do not issue a buy/sell recommendation as a \
settled call — propose TAKE/PASS and state that a human must confirm. Cite \
sources by publisher and date. Keep the memo under 250 words.
"""


def build_user_prompt(calls: list[dict] | None = None) -> str:
    """Exact user prompt sent to GLM-5.2 (and shown when falling back)."""
    rows = calls if calls is not None else CALLS
    parts = [
        "Draft a memo that proposes TAKE on Rogo and PASS on Fiscal.ai "
        "(formerly FinChat) as AI-in-finance *workflow tools*, not as public "
        "equities. Ground every sentence in the sourced facts below. Do not "
        "add numbers that are not listed. End with: Human confirms TAKE/PASS.",
        "",
        "SOURCED CALLS",
    ]
    for call in rows:
        parts.append(f"\n## {call['company']} — proposed {call['proposed']}")
        parts.append(call["summary"])
        for fact in call["facts"]:
            src = fact["source"]
            parts.append(
                f"- [{fact['id']}] {fact['text']}\n"
                f"  source: {src['publisher']} ({src['date']}) {src['url']}\n"
                f"  quote: {src['verbatim_quote']!r}"
            )
        for note in call["unverified"]:
            parts.append(f"- UNVERIFIED (do not treat as fact): {note}")
    return "\n".join(parts)


MEMO_PROMPT = build_user_prompt()

PRECOMPUTED_DRAFT = """\
Cached GLM-5.2 desk memo (zai-org/GLM-5.2)

Proposed: TAKE Rogo · PASS Fiscal.ai (formerly FinChat)
Scope: AI-in-finance workflow tools. Not a public-equity recommendation.

TAKE — Rogo
Rogo’s April 29, 2026 company announcement (PR Newswire) states it is “the AI \
platform purpose-built for finance” and that it “has raised $160 million in \
Series D funding led by Kleiner Perkins.” The same announcement introduces \
Felix as “agentic AI that executes complex, multi-step financial processes \
autonomously,” and names Rothschild & Co, Jefferies, Lazard, Moelis, and \
Nomura among institutions using the product. That is finance-native agents \
plus named IB distribution, which is the TAKE screen here.

A ~$2B valuation appearing in secondary coverage is unverified and is not \
used as a fact.

PASS — Fiscal.ai (formerly FinChat)
Fiscal.ai’s own Series A post announces a rebrand from FinChat and “$10M USD \
Series A funding led by Portage,” and says it already had “over 350,000 \
registered users.” The same post says FinChat launched in 2023 “to empower \
everyone to query financial data at scale” and that ambitions moved “beyond \
the Chat interface.” That is a public-data chat/query wrapper (now also \
terminal + API), not named IB agent distribution. PASS vs Rogo on this screen.

Human confirms TAKE/PASS. Model drafts; the analyst owns the call.
"""
