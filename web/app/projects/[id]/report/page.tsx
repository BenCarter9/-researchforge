"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { FinancialsTable } from "@/components/FinancialsTable";
import type { OpenedCitation } from "@/components/ClaimLine";
import { SectionView } from "@/components/SectionView";
import { SourceViewer } from "@/components/SourceViewer";
import { getReport } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { Report, YoyCalc } from "@/lib/types";

type TabId = "snapshot" | "business" | "financials" | "risks";

const TABS: Array<{ id: TabId; label: string }> = [
  { id: "snapshot", label: "Snapshot" },
  { id: "business", label: "Business" },
  { id: "financials", label: "Financials" },
  { id: "risks", label: "Risks" },
];

export default function ReportPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const [projectId, setProjectId] = useState<string | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabId>("snapshot");
  const [selectedCitation, setSelectedCitation] = useState<OpenedCitation | null>(
    null
  );
  const [selectedFormula, setSelectedFormula] = useState<{
    metric: string;
    calc: YoyCalc;
  } | null>(null);

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
    getReport(projectId)
      .then((result) => {
        if (!cancelled) setReport(result);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load report.");
        }
      });

    return () => {
      cancelled = true;
    };
  }, [projectId]);

  return (
    <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6 sm:py-14">
      {error && (
        <p role="alert" className="mb-6 text-sm text-[var(--bad)]">
          {error}
        </p>
      )}

      {!report && !error && (
        <p className="font-sans text-sm text-mute">Loading report…</p>
      )}

      {report && (
        <>
          <header className="mb-10 animate-fade-up border-b border-rule pb-8">
            <div className="flex flex-wrap items-baseline justify-between gap-4">
              <Link
                href="/"
                className="font-sans text-[0.7rem] font-medium uppercase tracking-[0.18em] text-mute hover:text-ink"
              >
                ResearchForge
              </Link>
              <Link
                href="/desk"
                className="font-sans text-sm font-medium text-accent underline-offset-4 hover:underline"
              >
                Open the desk
              </Link>
            </div>
            <h1 className="mt-3 font-display text-5xl tracking-tight text-ink sm:text-6xl">
              {report.project.ticker}
            </h1>
            <p className="mt-2 max-w-2xl font-serif text-xl text-mute">
              {report.project.company}
            </p>
            {report.project.research_date && (
              <p className="mt-3 font-sans text-xs tracking-wide text-mute">
                Research date {report.project.research_date}
              </p>
            )}
          </header>

          <div className="flex flex-col gap-8 lg:flex-row lg:items-start">
            <div className="min-w-0 flex-1">
              <nav
                aria-label="Report sections"
                className="mb-8 flex flex-wrap gap-1 border-b border-rule"
              >
                {TABS.map((tab) => (
                  <button
                    key={tab.id}
                    type="button"
                    onClick={() => setActiveTab(tab.id)}
                    aria-current={activeTab === tab.id ? "page" : undefined}
                    className={cn(
                      "relative px-3 py-3 font-sans text-sm transition-colors duration-150",
                      activeTab === tab.id
                        ? "text-ink after:absolute after:inset-x-0 after:bottom-0 after:h-0.5 after:bg-accent"
                        : "text-mute hover:text-ink"
                    )}
                  >
                    {tab.label}
                  </button>
                ))}
              </nav>

              <div
                key={activeTab}
                className="animate-fade-up rounded-sm border border-rule/80 bg-surface/70 px-1 sm:px-2"
              >
                {activeTab === "snapshot" && (
                  <SectionView
                    section={report.snapshot}
                    onOpenCitation={(citation) => {
                      setSelectedFormula(null);
                      setSelectedCitation(citation);
                    }}
                  />
                )}
                {activeTab === "business" && (
                  <SectionView
                    section={report.business}
                    onOpenCitation={(citation) => {
                      setSelectedFormula(null);
                      setSelectedCitation(citation);
                    }}
                  />
                )}
                {activeTab === "financials" && (
                  <div className="space-y-8 px-3 py-4 sm:px-4">
                    <FinancialsTable
                      table={report.financials.table}
                      onOpenFormula={(payload) => {
                        setSelectedCitation(null);
                        setSelectedFormula(payload);
                      }}
                    />
                    <div className="border-t border-rule pt-2">
                      <SectionView
                        section={report.financials}
                        onOpenCitation={(citation) => {
                          setSelectedFormula(null);
                          setSelectedCitation(citation);
                        }}
                      />
                    </div>
                  </div>
                )}
                {activeTab === "risks" && (
                  <SectionView
                    section={report.risks}
                    onOpenCitation={(citation) => {
                      setSelectedFormula(null);
                      setSelectedCitation(citation);
                    }}
                  />
                )}
              </div>
            </div>

            {(selectedCitation || selectedFormula) && (
              <aside className="w-full shrink-0 lg:sticky lg:top-8 lg:w-[22rem]">
                {selectedCitation && (
                  <SourceViewer
                    chunkId={selectedCitation.chunkId}
                    quote={selectedCitation.quote}
                    claimText={selectedCitation.claimText}
                    citationId={selectedCitation.citationId}
                    passage={selectedCitation.passage}
                    sectionLabel={selectedCitation.sectionLabel}
                    onClose={() => setSelectedCitation(null)}
                  />
                )}
                {selectedFormula && (
                  <div className="animate-slide-in space-y-4 rounded-sm bg-panel p-5 text-surface">
                    <div className="flex items-center justify-between border-b border-white/10 pb-3">
                      <h2 className="font-display text-lg tracking-tight text-surface">
                        Formula
                      </h2>
                      <button
                        type="button"
                        onClick={() => setSelectedFormula(null)}
                        aria-label="Close formula panel"
                        className="text-xs text-surface/60 hover:text-surface"
                      >
                        Close
                      </button>
                    </div>
                    <p className="font-serif text-sm text-surface/90">
                      {selectedFormula.metric} YoY
                    </p>
                    <p className="font-sans text-sm">
                      <code>{selectedFormula.calc.formula}</code>
                    </p>
                    <dl className="space-y-1 font-sans text-xs text-surface/70">
                      {Object.entries(selectedFormula.calc.inputs).map(
                        ([name, value]) => (
                          <div key={name} className="flex justify-between gap-4">
                            <dt>{name}</dt>
                            <dd className="tabular-nums">
                              {value == null ? "unavailable" : value.toLocaleString("en-US")}
                            </dd>
                          </div>
                        )
                      )}
                    </dl>
                    <p className="font-sans text-xs text-surface/50">
                      Deterministic Python arithmetic. The model does not compute this.
                    </p>
                  </div>
                )}
              </aside>
            )}
          </div>
        </>
      )}
    </main>
  );
}
