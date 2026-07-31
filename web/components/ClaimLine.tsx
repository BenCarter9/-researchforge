import { EvidenceChip } from "@/components/EvidenceChip";
import type { Claim } from "@/lib/types";

export interface OpenedCitation {
  chunkId: string;
  quote: string;
  claimText: string;
  citationId: string;
}

export interface ClaimLineProps {
  claim: Claim;
  onOpenCitation?: (citation: OpenedCitation) => void;
}

// "management_claim" -> "Management claim"
function humanizeClaimType(claimType: Claim["claim_type"]): string {
  const withSpaces = claimType.replace(/_/g, " ");
  return withSpaces.charAt(0).toUpperCase() + withSpaces.slice(1);
}

export function ClaimLine({ claim, onOpenCitation }: ClaimLineProps) {
  const citation = claim.citation;

  return (
    <li className="border-b border-slate-100 py-3 last:border-b-0">
      <p className="text-sm text-slate-900">{claim.claim_text}</p>
      <div className="mt-1.5 flex flex-wrap items-center gap-2">
        <EvidenceChip status={claim.evidence_status} />
        <span className="inline-flex items-center rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5 text-xs font-medium text-slate-600">
          {humanizeClaimType(claim.claim_type)}
        </span>
        {citation && (
          <button
            type="button"
            onClick={() =>
              onOpenCitation?.({
                chunkId: citation.chunk_id,
                quote: citation.verbatim_quote,
                claimText: claim.claim_text,
                citationId: citation.id,
              })
            }
            className="inline-flex items-center rounded-full border border-slate-300 px-2 py-0.5 text-xs font-medium text-slate-700 transition-colors hover:bg-slate-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
          >
            Source
          </button>
        )}
      </div>
    </li>
  );
}
