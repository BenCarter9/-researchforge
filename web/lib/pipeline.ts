import type { StageStatus } from "./types";

export type PipelineState = "empty" | "running" | "done" | "error";

// Pure helper: derives the overall pipeline state from the list of stage
// statuses returned by `getStatus`. Used by the processing page to decide
// when to stop polling and where to route next.
export function pipelineState(stages: StageStatus[]): PipelineState {
  if (stages.some((s) => s.status === "error")) return "error";
  if (stages.length > 0 && stages.every((s) => s.status === "done")) return "done";
  if (stages.length === 0) return "empty";
  return "running";
}

// "fetch_filing" -> "Fetch filing"
export function humanizeStageName(stage: string): string {
  const withSpaces = stage.replace(/[_-]+/g, " ").trim();
  if (!withSpaces) return withSpaces;
  return withSpaces.charAt(0).toUpperCase() + withSpaces.slice(1);
}
