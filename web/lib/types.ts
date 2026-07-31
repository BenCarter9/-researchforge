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
export interface FinancialRow {
  metric: string;
  key: string;
  values: Record<string, number | "unavailable">;
  yoy: number | "unavailable";
}

export interface FinancialsSection extends Section {
  table: FinancialRow[];
}

export interface Report {
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
