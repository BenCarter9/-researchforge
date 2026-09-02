import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { DeskView } from "./DeskView";
import type { DeskCall, DeskMemo, DeskPayload } from "@/lib/types";

vi.mock("@/lib/api", () => ({
  draftDeskMemo: vi.fn(),
}));

import { draftDeskMemo } from "@/lib/api";

function source(quote: string) {
  return {
    publisher: "Example",
    date: "2026-04-29",
    url: "https://example.com/source",
    verbatim_quote: quote,
  };
}

const rogo: DeskCall = {
  id: "rogo",
  company: "Rogo",
  proposed: "TAKE",
  headline: "Finance-native agents",
  summary: "Company-announced $160 million Series D. A human must confirm.",
  facts: [
    {
      id: "rogo-series-d",
      text: "Rogo announced $160 million in Series D funding on April 29, 2026.",
      kind: "reported_fact",
      source: source("raised $160 million in Series D funding"),
    },
  ],
  unverified: [
    "Secondary coverage has circulated a ~$2B valuation. That figure is unverified here and is not treated as fact.",
  ],
};

const fiscal: DeskCall = {
  id: "fiscal-ai",
  company: "Fiscal.ai (formerly FinChat)",
  proposed: "PASS",
  headline: "Public-data chat wrapper",
  summary: "$10 million Series A; over 350,000 registered users.",
  facts: [
    {
      id: "fiscal-users",
      text: "Fiscal.ai reported already over 350,000 registered users.",
      kind: "management_claim",
      source: source("already over 350,000 registered users"),
    },
  ],
  unverified: [],
};

const precomputed: DeskMemo = {
  model_id: "zai-org/GLM-5.2",
  model_license: "MIT",
  weights_url: "https://huggingface.co/zai-org/GLM-5.2",
  source: "cached",
  label:
    "Cached GLM-5.2 draft (zai-org/GLM-5.2). Same prompt as a live call — expand Exact prompt and model id. Confirm TAKE/PASS yourself.",
  draft: "Precomputed TAKE Rogo / PASS Fiscal.ai. Human confirms TAKE/PASS.",
  prompt: "USER PROMPT BODY",
  system_prompt: "SYSTEM PROMPT BODY",
  live_available: false,
  key_name: null,
  request_model: null,
  human_owns_call: true,
};

const desk: DeskPayload = {
  model_id: "zai-org/GLM-5.2",
  model_license: "MIT",
  weights_url: "https://huggingface.co/zai-org/GLM-5.2",
  live_available: false,
  key_name: null,
  request_model: null,
  prompt: "USER PROMPT BODY",
  system_prompt: "SYSTEM PROMPT BODY",
  calls: [rogo, fiscal],
  human_owns_call: true,
  precomputed,
};

describe("DeskView", () => {
  beforeEach(() => {
    vi.mocked(draftDeskMemo).mockReset();
  });

  it("shows TAKE/PASS cards, citations, model id, and a labeled precomputed draft", async () => {
    const user = userEvent.setup();
    render(<DeskView desk={desk} />);

    expect(screen.getByRole("heading", { name: "Rogo" })).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Fiscal.ai (formerly FinChat)" })
    ).toBeInTheDocument();
    expect(screen.getAllByText(/draft take/i)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/draft pass/i)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/\$160 million/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/350,000 registered users/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/unverified — not treated as fact/i)).toBeInTheDocument();
    expect(screen.getAllByText(/zai-org\/GLM-5.2/).length).toBeGreaterThan(0);
    expect(screen.getByRole("status")).toHaveTextContent(/cached GLM-5.2 draft/i);

    await user.click(screen.getByText("Exact prompt and model id"));
    expect(screen.getByText("USER PROMPT BODY")).toBeInTheDocument();
    expect(screen.getByText("SYSTEM PROMPT BODY")).toBeInTheDocument();
  });

  it("lets the human confirm TAKE/PASS independently of the model draft", async () => {
    const user = userEvent.setup();
    render(<DeskView desk={desk} />);

    expect(screen.getAllByText(/awaiting your call/i)).toHaveLength(2);
    await user.click(screen.getByRole("button", { name: /confirm take/i }));
    expect(screen.getByText(/confirmed by you/i)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /confirm pass/i }));
    expect(screen.getAllByText(/confirmed by you/i)).toHaveLength(2);
    await user.click(screen.getAllByRole("button", { name: /reject draft/i })[1]);
    expect(screen.getByText(/rejected by you/i)).toBeInTheDocument();
  });

  it("requests a memo draft and replaces the precomputed text when the API returns live output", async () => {
    vi.mocked(draftDeskMemo).mockResolvedValue({
      ...precomputed,
      source: "live",
      label: "Live GLM-5.2 draft (zai-org/GLM-5.2)",
      draft: "Live memo from GLM-5.2. Human confirms TAKE/PASS.",
      live_available: true,
      key_name: "GLM_API_KEY",
    });
    const user = userEvent.setup();
    render(<DeskView desk={desk} />);

    await user.click(screen.getByRole("button", { name: /cached GLM-5.2 draft/i }));
    await waitFor(() => {
      expect(draftDeskMemo).toHaveBeenCalledTimes(1);
    });
    expect(screen.getByRole("status")).toHaveTextContent(/live GLM-5.2 draft/i);
    expect(screen.getByText(/live memo from GLM-5.2/i)).toBeInTheDocument();
  });
});
