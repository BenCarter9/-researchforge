import { ClaimLine, type OpenedCitation } from "@/components/ClaimLine";
import type { Section } from "@/lib/types";

export interface SectionViewProps {
  section: Section;
  onOpenCitation?: (citation: OpenedCitation) => void;
}

export function SectionView({ section, onOpenCitation }: SectionViewProps) {
  if (section.claims.length === 0) {
    return <p className="text-sm text-slate-500">No claims in this section.</p>;
  }

  return (
    <ul className="divide-y divide-slate-100">
      {section.claims.map((claim) => (
        <ClaimLine key={claim.id} claim={claim} onOpenCitation={onOpenCitation} />
      ))}
    </ul>
  );
}
