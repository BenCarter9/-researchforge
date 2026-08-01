"use client";

import { useEffect, useState } from "react";

import { getChunk, markCitation } from "@/lib/api";
import type { Chunk } from "@/lib/types";

export interface SourceViewerProps {
  chunkId: string;
  quote: string;
  claimText: string;
  citationId: string;
  onClose?: () => void;
}

// "prepared_remarks_cfo" -> "Prepared remarks cfo"
function humanizeSectionLabel(label: string): string {
  const withSpaces = label.replace(/_/g, " ");
  return withSpaces.charAt(0).toUpperCase() + withSpaces.slice(1);
}

function pageRangeLabel(chunk: Chunk): string | null {
  if (chunk.page_start == null) return null;
  if (chunk.page_end != null && chunk.page_end !== chunk.page_start) {
    return `Pages ${chunk.page_start}–${chunk.page_end}`;
  }
  return `Page ${chunk.page_start}`;
}

type MarkedState = "valid" | "invalid" | null;

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

interface QuoteMatch {
  start: number;
  length: number;
}

// Locate `quote` inside `text` tolerating whitespace differences (the
// backend's verbatim_verify collapses runs of whitespace, including
// newlines, before comparing). Returns the span in the ORIGINAL text that
// matched, so the highlight covers the exact original characters (e.g. a
// quote written with single spaces can match text containing a newline).
function findQuoteMatch(text: string, quote: string): QuoteMatch | null {
  if (!quote) return null;
  const pattern = escapeRegExp(quote).replace(/\s+/g, "\\s+");
  let regex: RegExp;
  try {
    regex = new RegExp(pattern);
  } catch {
    return null;
  }
  const match = regex.exec(text);
  if (!match) return null;
  return { start: match.index, length: match[0].length };
}

export function SourceViewer({
  chunkId,
  quote,
  claimText,
  citationId,
  onClose,
}: SourceViewerProps) {
  const [chunk, setChunk] = useState<Chunk | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [markError, setMarkError] = useState<string | null>(null);
  const [marked, setMarked] = useState<MarkedState>(null);
  const [isMarking, setIsMarking] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setChunk(null);
    setLoadError(null);
    setMarked(null);
    setMarkError(null);

    getChunk(chunkId)
      .then((result) => {
        if (!cancelled) setChunk(result);
      })
      .catch((err) => {
        if (!cancelled) {
          setLoadError(err instanceof Error ? err.message : "Failed to load source.");
        }
      });

    return () => {
      cancelled = true;
    };
  }, [chunkId, citationId]);

  const quoteMatch = chunk && quote.length > 0 ? findQuoteMatch(chunk.text, quote) : null;

  async function handleMark(valid: boolean) {
    setMarkError(null);
    setIsMarking(true);
    try {
      await markCitation(citationId, valid);
      setMarked(valid ? "valid" : "invalid");
    } catch (err) {
      setMarkError(err instanceof Error ? err.message : "Failed to mark citation.");
    } finally {
      setIsMarking(false);
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-900">Source</h2>
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            aria-label="Close source panel"
            className="text-xs text-slate-500 hover:text-slate-800"
          >
            Close
          </button>
        )}
      </div>

      {loadError && (
        <p role="alert" className="text-sm text-red-600">
          {loadError}
        </p>
      )}

      {!chunk && !loadError && (
        <p className="text-sm text-slate-500">Loading source…</p>
      )}

      {chunk && (
        <>
          <div className="text-xs text-slate-500">
            <p>{humanizeSectionLabel(chunk.section_label)}</p>
            {pageRangeLabel(chunk) && <p>{pageRangeLabel(chunk)}</p>}
          </div>

          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
              Supports
            </p>
            <p className="text-sm text-slate-700">{claimText}</p>
          </div>

          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
              Passage
            </p>
            <p className="text-sm leading-relaxed text-slate-800">
              {(() => {
                if (!quoteMatch) {
                  return chunk.text;
                }
                const before = chunk.text.slice(0, quoteMatch.start);
                const match = chunk.text.slice(
                  quoteMatch.start,
                  quoteMatch.start + quoteMatch.length
                );
                const after = chunk.text.slice(quoteMatch.start + quoteMatch.length);
                return (
                  <>
                    {before}
                    <mark className="rounded bg-amber-200 px-0.5">{match}</mark>
                    {after}
                  </>
                );
              })()}
            </p>
            {!quoteMatch && quote.length > 0 && (
              <p className="mt-1 text-xs italic text-slate-400">
                quote not located in source
              </p>
            )}
          </div>

          <div className="flex items-center gap-2 pt-1">
            <button
              type="button"
              disabled={isMarking}
              onClick={() => handleMark(true)}
              className="inline-flex items-center rounded-md border border-green-300 bg-green-50 px-2 py-1 text-xs font-medium text-green-800 transition-colors hover:bg-green-100 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Mark valid
            </button>
            <button
              type="button"
              disabled={isMarking}
              onClick={() => handleMark(false)}
              className="inline-flex items-center rounded-md border border-red-300 bg-red-50 px-2 py-1 text-xs font-medium text-red-800 transition-colors hover:bg-red-100 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Mark invalid
            </button>
          </div>

          {marked && (
            <p className="text-xs text-slate-500">
              Marked as {marked === "valid" ? "valid" : "invalid"}.
            </p>
          )}

          {markError && (
            <p role="alert" className="text-sm text-red-600">
              {markError}
            </p>
          )}
        </>
      )}
    </div>
  );
}
