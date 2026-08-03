import { cn } from "@/lib/cn";
import type { EvidenceStatus } from "@/lib/types";

export interface EvidenceChipProps {
  status: EvidenceStatus;
}

// The evidence signal is a traffic light with a text label, never a numeric
// confidence score. Compact status mark + label — not a rounded pill cluster.
const config: Record<
  EvidenceStatus,
  { label: string; markClass: string; textClass: string }
> = {
  green: {
    label: "Supported",
    markClass: "bg-[var(--good)]",
    textClass: "text-[var(--good)]",
  },
  yellow: {
    label: "Inference / partial",
    markClass: "bg-[var(--warn)]",
    textClass: "text-[var(--warn)]",
  },
  red: {
    label: "Unsupported",
    markClass: "bg-[var(--bad)]",
    textClass: "text-[var(--bad)]",
  },
  gray: {
    label: "Assumption",
    markClass: "bg-mute",
    textClass: "text-mute",
  },
};

export function EvidenceChip({ status }: EvidenceChipProps) {
  const { label, markClass, textClass } = config[status];

  return (
    <span className={cn("inline-flex items-center gap-1.5 text-xs font-medium", textClass)}>
      <span aria-hidden className={cn("h-1.5 w-1.5 shrink-0 rounded-sm", markClass)} />
      {label}
    </span>
  );
}
