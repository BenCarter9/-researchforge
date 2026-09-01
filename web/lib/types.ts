// Types mirroring the FastAPI response shapes exactly.
// See api/app/routes/report.py, api/app/routes/projects.py,
// api/app/llm/schema.py, and api/app/finance/engine.py.

export type EvidenceStatus = "green" | "yellow" | "red" | "gray";

export type ClaimType =
  | "reported_fact"
  | "management_claim"
  | "analyst_inference"
  | "assumption"
  | "unsupported";

export interface Citation {
  id: string;
  chunk_id: string;
  verbatim_quote: string;
  verbatim_verified: boolean;
  passage?: string | null;
  section_label?: string | null;
}

export interface Claim {
  id: string;
  claim_text: string;
  claim_type: ClaimType;
  evidence_status: EvidenceStatus;
  citation: Citation | null;
}

export interface Section {
  claims: Claim[];
}

// Financial table row: `values` maps a fiscal-year label (e.g. "FY2025") to
// either a number or the string "unavailable" when the underlying fact is
// missing. `yoy` is similarly a number or "unavailable".
export interface YoyCalc {
  metric: string;
  formula: string;
  inputs: Record<string, number | null>;
  result: number | null;
  unit: string;
  period: string | null;
}

export interface FinancialRow {
  metric: string;
  key: string;
  values: Record<string, number | "unavailable">;
  yoy: number | "unavailable";
  yoy_calc?: YoyCalc | null;
}

export interface FinancialsSection extends Section {
  table: FinancialRow[];
}

export interface Report {
  project: {
    id: string;
    company: string;
    ticker: string;
    research_date: string | null;
    status: string;
  };
  snapshot: Section;
  business: Section;
  financials: FinancialsSection;
  risks: Section;
}

export interface Chunk {
  document_id: string;
  section_label: string;
  page_start: number | null;
  page_end: number | null;
  speaker: string | null;
  text: string;
}

export interface StageStatus {
  stage: string;
  status: "pending" | "running" | "done" | "error";
  error: string | null;
}

export interface DeskSource {
  publisher: string;
  date: string;
  url: string;
  verbatim_quote: string;
}

export interface DeskFact {
  id: string;
  text: string;
  kind: string;
  source: DeskSource;
}

export interface DeskCall {
  id: string;
  company: string;
  proposed: "TAKE" | "PASS";
  headline: string;
  summary: string;
  facts: DeskFact[];
  unverified: string[];
}

export interface DeskMemo {
  model_id: string;
  model_license: string;
  weights_url: string;
  source: "live" | "cached";
  label: string;
  draft: string;
  prompt: string;
  system_prompt: string;
  live_available: boolean;
  key_name: string | null;
  request_model: string | null;
  human_owns_call: boolean;
}

export interface DeskPayload {
  model_id: string;
  model_license: string;
  weights_url: string;
  live_available: boolean;
  key_name: string | null;
  request_model: string | null;
  prompt: string;
  system_prompt: string;
  calls: DeskCall[];
  human_owns_call: boolean;
  precomputed: DeskMemo;
}
