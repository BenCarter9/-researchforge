"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { DeskView } from "@/components/DeskView";
import { getDesk } from "@/lib/api";
import type { DeskPayload } from "@/lib/types";

export default function DeskPage() {
  const [desk, setDesk] = useState<DeskPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getDesk()
      .then((payload) => {
        if (!cancelled) setDesk(payload);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load desk.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="mx-auto max-w-5xl px-4 py-12 sm:px-6 sm:py-16">
      <Link
        href="/"
        className="font-display text-lg tracking-tight text-ink transition-colors hover:text-accent"
      >
        ResearchForge
      </Link>
      <p className="mt-8 font-sans text-[0.7rem] font-medium uppercase tracking-[0.2em] text-mute">
        Workflow-tools desk
      </p>
      <h1 className="mt-3 font-display text-5xl tracking-tight text-ink sm:text-6xl">
        Desk
      </h1>

      {error && (
        <p role="alert" className="mt-8 font-sans text-sm text-[var(--bad)]">
          {error}
        </p>
      )}

      {!desk && !error && (
        <p className="mt-8 font-sans text-sm text-mute">Loading desk…</p>
      )}

      {desk && (
        <div className="mt-8">
          <DeskView desk={desk} />
        </div>
      )}
    </main>
  );
}
