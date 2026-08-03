import { ClaimLine, type OpenedCitation } from "@/components/ClaimLine";
import type { Section } from "@/lib/types";

export interface SectionViewProps {
  section: Section;
  onOpenCitation?: (citation: OpenedCitation) => void;
}

export function SectionView({ section, onOpenCitation }: SectionViewProps) {
  if (section.claims.length === 0) {
    return (
      <p className="px-3 py-8 font-sans text-sm text-mute sm:px-4">
        No claims in this section.
      </p>
    );
  }

  return (
    <ul className="px-3 sm:px-4">
      {section.claims.map((claim) => (
        <ClaimLine key={claim.id} claim={claim} onOpenCitation={onOpenCitation} />
      ))}
    </ul>
  );
}
