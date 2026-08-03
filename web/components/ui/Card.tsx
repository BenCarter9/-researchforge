import type { HTMLAttributes } from "react";

import { cn } from "@/lib/cn";

export type CardProps = HTMLAttributes<HTMLDivElement>;

export function Card({ className, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-sm border border-rule bg-surface/90 p-6 shadow-none",
        className
      )}
      {...props}
    />
  );
}
