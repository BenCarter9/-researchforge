"use client";

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
    <main className="mx-auto max-w-lg px-4 py-12">
      <h1 className="mb-6 text-2xl font-semibold text-slate-900">
        Generating report…
      </h1>
      <Card>
        {pollError && (
          <p role="alert" className="mb-4 text-sm text-red-600">
            {pollError}
          </p>
        )}
        <StageList stages={stages} />
      </Card>
    </main>
  );
}
