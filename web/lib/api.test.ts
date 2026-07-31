import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { getReport } from "./api";
import type { Report } from "./types";

const mockReport: Report = {
  snapshot: {
    claims: [
      {
        id: "claim-1",
        claim_text: "Revenue grew 12% year over year.",
        claim_type: "reported_fact",
        evidence_status: "green",
        citation: {
          id: "cit-1",
          chunk_id: "chunk-1",
          verbatim_quote: "revenue grew 12% year over year",
          verbatim_verified: true,
        },
      },
      {
        id: "claim-2",
        claim_text: "Management expects continued momentum.",
        claim_type: "management_claim",
        evidence_status: "gray",
        citation: null,
      },
    ],
  },
  business: { claims: [] },
  financials: {
    claims: [],
    table: [
      {
        metric: "Revenue",
        key: "revenue",
        values: { FY2024: 1000, FY2025: "unavailable" },
        yoy: "unavailable",
      },
    ],
  },
  risks: { claims: [] },
};

describe("getReport", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("fetches the report from the correct endpoint and parses it into the typed Report shape", async () => {
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: async () => mockReport,
      text: async () => "",
    });

    const report = await getReport("p1");

    expect(fetch).toHaveBeenCalledTimes(1);
    expect(fetch).toHaveBeenCalledWith("/api/projects/p1/report");

    // A fiscal-year key round-trips as a number.
    expect(report.financials.table[0].values["FY2024"]).toBe(1000);
    // An "unavailable" cell round-trips as the literal string, not coerced.
    expect(report.financials.table[0].values["FY2025"]).toBe("unavailable");
    expect(typeof report.financials.table[0].values["FY2025"]).toBe("string");
    expect(report.financials.table[0].yoy).toBe("unavailable");

    // A claim's citation can be null.
    expect(report.snapshot.claims[1].citation).toBeNull();
    // And non-null citations retain their fields.
    expect(report.snapshot.claims[0].citation).toEqual({
      id: "cit-1",
      chunk_id: "chunk-1",
      verbatim_quote: "revenue grew 12% year over year",
      verbatim_verified: true,
    });
  });

  it("throws with the response body when the request is not OK", async () => {
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({}),
      text: async () => "project not found",
    });

    await expect(getReport("missing")).rejects.toThrow("project not found");
  });
});
