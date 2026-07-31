"use client";

import { useEffect, useState } from "react";

import { FinancialsTable } from "@/components/FinancialsTable";
import type { OpenedCitation } from "@/components/ClaimLine";
import { SectionView } from "@/components/SectionView";
import { SourceViewer } from "@/components/SourceViewer";
import { Card } from "@/components/ui/Card";
import { getReport } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { Report } from "@/lib/types";

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
    <main className="mx-auto max-w-5xl px-4 py-12">
      <h1 className="mb-6 text-2xl font-semibold text-slate-900">Report</h1>

      {error && (
        <p role="alert" className="mb-4 text-sm text-red-600">
          {error}
        </p>
      )}

      {!report && !error && (
        <p className="text-sm text-slate-500">Loading report…</p>
      )}

      {report && (
        <div className="flex flex-col gap-6 lg:flex-row">
          <div className="min-w-0 flex-1">
            <nav
              aria-label="Report sections"
              className="mb-6 flex gap-2 border-b border-slate-200"
            >
              {TABS.map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveTab(tab.id)}
                  aria-current={activeTab === tab.id ? "page" : undefined}
                  className={cn(
                    "border-b-2 px-3 py-2 text-sm font-medium transition-colors",
                    activeTab === tab.id
                      ? "border-slate-900 text-slate-900"
                      : "border-transparent text-slate-500 hover:text-slate-800"
                  )}
                >
                  {tab.label}
                </button>
              ))}
            </nav>

            <Card>
              {activeTab === "snapshot" && (
                <SectionView
                  section={report.snapshot}
                  onOpenCitation={setSelectedCitation}
                />
              )}
              {activeTab === "business" && (
                <SectionView
                  section={report.business}
                  onOpenCitation={setSelectedCitation}
                />
              )}
              {activeTab === "financials" && (
                <div className="space-y-6">
                  <FinancialsTable table={report.financials.table} />
                  <SectionView
                    section={report.financials}
                    onOpenCitation={setSelectedCitation}
                  />
                </div>
              )}
              {activeTab === "risks" && (
                <SectionView
                  section={report.risks}
                  onOpenCitation={setSelectedCitation}
                />
              )}
            </Card>
          </div>

          {selectedCitation && (
            <aside className="w-full shrink-0 lg:w-80">
              <Card>
                <SourceViewer
                  chunkId={selectedCitation.chunkId}
                  quote={selectedCitation.quote}
                  claimText={selectedCitation.claimText}
                  citationId={selectedCitation.citationId}
                  onClose={() => setSelectedCitation(null)}
                />
              </Card>
            </aside>
          )}
        </div>
      )}
    </main>
  );
}
