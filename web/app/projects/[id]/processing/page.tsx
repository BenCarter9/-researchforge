"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { StageList } from "@/components/StageList";
import { Card } from "@/components/ui/Card";
import { getStatus } from "@/lib/api";
import { pipelineState } from "@/lib/pipeline";
import type { StageStatus } from "@/lib/types";

const POLL_INTERVAL_MS = 2000;

export default function ProcessingPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const router = useRouter();
  const [projectId, setProjectId] = useState<string | null>(null);
  const [stages, setStages] = useState<StageStatus[]>([]);
  const [pollError, setPollError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    params.then(({ id }) => {
      if (!cancelled) setProjectId(id);
    });
    return () => {
      cancelled = true;
    };
  }, [params]);

  useEffect(() => {
    if (!projectId) return;

    let cancelled = false;

    async function poll() {
      try {
        const result = await getStatus(projectId as string);
        if (cancelled) return;
        setStages(result);

        const state = pipelineState(result);
        if (state === "done" || state === "error") {
          clearInterval(intervalId);
          if (state === "done") {
            router.push(`/projects/${projectId}/report`);
          }
        }
      } catch (err) {
        if (!cancelled) {
          setPollError(
            err instanceof Error ? err.message : "Failed to fetch status."
          );
        }
      }
    }

    const intervalId = setInterval(poll, POLL_INTERVAL_MS);
    poll();

    return () => {
      cancelled = true;
      clearInterval(intervalId);
    };
  }, [projectId, router]);

  return (
    <main className="mx-auto max-w-lg px-4 py-12 sm:py-16">
      <Link
        href="/"
        className="font-display text-lg tracking-tight text-ink transition-colors hover:text-accent"
      >
        ResearchForge
      </Link>
      <h1 className="mt-8 font-display text-3xl tracking-tight text-ink">
        Generating report…
      </h1>
      <p className="mt-2 font-serif text-mute">
        Fetching filings, extracting financials, and drafting cited sections.
      </p>
      <Card className="mt-8">
        {pollError && (
          <p role="alert" className="mb-4 text-sm text-[var(--bad)]">
            {pollError}
          </p>
        )}
        <StageList stages={stages} />
      </Card>
    </main>
  );
}
