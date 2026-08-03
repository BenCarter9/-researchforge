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
    <li className="border-b border-rule/70 py-5 last:border-b-0 animate-fade-up">
      <p className="font-serif text-[1.05rem] leading-relaxed text-ink">{claim.claim_text}</p>
      <div className="mt-2.5 flex flex-wrap items-center gap-x-3 gap-y-1.5">
        <EvidenceChip status={claim.evidence_status} />
        <span className="text-xs tracking-wide text-mute">{humanizeClaimType(claim.claim_type)}</span>
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
            className="text-xs font-medium text-accent underline-offset-4 transition-colors hover:text-ink hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
          >
            Source
          </button>
        )}
      </div>
    </li>
  );
}
