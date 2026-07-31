import { cn } from "@/lib/cn";
import type { EvidenceStatus } from "@/lib/types";

export interface EvidenceChipProps {
  status: EvidenceStatus;
}

// The evidence signal is a traffic light with a text label, never a numeric
// confidence score. Each status maps to a distinct color and a human label —
// do not add a number anywhere in this component.
const config: Record<EvidenceStatus, { label: string; className: string }> = {
  green: {
    label: "Supported",
    className: "border-green-200 bg-green-100 text-green-800",
  },
  yellow: {
    label: "Inference / partial",
    className: "border-amber-200 bg-amber-100 text-amber-800",
  },
  red: {
    label: "Unsupported",
    className: "border-red-200 bg-red-100 text-red-800",
  },
  gray: {
    label: "Assumption",
    className: "border-gray-200 bg-gray-100 text-gray-800",
  },
};

export function EvidenceChip({ status }: EvidenceChipProps) {
  const { label, className } = config[status];

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium",
        className
      )}
    >
      {label}
    </span>
  );
}
