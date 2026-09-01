"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { DeskView } from "@/components/DeskView";
import { getDesk } from "@/lib/api";
import deskSeed from "@/lib/deskSeed.json";
import type { DeskPayload } from "@/lib/types";

const INITIAL_DESK = deskSeed as DeskPayload;

export default function DeskPage() {
  const [desk, setDesk] = useState<DeskPayload>(INITIAL_DESK);

  useEffect(() => {
    let cancelled = false;
    getDesk()
      .then((payload) => {
        if (!cancelled) setDesk(payload);
      })
      .catch(() => {
        // Keep the first-paint seed if the API is down.
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
      <div className="mt-8">
        <DeskView desk={desk} />
      </div>
    </main>
  );
}
