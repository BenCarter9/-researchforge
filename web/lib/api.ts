import type { Chunk, Report, StageStatus } from "./types";

// All requests use relative URLs so the Next.js rewrite in next.config.mjs
// (`/api/:path*` -> the FastAPI backend) handles routing in both dev and
// production.

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text);
  }
  return (await res.json()) as T;
}

export async function createProject(input: {
  company: string;
  ticker: string;
  research_date?: string;
}): Promise<{ project_id: string }> {
  const res = await fetch("/api/projects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  return json(res);
}

export async function uploadTranscript(
  projectId: string,
  input: { text: string; label: string }
): Promise<{ document_id: string; chunk_count: number }> {
  const res = await fetch(`/api/projects/${projectId}/transcript`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  return json(res);
}

export async function startAnalysis(projectId: string): Promise<{ status: string }> {
  const res = await fetch(`/api/projects/${projectId}/analyze`, {
    method: "POST",
  });
  return json(res);
}

export async function getStatus(projectId: string): Promise<StageStatus[]> {
  const res = await fetch(`/api/projects/${projectId}/status`);
  return json(res);
}

export async function getReport(projectId: string): Promise<Report> {
  const res = await fetch(`/api/projects/${projectId}/report`);
  return json(res);
}

export async function getChunk(chunkId: string): Promise<Chunk> {
  const res = await fetch(`/api/chunks/${chunkId}`);
  return json(res);
}

export async function markCitation(
  citationId: string,
  valid: boolean
): Promise<{ ok: boolean }> {
  const res = await fetch(`/api/citations/${citationId}/mark`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ valid }),
  });
  return json(res);
}
