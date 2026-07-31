import { describe, expect, it } from "vitest";

import { humanizeStageName, pipelineState } from "./pipeline";
import type { StageStatus } from "./types";

function stage(
  name: string,
  status: StageStatus["status"],
  error: string | null = null
): StageStatus {
  return { stage: name, status, error };
}

describe("pipelineState", () => {
  it("is 'empty' for an empty list", () => {
    expect(pipelineState([])).toBe("empty");
  });

  it("is 'done' when non-empty and every stage is done", () => {
    const stages = [stage("fetch_filing", "done"), stage("chunk", "done")];
    expect(pipelineState(stages)).toBe("done");
  });

  it("is 'error' when any stage has errored, regardless of others", () => {
    const stages = [
      stage("fetch_filing", "done"),
      stage("chunk", "error", "boom"),
      stage("extract_claims", "pending"),
    ];
    expect(pipelineState(stages)).toBe("error");
  });

  it("is 'running' for a mix of running/pending/done with no error", () => {
    const stages = [
      stage("fetch_filing", "done"),
      stage("chunk", "running"),
      stage("extract_claims", "pending"),
    ];
    expect(pipelineState(stages)).toBe("running");
  });
});

describe("humanizeStageName", () => {
  it("converts snake_case to a capitalized phrase", () => {
    expect(humanizeStageName("fetch_filing")).toBe("Fetch filing");
    expect(humanizeStageName("extract_claims")).toBe("Extract claims");
    expect(humanizeStageName("chunk")).toBe("Chunk");
  });
});
